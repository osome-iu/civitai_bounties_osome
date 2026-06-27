"""
Purpose:
- Extract information about example images submitted with each bounty from CivitAI HTML.

Inputs:
- None.
- Data is read via constants defined below.

Outputs:
- `bounties_example_images_frame.parquet`: cleaned dataframe with the following columns:
    - bounty_number (int): Unique identifier for the bounty.
    - bounty_url (str): URL to the bounty.
    - with_blur (bool): If "True" it means that the cleaned data is based on the raw data which has blur
        in the raw HTML. If "False" it means that the cleaned data is based on the raw data which does
        not have blur in the HTML.
    - ex_image_url (str): URL to the example image. If blurred, value will be None. When `type` column
        is set to 'video', this column will contain a URL to a single frame of the video.
    - ex_video_url (str): URL to the example video, if present. If blurred, value will be None.
    - type (str): Labels the type of example in the bounty. Values are "image" (if the example is
        an image) and "video" (if the example is a video). If `with_blur` is True, AND the example
        is blurred, this column will be set to None as the HTML does not indicate the type of example.
    - nsfw_rating (str): Rating indicates whether the submission example image was
        blurred, and marked as NSFW. Options: 'R', 'X', 'XXX', 'Images hidden due to
        mature content settings', or None. None is used when the image is NOT blurred
        and the URL can be extracted.

Notes:
- If both ex_image_url and nsfw_rating are None, there was an error in the extraction.
- All values in the column nsfw_rating is set to None if in the source data images are not blurred.

Author:
- Matt DeVerna & Shalmoli Ghosh
"""

import argparse
import os
import json

import pandas as pd
from bs4 import BeautifulSoup

# Ensure the current directory is where the script is located so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Argument parser for command line options
parser = argparse.ArgumentParser(description="Process bounties example images.")
parser.add_argument(
    "--with_blur",
    action="store_true",
    help="Set this flag to process bounties with blur.",
)
args = parser.parse_args()

# Constants
OUT_DIR = "../../data/clean"
WITH_BLUR = args.with_blur
BOUNTIES_DIR = "../../data/bounties_with_blur" if WITH_BLUR else "../../data/bounties"

files = sorted([file for file in os.listdir(BOUNTIES_DIR) if file.endswith(".json")])
num_files = len(files)

records = []
for idx, file in enumerate(files, start=1):
    print(f"Working on file {idx}/{num_files}")
    fp = os.path.join(BOUNTIES_DIR, file)

    with open(fp, "r") as f:
        data = json.load(f)

    # Extract bounty number from URL
    bounty_url = data["url"]
    bounty_number = int(bounty_url.split("/")[-1])

    # Return all entries as a list
    html_text = data["html_text"]
    soup = BeautifulSoup(html_text, "html.parser")

    # Extract all example images
    carousel_slides = soup.find_all(class_="mantine-Carousel-slide")

    record_base = {
        "bounty_number": bounty_number,
        "bounty_url": bounty_url,
        "with_blur": WITH_BLUR,
    }

    for slide in carousel_slides:
        temp_record = record_base.copy()

        try:
            img_obj = slide.find("img")
            video_obj = slide.find("video")

            # This is the case when the example is blurred
            if img_obj is None and video_obj is None:
                rating = slide.find(class_="mantine-h9iq4m mantine-Badge-inner").text
                temp_record["ex_image_url"] = None
                temp_record["ex_video_url"] = None
                temp_record["type"] = None
                temp_record["nsfw_rating"] = rating

            elif img_obj:
                ex_image_url = img_obj.get("src")
                ex_image_url = ex_image_url.replace(" ", "%20")  # Handle spaces
                temp_record["ex_image_url"] = ex_image_url
                temp_record["type"] = "image"
                temp_record["nsfw_rating"] = None
                temp_record["ex_video_url"] = None

            elif video_obj:
                # Here, the example image is a frame from the video
                ex_image_url = video_obj.get("poster")
                ex_image_url = ex_image_url.replace(" ", "%20")

                # Now we extract all available source URLs for the video
                clip_url = video_obj.find_all("source")
                url_dict = dict()
                for source in clip_url:
                    url_dict[source.get("type")] = source.get("src")
                # Extract video URL, prioritizing mp4 over webm
                ex_video_url = url_dict.get("video/mp4") or url_dict.get("video/webm")

                temp_record["ex_image_url"] = ex_image_url
                temp_record["ex_video_url"] = ex_video_url
                temp_record["type"] = "video"
                temp_record["nsfw_rating"] = None

            else:
                raise Exception(f"Unknown example encountered! Bounty: {bounty_number}")

            records.append(temp_record)

        except Exception as e:
            # In very few odd cases, images are hidden and labeled with a different nsfw
            # messages. We catch those here.
            rating = slide.find(class_="mantine-Text-root mantine-ljqvxq")
            if rating:
                temp_record["ex_image_url"] = "Error"
                temp_record["ex_video_url"] = None
                temp_record["type"] = None
                temp_record["nsfw_rating"] = rating.text
                records.append(temp_record)
                continue

            # Otherwise, we raise an exception
            print(f"Slide carousel: {slide}")
            if bounty_number == 1079:
                continue
            raise Exception(f"Error in bounty {bounty_number}: {e}")

# Create dataframe
clean_df = pd.DataFrame.from_records(records)
clean_df = clean_df.sort_values("bounty_number").reset_index(drop=True)

# Save files
out_fp = (
    os.path.join(OUT_DIR, "bounties_example_images_frame_w_blur.parquet")
    if WITH_BLUR
    else (os.path.join(OUT_DIR, "bounties_example_images_frame_wo_blur.parquet"))
)
print(f"Creating file: {out_fp}")
clean_df.to_parquet(out_fp, index=False)
