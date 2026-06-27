"""
Purpose:
- Generate the user concentration analysis figure (fig 5) presented in the paper.

Inputs:
- bounties_frame_w_blur_published.parquet: cleaned dataframe containing the complete bounty data .
- bounties_example_images_frame_w_blur_published.parquet: cleaned dataframe containing the complete bounty example images data.
- bounties_in_blur_and_non_blur.txt: list of common bounty numbers in the blurred and non-blurred version of the data.
- common_bounties_ratings_published.parquet: cleaned dataframe containing the ratings of the common bounties by the platform.
- general_theme_clean_published.parquet: cleaned dataframe containing the general theme assigned to each bounty by GPT models.
- overall_deepfake_validation_published.csv: cleaned dataframe containing the validated deepfake data.

Outputs:
- user_concentration_analysis.pdf
- user_concentration_analysis.png

Author:
- Shalmoli Ghosh
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.ticker as mticker


plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = "../../../data/clean"
BOUNTIES_IN_BLUR_AND_NON_BLUR_FP = os.path.join(
    DATA_DIR, "common_bounties_ratings_published.parquet"
)
OPENAI_DATA_DIR = "../../../data/openai_responses/bounty_themes"
CLEAN_BOUNTY_THEME_FNAME = "clean/general_theme_clean_published.parquet"

FIG_DIR = "../../../results/figures"
os.makedirs(FIG_DIR, exist_ok=True)

bounty_ratings_df = pd.read_parquet(BOUNTIES_IN_BLUR_AND_NON_BLUR_FP)
df = pd.read_parquet(os.path.join(DATA_DIR, "bounties_frame_w_blur_published.parquet"))
df_images = pd.read_parquet(
    os.path.join(DATA_DIR, "bounties_example_images_frame_w_blur_published.parquet")
)
df_theme = pd.read_parquet(os.path.join(OPENAI_DATA_DIR, CLEAN_BOUNTY_THEME_FNAME))
df_theme = df_theme[df_theme["model"] == "gpt-4.1-2025-04-14"]
df_best_fit = df_theme[["bounty_number", "best_fit_theme"]].drop_duplicates()
df_deepfake = pd.read_csv(
    "../../../data/intermediate/overall_deepfake_validation_published.csv"
)

df["started_dt"] = pd.to_datetime(df["started"])
df["deadline_dt"] = pd.to_datetime(df["deadline"])
bounty_numbers = bounty_ratings_df["bounty_number"].tolist()

filtered_df = df[df["bounty_number"].isin(bounty_numbers)]
filtered_df_images = df_images[df_images["bounty_number"].isin(bounty_numbers)]

merged_df = pd.merge(
    filtered_df,
    filtered_df_images[
        ["bounty_number", "nsfw_rating"]
    ],  # Let's include only the columns we want!
    on="bounty_number",
    how="left",
)
merged_df["nsfw_rating"] = merged_df["nsfw_rating"].fillna("SFW")
# Number of bounties with "Images hidden due to mature content settings"
hidden_frame = merged_df[
    merged_df["nsfw_rating"] == "Images hidden due to mature content settings"
]
num_bounties = hidden_frame.bounty_number.nunique()
print(
    f"Number of bounties dropped with 'Images hidden due to mature content settings': {num_bounties}"
)

merged_df.nsfw_rating.value_counts(dropna=False)
len(merged_df.bounty_number.unique())

nsfw_categories = [
    "SFW",
    "R",
    "Images hidden due to mature content settings",
    "X",
    "XXX",
]
merged_df["nsfw_rating"] = pd.Categorical(
    merged_df["nsfw_rating"], categories=nsfw_categories, ordered=True
)
merged_df["nsfw_rating_numeric"] = merged_df["nsfw_rating"].cat.codes

bounty_extreme_nsfw_df = (
    merged_df.groupby("bounty_number")["nsfw_rating"]
    .max()
    .to_frame("extreme_nsfw")
    .reset_index()
)

nsfw_bounties_df = bounty_ratings_df[bounty_ratings_df["rating"] == "NSFW"]
total_nsfw = len(nsfw_bounties_df) + len(
    df_best_fit[df_best_fit["best_fit_theme"] == "nsfw"]
)

merged_df = pd.merge(bounty_ratings_df, df_best_fit, on="bounty_number", how="outer")

# Fill NaN values in best_fit_theme with 'nsfw' where rating is 'NSFW'
merged_df.loc[merged_df["rating"] == "NSFW", "best_fit_theme"] = "nsfw"

result_df = pd.merge(merged_df, filtered_df, on="bounty_number", how="inner")
result_df["updated_best_fit_theme"] = result_df["best_fit_theme"]

# Create dict mapping bounty numbers to their Final Label
bounty_to_label = df_deepfake.set_index("bounty_number")["Final label"].to_dict()

# Update best_fit_theme for bounties that have a Final Label
result_df.loc[
    result_df["bounty_number"].isin(bounty_to_label.keys()), "updated_best_fit_theme"
] = result_df.loc[
    result_df["bounty_number"].isin(bounty_to_label.keys()), "bounty_number"
].map(bounty_to_label)

result_df["updated_best_fit_theme"] = result_df["updated_best_fit_theme"].replace(
    "human_deepfake", "sfw_human_deepfake"
)

updated_theme_counts = result_df["updated_best_fit_theme"].value_counts().to_dict()

result_df["theme_new"] = result_df["updated_best_fit_theme"].replace(
    {
        "nsfw": "NSFW",
        "fictional_characters": "SFW",
        "sfw_human_deepfake": "Deepfake",
        "scene_objects_clothing": "SFW",
        "style_and_culture": "SFW",
        "human_attributes": "SFW",
        "open_request": "SFW",
        "nsfw_human_deepfake": "Deepfake",
        "miscellaneous": "SFW",
        "style_and _culture": "SFW",
    }
)


def calculate_lorenz_curve(values):
    """Calculate Lorenz curve coordinates"""
    # Sort values in DESCENDING order (most bounties first)
    sorted_values = np.sort(values)[::-1]
    n = len(sorted_values)

    # Calculate cumulative proportions
    cumsum = np.cumsum(sorted_values)
    cumsum_prop = cumsum / cumsum[-1]  # Normalize to [0, 1]

    # Add (0,0) at the start
    lorenz_x = np.insert(np.arange(1, n + 1) / n, 0, 0)
    lorenz_y = np.insert(cumsum_prop, 0, 0)

    return lorenz_x, lorenz_y


def calculate_gini(values):
    """Calculate Gini coefficient"""
    sorted_values = np.sort(values)
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values)

    # Gini formula
    gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_values)) / (
        n * np.sum(sorted_values)
    ) - (n + 1) / n

    return gini


def get_y_at_x(lorenz_x, lorenz_y, target_x):
    """Get y-value at specific x using linear interpolation"""
    return np.interp(target_x, lorenz_x, lorenz_y)


# Load your data - assuming result_df is already defined
df = result_df

# Count bounties per supporter for each rating
sfw_counts = df[df["rating"] == "SFW"].groupby("supporter").size().values
nsfw_counts = df[df["rating"] == "NSFW"].groupby("supporter").size().values
deepfake_counts = df[df["theme_new"] == "Deepfake"].groupby("supporter").size().values
all_counts = df.groupby("supporter").size().values

# Calculate Lorenz curves
sfw_x, sfw_y = calculate_lorenz_curve(sfw_counts)
nsfw_x, nsfw_y = calculate_lorenz_curve(nsfw_counts)
deepfake_x, deepfake_y = calculate_lorenz_curve(deepfake_counts)
all_x, all_y = calculate_lorenz_curve(all_counts)

# Calculate Gini coefficients
gini_sfw = calculate_gini(sfw_counts)
gini_nsfw = calculate_gini(nsfw_counts)
gini_deepfake = calculate_gini(deepfake_counts)
gini_all = calculate_gini(all_counts)

# Get y-values at x=0.1 for reporting
y_sfw_20 = get_y_at_x(sfw_x, sfw_y, 0.2)
y_nsfw_20 = get_y_at_x(nsfw_x, nsfw_y, 0.2)
y_deepfake_20 = get_y_at_x(deepfake_x, deepfake_y, 0.2)

fig3, ax3 = plt.subplots(figsize=(7, 6))

# Plot equality line
ax3.plot([0, 1], [0, 1], "k--", linewidth=1.5, alpha=0.5)

# Plot Lorenz curves
ax3.plot(
    sfw_x,
    sfw_y,
    linewidth=2.5,
    label=f"SFW (Gini = {gini_sfw:.2f})",
    color="dodgerblue",
)
ax3.plot(
    nsfw_x,
    nsfw_y,
    linewidth=2.5,
    label=f"NSFW (Gini = {gini_nsfw:.2f})",
    color="firebrick",
)
ax3.plot(
    deepfake_x,
    deepfake_y,
    linewidth=2.5,
    label=f"Deepfake (Gini = {gini_deepfake:.2f})",
    color="#D29343",
)

# Add vertical line at 10%
ax3.axvline(x=0.2, color="gray", linestyle=":", linewidth=1.5, alpha=0.6, zorder=1)
# ax3.text(0.2, 1.02, '20%', ha='center', va='bottom', fontsize=14, color='red',
#  transform=ax3.get_xaxis_transform())

# Add horizontal lines from intersection to y-axis
ax3.axhline(
    y=y_deepfake_20,
    xmax=0.2,
    color="#D29343",
    linestyle=":",
    linewidth=1.5,
    alpha=0.6,
    zorder=1,
)
ax3.axhline(
    y=y_sfw_20,
    xmax=0.2,
    color="dodgerblue",
    linestyle=":",
    linewidth=1.5,
    alpha=0.6,
    zorder=1,
)
ax3.axhline(
    y=y_nsfw_20,
    xmax=0.2,
    color="firebrick",
    linestyle=":",
    linewidth=1.5,
    alpha=0.6,
    zorder=1,
)

# Add markers at the intersection points
ax3.plot(0.2, y_sfw_20, "o", color="dodgerblue", markersize=7, zorder=5)
ax3.plot(0.2, y_nsfw_20, "o", color="firebrick", markersize=7, zorder=5)
ax3.plot(0.2, y_deepfake_20, "o", color="#D29343", markersize=7, zorder=5)

# Format axes
ax3.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
ax3.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

# Set custom x-ticks to include 20%
ax3.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

# Make the 20% tick label bold and red
for label in ax3.get_xticklabels():
    if label.get_text() == "20%":
        label.set_weight("bold")
        label.set_color("red")

ax3.set_xlabel("Cumulative percentage of supporters", fontsize=16)
ax3.set_ylabel("Cumulative percentage of bounties", fontsize=16)
ax3.legend(loc="lower right", fontsize=13, frameon=False)
ax3.grid(alpha=0.3, linestyle="--", linewidth=0.5)
ax3.spines["right"].set_visible(False)
ax3.spines["top"].set_visible(False)
ax3.set_aspect("equal")

plt.tight_layout()
fig3.savefig(
    os.path.join(FIG_DIR, "user_concentration_analysis.png"),
    dpi=600,
    bbox_inches="tight",
)
fig3.savefig(
    os.path.join(FIG_DIR, "user_concentration_analysis.pdf"),
    dpi=600,
    bbox_inches="tight",
)
