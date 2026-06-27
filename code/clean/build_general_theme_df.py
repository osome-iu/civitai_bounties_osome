"""
Purpose:
- Clean the OpenAI general theme extraction responses about the bounties.

Inputs:
- Data is read via constants defined below.

Outputs:
- `general_theme_frame.parquet`: cleaned dataframe with the following columns:
    - bounty_number (int): Unique identifier for the bounty.
    - id (str): Unique identifier given by GPT model.
    - model (str): Model used for the task.
    - completion_tokens	(int): number of tokens used to respond to the prompt.
    - prompt_tokens	(int): number of tokens in the prompt.
    - total_tokens	(int): completion_tokens + prompt_tokens.
    - best_fit_theme (str): The best theme extracted by GPT model from the given title and description and image urls.
    - best_fit_rationale (str): The rationale given by the gpt model for the best theme extracted.
    - relevant_theme (str): Other relevant themes extracted by the GPT model for a specific bounty.
    - relevant_rationale (str): The rationale given by the gpt model for the relevant theme extracted.

Author:
- Matthew DeVerna & Shalmoli Ghosh
"""

import json
import os
import glob
import sys

import numpy as np
import pandas as pd

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the possible themes
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "analyze", "openai"))
from response_structures import ThemeLiteral

# Paths to load data for cleaning
DATA_DIR = "../../data"
OPENAI_DATA_DIR = os.path.join(DATA_DIR, "openai_responses/bounty_themes/")
OPENAI_RAW_DIR = os.path.join(OPENAI_DATA_DIR, "raw")
FILE_MATCHING_STRING = "general_theme_responses__gpt-*.jsonl"

# Paths to load data for data checks
CLEAN_DIR = os.path.join(DATA_DIR, "clean")
BOUNTY_RATINGS_FP = os.path.join(CLEAN_DIR, "common_bounties_ratings.parquet")

# Ouput directory where results will be saved
OPENAI_CLEAN_DIR = os.path.join(OPENAI_DATA_DIR, "clean")
os.makedirs(OPENAI_CLEAN_DIR, exist_ok=True)

# Output file path
CLEAN_GENERAL_OUTPUT_FP = os.path.join(OPENAI_CLEAN_DIR, "general_theme_clean.parquet")


def extract_themes(record):
    """
    Extract bounty theme information from OpenAI responses.

    Parameters:
    ----------
    response (dict): The nested OpenAI general theme response to be flattened.

    Returns:
    ----------
    dict: A flattened version of the input response with only what we need.
    """

    message = record["choices"][0]["message"]

    if message.get("parsed"):
        parsed = message["parsed"]
    elif message.get("refusal"):
        # In one case, the model "refuses" but still provides a proper JSON response
        parsed = json.loads(message["refusal"])

    # There may be multiple relevant themes, so we first create a base record...
    base_record = {
        "bounty_number": record.get("bounty_number"),
        "id": record.get("id"),
        "model": record.get("model"),
        "completion_tokens": record.get("usage", {}).get("completion_tokens"),
        "prompt_tokens": record.get("usage", {}).get("prompt_tokens"),
        "total_tokens": record.get("usage", {}).get("total_tokens"),
        "best_fit_theme": parsed.get("best_fit_theme", {}).get("theme"),
        "best_fit_rationale": parsed.get("best_fit_theme", {}).get("rationale"),
    }

    # ... then we create a list of records for each relevant theme.
    theme_records = []
    relevant_themes = parsed.get("relevant_themes", [])
    if relevant_themes:
        for theme in parsed.get("relevant_themes", []):
            theme_record = base_record.copy()
            theme_record["relevant_theme"] = theme.get("theme")
            theme_record["relevant_rationale"] = theme.get("rationale")
            theme_records.append(theme_record)
    else:
        # If there are no relevant themes, we still need to create a record
        # with the best fit theme and rationale.
        theme_record = base_record.copy()
        theme_record["relevant_theme"] = None
        theme_record["relevant_rationale"] = None
        theme_records.append(theme_record)

    return theme_records


if __name__ == "__main__":

    openai_raw_files = glob.glob(os.path.join(OPENAI_RAW_DIR, FILE_MATCHING_STRING))

    dfs = []
    for file in openai_raw_files:

        print(f"Processing file: {file}")
        with open(file, "r") as f:
            records = [json.loads(line) for line in f]

        theme_records = []
        for r in records:
            # extract_themes returns a list for each record, so we need to extend the list
            theme_records.extend(extract_themes(r))

        df = pd.DataFrame.from_records(theme_records)
        dfs.append(df)

    # Concatenate all dataframes into one and save
    df = pd.concat(dfs, ignore_index=True)

    print("Running checks on the dataframe...")
    assert df["bounty_number"].notnull().all(), "Some bounty numbers are missing!"

    # Check that all themes are valid
    valid_themes = set(ThemeLiteral.__args__)
    all_themes = set(df["best_fit_theme"].unique()).union(
        set(df["relevant_theme"].dropna().unique())
    )
    assert all_themes.issubset(valid_themes), (
        "Some themes are not valid! \n"
        f"Valid themes: {valid_themes} \n"
        f"Found themes: {all_themes}"
    )

    # Check all SFW bounties have a response and only SFW bounties are present
    df_ratings = pd.read_parquet(BOUNTY_RATINGS_FP)
    sfw_bounties = set(
        df_ratings[df_ratings["rating"] == "SFW"]["bounty_number"].unique()
    )
    theme_bounties = set(df["bounty_number"].unique())

    # Check for exact set match
    assert sfw_bounties == theme_bounties, (
        "SFW bounties and theme bounties do not match exactly! \n"
        f"Missing SFW bounties: {sfw_bounties - theme_bounties} \n"
        f"Extra bounties (non-SFW): {theme_bounties - sfw_bounties}"
    )

    print("All checks passed!")

    print(f"Saving cleaned dataframe to {CLEAN_GENERAL_OUTPUT_FP}")
    df.to_parquet(CLEAN_GENERAL_OUTPUT_FP, index=False)
    print("Script completed successfully.")
