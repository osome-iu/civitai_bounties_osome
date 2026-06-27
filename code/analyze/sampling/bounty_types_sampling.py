"""
Purpose:
- Create a dataset of 150 bounties by taking 50 random samples from each of the top 3 bounty types as measured by the count.
    We only sample from SFW bounties, as other bounties will be categorized automatically as NSFW.

Inputs:
- bounties_frame_w_blur.parquet: cleaned dataframe containing the complete bounty data .
- bounties_example_images_frame_w_blur.parquet: cleaned dataframe containing the complete bounty example images data.
- bounties_in_blur_and_non_blur.txt: list of common bounty numbers in the blurred and non-blurred version of the data.

Outputs:
- `bounties_sample.csv` file with the following columns
    - bounty_number (int): Unique identifier for the bounty.
    - url (str): URL to the bounty.

Author:
- Shalmoli Ghosh
"""

import datetime
import os
import pandas as pd

# Ensure the current directory is where the script is located so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
FP_BOUNTIES = "../../../data/clean/bounties_frame_w_blur.parquet"
FP_BOUNTIES_IMAGES = "../../../data/clean/bounties_example_images_frame_w_blur.parquet"
BOUNTY_TYPES = [
    "Lora Creation",
    "Image Creation",
    "Model Creation",
    "Data Set Creation",
    "Embed Creation",
    "Video Creation",
    "Other",
]
OUT_DIR = "../../../data/intermediate"
N_TOP_BOUNTIES = 3
N_SAMPLES = 50
RANDOM_STATE = 1


def sample_selection(df, target_class, n_samples, rand_state):
    """
    Sample a specified number of rows from a DataFrame for a specific class.

    Parameters:
    - df (pd.DataFrame): DataFrame to sample from
    - target_class (str): The specific class to sample from
    - n_samples (int): Maximum number of samples to draw (default is 50)
    - rand_state (int): Random state for reproducibility

    Returns:
    - pd.DataFrame: A DataFrame containing the sampled rows.
    """
    # Filter the DataFrame for the specified class
    class_df = df[df["bounty_type"] == target_class].copy()

    # Determine the number of available samples
    available_samples = len(class_df)

    # Determine the number of samples to draw
    num_samples_to_draw = min(n_samples, available_samples)

    # Sample the data
    sampled_data = class_df.sample(n=num_samples_to_draw, random_state=rand_state)

    return sampled_data


if __name__ == "__main__":
    # Load data and select rows for only the top bounty types
    bounties_df = pd.read_parquet(FP_BOUNTIES)
    df_images = pd.read_parquet(FP_BOUNTIES_IMAGES)

    # Select bounties that are present in both blurred and non-blurred data
    temp_fp = os.path.join(OUT_DIR, "bounties_in_blur_and_non_blur.txt")
    with open(temp_fp, "r") as f:
        common_bounties = [int(line) for line in f]
    filtered_df = bounties_df[bounties_df["bounty_number"].isin(common_bounties)]
    filtered_df_images = df_images[df_images["bounty_number"].isin(common_bounties)]

    # We consider any bounty with at least one image as NSFW, so we need to merge the two dataframes
    # to get identify nsfw_rating for each bounty. Then we filter out NSFW bounties and sample only SFW bounties.
    merged_df = pd.merge(
        filtered_df,
        filtered_df_images[["bounty_number", "nsfw_rating"]],
        on="bounty_number",
        how="inner",
    )

    # Cells without any nsfw_rating are considered SFW
    merged_df["nsfw_rating"] = merged_df["nsfw_rating"].fillna("SFW")
    merged_df = merged_df[
        merged_df["nsfw_rating"] != "Images hidden due to mature content settings"
    ]

    # We create an ordered categorical value so that we can use max() to get the most extreme nsfw rating
    nsfw_categories = ["SFW", "R", "X", "XXX"]
    merged_df["nsfw_rating"] = pd.Categorical(
        merged_df["nsfw_rating"], categories=nsfw_categories, ordered=True
    )
    bounty_extreme_nsfw_df = (
        merged_df.groupby("bounty_number")["nsfw_rating"]
        .max()
        .to_frame("extreme_nsfw")
        .reset_index()
    )

    # Drop duplicates
    all_data_df = bounty_extreme_nsfw_df.merge(
        merged_df.drop_duplicates(subset="bounty_number"),
        on="bounty_number",
        how="right",
    )

    # We want to sample on the most extreme nsfw rating
    all_data_df = all_data_df.drop(columns=["nsfw_rating"])
    final_df = all_data_df[all_data_df["extreme_nsfw"] == "SFW"]

    # Identify the most prevalent types of bounties
    top_bounty_types = (
        final_df["bounty_type"].value_counts().nlargest(N_TOP_BOUNTIES).index.tolist()
    )
    top_bounties_df = final_df[final_df["bounty_type"].isin(top_bounty_types)]

    # Sample data
    samples = []
    for bounty in top_bounty_types:
        bounty_samples = sample_selection(
            top_bounties_df, bounty, N_SAMPLES, RANDOM_STATE
        )
        samples.append(bounty_samples)
    sampled_bounties = pd.concat(samples, ignore_index=True)

    sampled_bounties = sampled_bounties[["bounty_number", "url"]]

    # Save files with the current date in the filename (YYYY-mm-dd_bounties_sample.csv)
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    out_fp = os.path.join(OUT_DIR, f"{current_date}_bounties_sample.csv")
    sampled_bounties.to_csv((out_fp), index=False)
    print(f"Sampled bounties saved to {out_fp}")
