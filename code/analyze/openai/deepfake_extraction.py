"""
Purpose:
    This script extracts deepfakes from bounty data by leveraging OpenAI's API.
    It processes each bounty's title, description, to check if there is deepfake in any bounty.

Notes:
    - Only bounties rated as NSFW (not safe for work) are included.

Usage:
    Must be run from the command line with the appropriate mode argument.

    Required arguments:
    --model: Specifies the OpenAI model to use for processing, either "gpt-4.1" or "gpt-4o".

    Example command to run the script:
    python deepfake_extraction.py --model gpt-4o

Input:
    Bounty data are read in with filepaths set as constants.

Output:
    .jsonl file where each line represents the API response object.
        Filename format: deepfake_bounties_from_nsfw__<model_name>.jsonl

Author:
    Shalmoli Ghosh
"""

import argparse
import json
import os

import pandas as pd

from api_helpers import OpenAIClient
from response_structures import PersonEntityStructure
from prompts import SYS_PEOPLE

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constant file paths
DATA_DIR = "../../../data/clean"
INTERMEDIATE_DIR = "../../../data/intermediate"
OPENAI_RAW_RESPONSE = "../../../data/openai_responses/deepfakes/raw"
os.makedirs(OPENAI_RAW_RESPONSE, exist_ok=True)

# BLurred bounty data file paths
BOUNTIES_FRAME_W_BLUR = os.path.join(DATA_DIR, "bounties_frame_w_blur.parquet")

# Bounties in both blurred and non-blurred files
BOUNTIES_IN_BLUR_AND_NON_BLUR_FP = os.path.join(
    DATA_DIR, "common_bounties_ratings.parquet"
)

# Output file names, depending on the mode
OUTPUT_FP = "deepfake_bounties_from_nsfw.jsonl"


def parse_args():
    """
    Parse command-line arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments with 'model' attribute.
    """
    parser = argparse.ArgumentParser(description="Run deepfake extraction.")
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


if __name__ == "__main__":
    args = parse_args()

    # Load the bounties and example images DataFrames
    df = pd.read_parquet(BOUNTIES_FRAME_W_BLUR)

    # Load bounty ratings, use to select SFW bounties
    bounty_ratings_df = pd.read_parquet(BOUNTIES_IN_BLUR_AND_NON_BLUR_FP)
    nsfw_bounties_df = bounty_ratings_df[bounty_ratings_df["rating"] == "NSFW"]
    nsfw_bounty_numbers = nsfw_bounties_df["bounty_number"].tolist()

    filtered_df = df[df["bounty_number"].isin(nsfw_bounty_numbers)]

    # Adjust data and output file paths based on the mode
    base_filename, ext = OUTPUT_FP.rsplit(".", 1)
    output_file_path = os.path.join(
        OPENAI_RAW_RESPONSE, f"{base_filename}__{args.model}.{ext}"
    )

    # Remove completed bounties from merged_df
    completed_bounty_ids = find_completed_bounties(output_file_path)
    if completed_bounty_ids:
        print(f"Removing {len(completed_bounty_ids)} ids already processed.")
        filtered_df = filtered_df[
            ~filtered_df["bounty_number"].isin(completed_bounty_ids)
        ]

    num_bounties = len(filtered_df)

    print(f"Begin processing {num_bounties:,} bounties...")
    bounty_info = zip(
        range(num_bounties),
        filtered_df["bounty_number"],
        filtered_df["bounty_title"],
        filtered_df["description"],
    )

    # Set up OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    oai_client = OpenAIClient()
    oai_client.initialize_client(api_key=openai_api_key)

    for idx, bounty_id, title, description in bounty_info:
        print(f"Working on bounty {bounty_id} ({idx}/{num_bounties})...")
        content = [
            {"type": "text", "text": f"TITLE: {title}\n\nDESCRIPTION: {description}"}
        ]

        # Hit the OpenAI API with the bounty information
        oai_response = oai_client.query_model(
            model=args.model,
            system_prompt=SYS_PEOPLE,
            user_instruction=content,
            format_class=PersonEntityStructure,
        )

        # Add bounty identifier into response dictionary
        response_dict = oai_response.model_dump()
        response_dict["bounty_number"] = bounty_id

        with open(output_file_path, "a") as f_out:
            f_out.write(f"{json.dumps(response_dict)}\n")

    print("Script completed successfully.")
