"""
Purpose:
- Generates the extreme nsfw rating labels to be used for the entire project under three
  different rating schemes (default, R-as-SFW, and R-and-X-as-SFW) and saves each as a
  separate parquet file. The default scheme is used for headline analyses; the two
  alternative schemes are used by the content-moderation robustness analysis.

Inputs:
- Data is read via constants defined below.

Outputs:
- `common_bounties_ratings.parquet`: default scheme — NSFW iff any image is R/X/XXX/hidden.
- `common_bounties_ratings_R_SFW.parquet`: NSFW iff any image is X/XXX/hidden (R treated as SFW).
- `common_bounties_ratings_R_X_SFW.parquet`: NSFW iff any image is XXX/hidden (R and X treated as SFW).

Each file has the same schema:
    - bounty_number (int): Unique identifier for the bounty.
    - rating (str): SFW (Suitable For Work) or NSFW (Not Suitable For Work)

Author:
- Shalmoli Ghosh
"""

import os
import pandas as pd

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set input and output directories/filepaths
DATA_DIR = "../../data"
INTERMEDIATE_DIR = os.path.join(DATA_DIR, "intermediate")
OUT_DIR = os.path.join(DATA_DIR, "clean")

COMMON_BOUNTY_FILE = os.path.join(INTERMEDIATE_DIR, "bounties_in_blur_and_non_blur.txt")
BOUNTIES_FRAME_FILE = os.path.join(OUT_DIR, "bounties_frame_w_blur.parquet")
BOUNTIES_EXAMPLE_IMAGES_FRAME_FILE = os.path.join(
    OUT_DIR, "bounties_example_images_frame_w_blur.parquet"
)
# Each rating scheme defines which raw image labels collapse to "SFW".
# The default scheme treats only true SFW images as SFW; the alternative schemes are used
# by the content-moderation robustness analysis to test sensitivity to where the SFW/NSFW
# threshold is drawn.
RATING_SCHEMES = {
    "common_bounties_ratings.parquet": {"SFW"},
    "common_bounties_ratings_R_SFW.parquet": {"SFW", "R"},
    "common_bounties_ratings_R_X_SFW.parquet": {"SFW", "R", "X"},
}

# Load the necessary data
with open(COMMON_BOUNTY_FILE, "r") as f:
    common_bounties = [int(line) for line in f]

df = pd.read_parquet(BOUNTIES_FRAME_FILE)
df_images = pd.read_parquet(BOUNTIES_EXAMPLE_IMAGES_FRAME_FILE)

filtered_df = df[df["bounty_number"].isin(common_bounties)]
filtered_df_images = df_images[df_images["bounty_number"].isin(common_bounties)]

# Add the nsfw_rating column to the filtered DataFrame
merged_df = pd.merge(
    filtered_df,
    filtered_df_images[["bounty_number", "nsfw_rating"]],
    on="bounty_number",
    how="left",
)

# Cells without any nsfw_rating are considered SFW as they were not blurred by Civitai
merged_df["nsfw_rating"] = merged_df["nsfw_rating"].fillna("SFW")

# We create an ordered categorical value so that we can use max() to get the most extreme nsfw rating
nsfw_categories = [
    "SFW",
    "Images hidden due to mature content settings",
    "R",
    "X",
    "XXX",
]
merged_df["nsfw_rating"] = pd.Categorical(
    merged_df["nsfw_rating"], categories=nsfw_categories, ordered=True
)
bounty_extreme_nsfw_df = (
    merged_df.groupby("bounty_number")["nsfw_rating"]
    .max()
    .to_frame("extreme_nsfw")
    .reset_index()
)

# Convert to str once to avoid warning about replace() not working on Categorical
extreme_str = bounty_extreme_nsfw_df["extreme_nsfw"].astype(str)

# Emit one parquet per rating scheme.
for filename, sfw_labels in RATING_SCHEMES.items():
    out_path = os.path.join(OUT_DIR, filename)
    out_df = pd.DataFrame(
        {
            "bounty_number": bounty_extreme_nsfw_df["bounty_number"],
            "rating": extreme_str.where(~extreme_str.isin(sfw_labels), "SFW").where(
                extreme_str.isin(sfw_labels), "NSFW"
            ),
        }
    )

    assert set(out_df["bounty_number"]) == set(common_bounties), (
        f"Error in {filename}: missing/extra bounties!"
    )
    assert out_df["bounty_number"].duplicated().sum() == 0, (
        f"Error in {filename}: duplicate bounties!"
    )

    print(f"Creating file: {out_path}")
    out_df.to_parquet(out_path, index=False)
