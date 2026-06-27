"""
Purpose:
    This script extracts general themes from bounty data by leveraging OpenAI's API.
    It processes each bounty's title, description, and associated image URLs to generate theme annotations.

Notes:
    - Only bounties rated as SFW (safe for work) are included.
    - Failed image URLs are logged separately for review.

Usage:
    Must be run from the command line with the appropriate mode argument.

    Required arguments:
    --mode: Specifies the mode of operation, either "sample" or "full".
        sample: Runs the script on a smaller subset of bounties for testing.
        full: Processes the entire dataset of bounties.
    --model: Specifies the OpenAI model to use for processing, either "gpt-4.1" or "gpt-4o".

    Example command to run the script:
    python general_theme_extraction.py --mode full --model gpt-4o

Input:
    Bounty data are read in with filepaths set as constants.

Output:
    .jsonl file where each line represents the API response object.
        Filename format: general_theme_responses__<model_name>.jsonl

Author:
    Matthew DeVerna & Shalmoli Ghosh
"""

import argparse
import json
import os
import requests

import pandas as pd

from api_helpers import OpenAIClient
from response_structures import BountyClassifierOutput
from prompts import SYS_GENERAL

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constant file paths
DATA_DIR = "../../../data/clean"
INTERMEDIATE_DIR = "../../../data/intermediate"
OPENAI_RAW_RESPONSE = "../../../data/openai_responses/bounty_themes/raw"
os.makedirs(OPENAI_RAW_RESPONSE, exist_ok=True)

# BLurred bounty data file paths
BOUNTIES_FRAME_W_BLUR = os.path.join(DATA_DIR, "bounties_frame_w_blur.parquet")
BOUNTIES_EXAMPLE_IMAGES_FRAME_W_BLUR = os.path.join(
    DATA_DIR, "bounties_example_images_frame_w_blur.parquet"
)

# Bounties in both blurred and non-blurred files
BOUNTIES_IN_BLUR_AND_NON_BLUR_FP = os.path.join(
    DATA_DIR, "common_bounties_ratings.parquet"
)

# Sample bounties to be annotated and tested
SAMPLE_FP = os.path.join(INTERMEDIATE_DIR, "2025-04-03_bounties_sample.csv")

# Output file names, depending on the mode
OUTPUT_FP = "general_theme_responses.jsonl"


# File to store failed image URLs
FAILED_URLS_FILENAME = "theme_extraction_bad_urls.jsonl"


def parse_args():
    """
    Parse command-line arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments with 'mode' attribute.
    """
    parser = argparse.ArgumentParser(
        description="Run theme extraction on sample or full dataset."
    )
    parser.add_argument(
        "--mode",
        choices=["sample", "full"],
        required=True,
        help="Choose the dataset to process: 'sample' runs on a small subset, while 'full' processes the entire dataset.",
    )
    parser.add_argument(
        "--model",
        choices=["gpt-4.1", "gpt-4o"],
        required=True,
        help="Choose the OpenAI model to use for processing.",
    )
    return parser.parse_args()


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
    args = parse_args()

    # Update the failed URLs file path depending on the model
    failed_base, ext = FAILED_URLS_FILENAME.rsplit(".", 1)
    FAILED_URLS_PATH = os.path.join(
        OPENAI_RAW_RESPONSE, f"{failed_base}__{args.model}.{ext}"
    )

    # Load the bounties and example images DataFrames
    df = pd.read_parquet(BOUNTIES_FRAME_W_BLUR)
    df_images = pd.read_parquet(BOUNTIES_EXAMPLE_IMAGES_FRAME_W_BLUR)

    # Load bounty ratings, use to select SFW bounties
    bounty_ratings_df = pd.read_parquet(BOUNTIES_IN_BLUR_AND_NON_BLUR_FP)
    sfw_bounties_df = bounty_ratings_df[bounty_ratings_df["rating"] == "SFW"]
    sfw_bounty_numbers = sfw_bounties_df["bounty_number"].tolist()

    filtered_df = df[df["bounty_number"].isin(sfw_bounty_numbers)]
    filtered_df_images = df_images[df_images["bounty_number"].isin(sfw_bounty_numbers)]

    # Group the example images DataFrame by bounty number and aggregate the ex_image_urls into a list
    image_urls_by_bounty = (
        filtered_df_images.groupby("bounty_number")["ex_image_url"]
        .agg(list)
        .reset_index()
    )

    # Merge the bounties DataFrame with the aggregated image URLs
    merged_df = pd.merge(
        filtered_df[["bounty_number", "bounty_title", "description"]],
        image_urls_by_bounty[["bounty_number", "ex_image_url"]],
        on="bounty_number",
        how="left",
    )

    # Adjust data and output file paths based on the mode
    if args.mode == "sample":
        sample_df = pd.read_csv(SAMPLE_FP)
        sample_df["bounty_number"] = sample_df["bounty_number"].astype(int)

        # Filter merged_df to only include sample bounties
        merged_df = merged_df[
            merged_df["bounty_number"].isin(sample_df["bounty_number"])
        ]

    base_filename, ext = OUTPUT_FP.rsplit(".", 1)
    output_file_path = os.path.join(
        OPENAI_RAW_RESPONSE, f"{base_filename}__{args.model}.{ext}"
    )

    # Remove completed bounties from merged_df
    completed_bounty_ids = find_completed_bounties(output_file_path)
    if completed_bounty_ids:
        print(f"Removing {len(completed_bounty_ids)} ids already processed.")
        merged_df = merged_df[~merged_df["bounty_number"].isin(completed_bounty_ids)]

    num_bounties = len(merged_df)

    print(f"Begin processing {num_bounties:,} bounties...")
    bounty_info = zip(
        range(num_bounties),
        merged_df["bounty_number"],
        merged_df["bounty_title"],
        merged_df["description"],
        merged_df["ex_image_url"],
    )

    # Set up OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    oai_client = OpenAIClient()
    oai_client.initialize_client(api_key=openai_api_key)

    for idx, bounty_id, title, description, image_list in bounty_info:
        print(f"Working on bounty {bounty_id} ({idx}/{num_bounties})...")
        content = [
            {"type": "text", "text": f"TITLE: {title}\n\nDESCRIPTION: {description}"}
        ]

        valid_images = []
        failed_images = []

        # image_list is NaN if the bounty has no example images
        if isinstance(image_list, list):
            # Filter out invalid image URLs
            for url in image_list:
                if is_valid_image_url(url):
                    valid_images.append(url)
                else:
                    failed_images.append(url)

            # If there are valid image URLs, add them to the query content
            for image_url in valid_images:
                content.append({"type": "image_url", "image_url": {"url": image_url}})

        # Save failed URLs for reporting
        if failed_images:
            with open(FAILED_URLS_PATH, "a") as f_failed:
                for failed_url in failed_images:
                    failed_data = {
                        "bounty_number": bounty_id,
                        "failed_url": failed_url,
                    }
                    f_failed.write(f"{json.dumps(failed_data)}\n")

        # Hit the OpenAI API with the bounty information
        oai_response = oai_client.query_model(
            model=args.model,
            system_prompt=SYS_GENERAL,
            user_instruction=content,
            format_class=BountyClassifierOutput,
        )

        # Add bounty identifier into response dictionary
        response_dict = oai_response.model_dump()
        response_dict["bounty_number"] = bounty_id

        with open(output_file_path, "a") as f_out:
            f_out.write(f"{json.dumps(response_dict)}\n")

    print("Script completed successfully.")
