"""
Purpose:
- Process and clean the OpenAI NSFW Deepfake responses about the bounties.

Inputs:
- Data is read via constants defined below.

Outputs:
- deepfake_bounties_from_nsfw.csv containing the parsed OpenAI responses as given below:
    - bounty_number (int): Unique identifier for the bounty.
    - deepfake (bool): True if the bounty requests a deepfake of a real person, False otherwise.
    - name (str): Full name of the person, or None if not identified
    - occupation (str): Person's occupation or role, or None
    - real_human (bool): True if the person is a real human, False otherwise
    - rationale (str): Brief explanation (≤50 words) of the classification decision

Author:
- Shalmoli Ghosh
"""

import os
import json
import pandas as pd

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

OPENAI_DATA_DIR = "../../data/openai_responses/deepfakes/"
OPENAI_DEEPFAKE_NSFW_FILE = os.path.join(
    OPENAI_DATA_DIR, "raw", "deepfake_bounties_from_nsfw__gpt-4.1.jsonl"
)
OPENAI_CLEAN_DIR = os.path.join(OPENAI_DATA_DIR, "clean")
os.makedirs(OPENAI_CLEAN_DIR, exist_ok=True)
CLEAN_DEEPFAKE_FNAME = "deepfake_bounties_from_nsfw.csv"



def parse_deepfake_responses(input_file):
    """
    Parse JSONL file containing GPT responses for deepfake classification.

    Parameters:
    -----------
    input_file : str
        Path to the input JSONL file

    Returns:
    --------
    pd.DataFrame
        DataFrame with extracted fields
    """

    records = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                # Parse the JSON line
                data = json.loads(line.strip())

                # Extract the parsed response
                parsed = data["choices"][0]["message"]["parsed"]

                # Create record with extracted fields
                record = {
                    "bounty_number": data["bounty_number"],
                    "deepfake": parsed["deepfake"],
                    "name": parsed["name"],
                    "occupation": parsed["occupation"],
                    "real_human": parsed["real_human"],
                    "rationale": parsed["rationale"],
                }

                records.append(record)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing line {line_num}: {e}")
                continue

    # Create DataFrame
    df = pd.DataFrame(records)

    return df


if __name__ == "__main__":
    df = parse_deepfake_responses(OPENAI_DEEPFAKE_NSFW_FILE)
    df.to_csv(os.path.join(OPENAI_CLEAN_DIR, CLEAN_DEEPFAKE_FNAME), index=False)
    print(f"Saved {len(df)} records to {CLEAN_DEEPFAKE_FNAME}")
