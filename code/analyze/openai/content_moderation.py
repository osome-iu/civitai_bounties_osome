"""
Purpose:
    Conduct content moderation analysis on all bounties based on the image urls for each bounty.
    The main purpose for this is to test the robustness of the labels given by us to each bounty.

References:
- https://platform.openai.com/docs/guides/moderation/overview

Input:
    Bounties are read in with paths set as constants below.

Output:
    .jsonl file where each line represents the API response object.

Author:
- Matthew DeVerna & Shalmoli Ghosh
"""

import json
import os
import requests

import pandas as pd

from api_helpers import OpenAIClient

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = "../../../data/clean"
OPENAI_RAW_RESPONSE = "../../../data/openai_responses/content_moderation/raw"

os.makedirs(OPENAI_RAW_RESPONSE, exist_ok=True)

# Non-blurred bounty data file paths
BOUNTIES_FRAME_WO_BLUR = os.path.join(DATA_DIR, "bounties_frame_wo_blur.parquet")
BOUNTIES_EXAMPLE_IMAGES_FRAME_WO_BLUR = os.path.join(
    DATA_DIR, "bounties_example_images_frame_wo_blur.parquet"
)

# Bounties in both blurred and non-blurred files
BOUNTIES_IN_BLUR_AND_NON_BLUR_FP = os.path.join(
    DATA_DIR, "common_bounties_ratings.parquet"
)

OUTPUT_FILENAME = "content_moderation_responses.jsonl"
FAILED_URLS_PATH = os.path.join(
    OPENAI_RAW_RESPONSE, "content_moderation_bad_urls.jsonl"
)
FAILED_QUERIES_PATH = os.path.join(
    OPENAI_RAW_RESPONSE, "failed_content_moderation_queries.jsonl"
)


def find_completed_bounties(file_path):
    """
    Return a set of completed bounty id numbers.

    Parameters:
    -----------
    path (str): full path the output .jsonl file.

    Returns:
    -----------
    bounty_ids (list): completed bounties
    """
    bounty_ids = []

    # Return empty list if no file
    if not os.path.exists(file_path):
        return bounty_ids

    # Otherwise, load and collect bounty_ids
    with open(file_path, "r") as f:
        return [json.loads(line)["bounty_number"] for line in f]


def is_valid_image_url(url):
    """
    Checks if an image URL is valid by making a HEAD request.

    Parameters:
    -----------
    url (str): The image URL to check.

    Returns:
    -----------
    bool: True if the URL returns a 200 status code and has an image content type, False otherwise.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get("Content-Type", "")
        return response.status_code == 200 and "image" in content_type
    except Exception:
        return False


if __name__ == "__main__":
    df_images = pd.read_parquet(BOUNTIES_EXAMPLE_IMAGES_FRAME_WO_BLUR)

    # Load bounty ratings, use to select SFW bounties
    bounty_ratings_df = pd.read_parquet(BOUNTIES_IN_BLUR_AND_NON_BLUR_FP)
    bounty_numbers = bounty_ratings_df["bounty_number"].tolist()

    filtered_df_images = df_images[df_images["bounty_number"].isin(bounty_numbers)]

    # Group the example images DataFrame by bounty number and aggregate the ex_image_urls into a list
    image_urls_by_bounty = (
        filtered_df_images.groupby("bounty_number")["ex_image_url"]
        .agg(list)
        .reset_index()
    )

    # Set up OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    oai_client = OpenAIClient()
    oai_client.initialize_client(api_key=openai_api_key)

    # Remove completed bounties from the data frame if they exist.
    output_file_path = os.path.join(OPENAI_RAW_RESPONSE, OUTPUT_FILENAME)
    completed_bounty_ids = find_completed_bounties(output_file_path)
    if len(completed_bounty_ids) > 0:
        print(f"Removing {len(completed_bounty_ids)} ids already processed.")
        image_urls_by_bounty = image_urls_by_bounty[
            ~image_urls_by_bounty["bounty_number"].isin(completed_bounty_ids)
        ]

    num_bounties = len(image_urls_by_bounty)
    print(f"Begin processing {num_bounties:,} bounties...")
    bounty_info = zip(
        range(len(image_urls_by_bounty)),
        image_urls_by_bounty["bounty_number"],
        image_urls_by_bounty["ex_image_url"],
    )

    for idx, bounty_id, image_list in bounty_info:
        print(f"Working on bounty {bounty_id} ({idx}/{len(image_urls_by_bounty)})...")

        valid_images = []

        # image_list is NaN if the bounty has no example images
        if isinstance(image_list, list):
            failed_images = []
            # Filter out invalid image URLs
            for url in image_list:
                if is_valid_image_url(url):
                    valid_images.append(url)
                else:
                    failed_images.append(url)
            # # Save failed URLs for reporting
            if failed_images:
                with open(FAILED_URLS_PATH, "a") as f_failed:
                    for failed_url in failed_images:
                        if failed_url != "Error":
                            failed_data = {
                                "bounty_number": bounty_id,
                                "failed_url": failed_url,
                                "problem": "failed url",
                            }
                        else:
                            failed_data = {
                                "bounty_number": bounty_id,
                                "failed_url": None,
                                "problem": "missing url",
                            }
                        f_failed.write(f"{json.dumps(failed_data)}\n")

            # If there are valid image URLs, add them to the query content
            for image_url in valid_images:
                try:
                    oai_response = oai_client.query_moderation(url=image_url)
                    response_dict = oai_response.model_dump()
                    response_dict["bounty_number"] = bounty_id
                    response_dict["image_url"] = image_url

                    with open(output_file_path, "a") as f_out:
                        f_out.write(f"{json.dumps(response_dict)}\n")
                except Exception as e:
                    print(
                        f"Error processing URL {image_url} for bounty {bounty_id}: {e}"
                    )
                    # Store the URL and bounty number
                    with open(FAILED_QUERIES_PATH, "a") as f:
                        f.write(
                            f"{json.dumps({'url': image_url, 'bounty_number': bounty_id})}\n"
                        )
