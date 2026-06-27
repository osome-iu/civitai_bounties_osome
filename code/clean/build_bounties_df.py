"""
Purpose:
- Process and clean CivitAI bounties HTML text, extracting bounty descriptions, engagement, and
    other descriptive information about the bounty.

Inputs:
- None.
- Data is read via constants defined below.

Outputs:
- `bounties.parquet`: cleaned dataframe with the following columns:
    - bounty_number (int): Unique identifier for the bounty.
    - bounty_title (str): Title or headline of the bounty.
    - bounty_type (str): Type or category of the bounty.
    - started (str): Date when the bounty was initiated.
    - deadline (str): Deadline date for the bounty submissions.
    - supporter (str): Name of the account supporting the bounty.
    - buzz (int): Amount of civitai “currency” provided by the supporter as a reward for completing the bounty.
    - description (str): Detailed text description of the bounty, written by the supporter.
    - status (str): Current status of the bounty (e.g., active, completed).
    - count_tracked (int): Number of times the bounty has been tracked.
    - count_likes (int): Number of likes received by the bounty.
    - count_comments (int): Number of comments made on the bounty.
    - count_entries (int): Number of submissions or entries for the bounty.
    - url (str): URL to the bounty.
    - base_model (str, nullable): Name of the base model used for the bounty, if specified.
        - May contain NaN.
    - model_preferences (str, nullable): Specific model preferences for the bounty, if applicable.
        - May contain NaN.
    - with_blur (bool): If "True" it means that the cleaned data is based on the raw data which has blur
        in the raw HTML. If "False" it means that the cleaned data is based on the raw data which does
        not have blur in the HTML.

Author:
- Matthew DeVerna & Shalmoli Ghosh
"""

import argparse
import json
import os

import pandas as pd

from bs4 import BeautifulSoup

# Ensure the current directory is where the script is located so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Process CivitAI bounties HTML text.")
parser.add_argument(
    "--with_blur",
    action="store_true",
    help="Include this flag to process bounties with blur.",
)
args = parser.parse_args()

# Constants
WITH_BLUR = args.with_blur
BOUNTIES_DIR = "../../data/bounties_with_blur" if WITH_BLUR else "../../data/bounties"

OUT_DIR = "../../data/clean"
KNOWN_KEYS = ["Bounty Type", "Base Model", "Started", "Deadline", "Model Preferences"]

files = sorted([file for file in os.listdir(BOUNTIES_DIR) if file.endswith(".json")])
num_files = len(files)

records = []
for idx, file in enumerate(files, start=1):
    print(f"Working on file {idx}/{num_files}")
    fp = os.path.join(BOUNTIES_DIR, file)

    with open(fp, "r") as f:
        data = json.load(f)
        html_text = data["html_text"]
        url = data["url"]

        # Initialize a dictionary record for this bounty's data with it's bounty number
        record = {"bounty_number": int(url.split("/")[-1])}

        soup = BeautifulSoup(html_text, "html.parser")

        # Get bounty title
        h1_tag = soup.find_all("h1", {"class": "mantine-Title-root"})[0]
        title = h1_tag.text
        record.update({"bounty_title": title})

        # Get bounty request information
        for row in soup.find_all("tr"):
            row_data = row.find_all("td")

            # Each row contains a key (like those shown in KNOWN_KEYS above)
            row_key = row_data[0].get_text(strip=True)
            row_value = row_data[1]
            inner_spans = row_value.find_all("span")

            # Sometimes the row's values has more than one word.
            # We combine them using the format: "firstword|secondword|...|"
            row_value = (
                "|".join([rval.get_text(strip=True) for rval in inner_spans])
                if inner_spans
                else row_value.get_text(strip=True)
            )

            if row_key in KNOWN_KEYS:
                row_key = "_".join(word.lower() for word in row_key.split(" "))
                record[row_key] = row_value

            # This one row require we manually set the key name
            else:
                record["supporter"] = row_key
                record["buzz"] = int(row_value.replace(",", ""))

        # Get bounty description.
        # Retain simple HTML formatting, emojis, etc. as LLMs can understand that
        description = []
        description_elements = soup.article.find_all("p")
        for description_el in description_elements:
            clean_str = "".join([str(el) for el in description_el.contents])
            description.append(clean_str)
        description = "\n".join(description)
        record.update({"description": description})

        # Create a list of all div objects that contain icon integer pairs
        badges_div_list = soup.find_all("div", "mantine-Badge-root")

        # Extract the pairs
        status_icon_int_pair = badges_div_list[1].find_all("span")
        tracked_icon_int_pair = badges_div_list[2].find_all("span")
        likes_icon_int_pair = badges_div_list[3].find_all("span")
        comments_icon_int_pair = badges_div_list[4].find_all("span")
        entries_icon_int_pair = badges_div_list[5].find_all("span")

        record.update(
            {
                "status": status_icon_int_pair[-1].text.lower(),
                "count_tracked": int(tracked_icon_int_pair[-1].text),
                "count_likes": int(likes_icon_int_pair[-1].text),
                "count_comments": int(comments_icon_int_pair[-1].text),
                "count_entries": int(entries_icon_int_pair[-1].text),
            }
        )
        record["url"] = url
        record["with_blur"] = WITH_BLUR

    records.append(record)

# Create DataFrame and sort
clean_df = pd.DataFrame.from_records(records)
clean_df = clean_df.sort_values("bounty_number").reset_index(drop=True)

# Save files
out_fp = (
    os.path.join(OUT_DIR, "bounties_frame_w_blur.parquet")
    if WITH_BLUR
    else os.path.join(OUT_DIR, "bounties_frame_wo_blur.parquet")
)
print(f"Creating file: {out_fp}")
clean_df.to_parquet(out_fp, index=False)
