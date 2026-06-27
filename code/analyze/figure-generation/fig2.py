"""
Purpose:
- Generate the type, theme, temporal figure presented in the paper.

Inputs:
- bounties_frame_w_blur_published.parquet: cleaned dataframe containing the complete bounty data .
- bounties_example_images_frame_w_blur_published.parquet: cleaned dataframe containing the complete bounty example images data.
- bounties_in_blur_and_non_blur.txt: list of common bounty numbers in the blurred and non-blurred version of the data.
- common_bounties_ratings_published.parquet: cleaned dataframe containing the ratings of the common bounties by the platform.
- general_theme_clean_published.parquet: cleaned dataframe containing the general theme assigned to each bounty by GPT models.
- overall_deepfake_validation_published.csv: cleaned dataframe containing the validated deepfake data.

Outputs:
- bounty_ts_count_props.pdf
- bounty_ts_count_props.png

Author:
- Shalmoli Ghosh
"""

import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14
plt.rcParams["axes.labelsize"] = 16
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["xtick.labelsize"] = 14
plt.rcParams["ytick.labelsize"] = 14
plt.rcParams["legend.fontsize"] = 14
plt.rcParams["figure.titlesize"] = 18


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

result_df["best_fit_theme_new"] = result_df["updated_best_fit_theme"].replace(
    {
        "nsfw": "NSFW",
        "fictional_characters": "SFW",
        "sfw_human_deepfake": "SFW",
        "scene_objects_clothing": "SFW",
        "style_and_culture": "SFW",
        "human_attributes": "SFW",
        "open_request": "SFW",
        "nsfw_human_deepfake": "NSFW",
        "miscellaneous": "SFW",
        "style_and _culture": "SFW",
    }
)

# Average and total buzz by SFW / NSFW : Uncomment the below lines if you want to see the average and total buzz by SFW/NSFW category.
# buzz_stats = result_df.groupby("best_fit_theme_new")["buzz"].agg(["mean", "sum", "std"])
# buzz_stats.columns = ["avg_buzz", "total_buzz", "std_buzz"]
# print("Buzz stats by content type:")
# print(buzz_stats.to_string())

result_df = result_df.set_index("started_dt")
result_df["year"] = result_df.index.year
result_df["month"] = result_df.index.month
result_df["week"] = result_df.index.isocalendar().week

count_data = (
    result_df.groupby(["bounty_type", "best_fit_theme_new"], observed=False)
    .size()
    .unstack()
)

if "Data Set Caption" in count_data.index and "Data Set Creation" in count_data.index:
    count_data.loc["Data Set Creation"] += count_data.loc["Data Set Caption"]
    count_data = count_data.drop("Data Set Caption")

count_data["total"] = count_data.sum(axis=1)
count_data = count_data.sort_values(by="total", ascending=True)

count_data.index = [
    val.replace(" Creation", "").replace("Lora", "LoRA") for val in count_data.index
]

# Group by year, month, week, and extreme_nsfw to get the count of bounty types
weekly_counts = (
    result_df.groupby(["year", "week", "best_fit_theme_new"], observed=False)
    .size()
    .unstack(fill_value=0)
)

weekly_counts = weekly_counts.reset_index()
weekly_counts.columns.name = None

weekly_proportions = (
    weekly_counts[["SFW", "NSFW"]]
    .div(weekly_counts[["SFW", "NSFW"]].sum(axis=1), axis=0)
    .fillna(0)
)

# Add the year and week columns
weekly_proportions["year"] = weekly_counts["year"]
weekly_proportions["week"] = weekly_counts["week"]

# Drop rows with all zeros in the specified columns for weekly_proportions
weekly_proportions = weekly_proportions[
    ~((weekly_proportions[["SFW", "NSFW"]] == 0).all(axis=1))
]

weekly_counts = weekly_counts[~((weekly_counts[["SFW", "NSFW"]] == 0).all(axis=1))]

# We want to let matplotlib use the datetime format to make the x-axis scale more readable
# So here, we create a column with datetime objects for each week.
dts = []
for yr, wk in zip(weekly_proportions["year"], weekly_proportions["week"]):
    dts.append(datetime.date.fromisocalendar(yr, wk, 1))

weekly_proportions["dt"] = dts

weekly_proportions["NSFW"] = 1 - weekly_proportions["SFW"]

proportions_data = count_data[["SFW", "NSFW"]].div(
    count_data[["total"]].sum(axis=1), axis=0
)

total_bounties = count_data["total"].sum()
count_data_proportions = count_data["total"] / total_bounties

# Define colorblind-friendly colors
colors = {
    "SFW": "dodgerblue",
    "NSFW": "firebrick",
}


# Create a figure with a gridspec layout
fig = plt.figure(figsize=(16, 10))
gs = GridSpec(
    2, 2, width_ratios=[4, 7], wspace=0.65, hspace=0.35, figure=fig
)  # Increased spacing


# Create four subplots
ax_right1 = fig.add_subplot(gs[0, 0])
ax_main = fig.add_subplot(gs[1, 1])
ax_right2 = fig.add_subplot(gs[1, 0])
ax_left2 = fig.add_subplot(gs[0, 1])


# CREATE TIMESERIES PLOT
# --------------------------------------------

# Plot the time series
for category in ["SFW", "NSFW"]:
    ax_main.plot(
        weekly_proportions["dt"],
        weekly_proportions[category],
        label=category,
        color=colors[category],
        linewidth=0,
        marker=".",
        zorder=3,
        alpha=0.25,
    )

# Fit a linear regression line for SFW
z_sfw = np.polyfit(
    mdates.date2num(weekly_proportions["dt"]), weekly_proportions["SFW"], 1
)
p_sfw = np.poly1d(z_sfw)
ax_main.plot(
    weekly_proportions["dt"],
    p_sfw(mdates.date2num(weekly_proportions["dt"])),
    color=colors["SFW"],
    linestyle="-",
    zorder=2,
)

# Fit a linear regression line for NSFW
z_nsfw = np.polyfit(
    mdates.date2num(weekly_proportions["dt"]), weekly_proportions["NSFW"], 1
)
p_nsfw = np.poly1d(z_nsfw)
ax_main.plot(
    weekly_proportions["dt"],
    p_nsfw(mdates.date2num(weekly_proportions["dt"])),
    color=colors["NSFW"],
    linestyle="-",
    zorder=2,
)

# Parameters
n_bootstraps = 1000
weekly_dates = weekly_proportions["dt"]
num_weeks = len(weekly_dates)

# Storage for bootstrapped estimates
ci_sfw = np.zeros((n_bootstraps, num_weeks))
ci_nsfw = np.zeros((n_bootstraps, num_weeks))

for i in range(n_bootstraps):
    # Block bootstrap: Sample contiguous chunks instead of independent points
    sample_indices = np.random.choice(num_weeks, num_weeks, replace=True)
    sample = weekly_proportions.iloc[sample_indices].sort_values(
        "dt"
    )  # Ensure chronological order

    sample_dates = mdates.date2num(sample["dt"])

    # Fit a linear trend for each bootstrap sample
    z_sfw_boot = np.polyfit(sample_dates, sample["SFW"], 1)
    p_sfw_boot = np.poly1d(z_sfw_boot)
    ci_sfw[i, :] = p_sfw_boot(mdates.date2num(weekly_dates))

    z_nsfw_boot = np.polyfit(sample_dates, sample["NSFW"], 1)
    p_nsfw_boot = np.poly1d(z_nsfw_boot)
    ci_nsfw[i, :] = p_nsfw_boot(mdates.date2num(weekly_dates))

# Compute 95% confidence intervals
ci_sfw_lower = np.percentile(ci_sfw, 2.5, axis=0)
ci_sfw_upper = np.percentile(ci_sfw, 97.5, axis=0)
ci_nsfw_lower = np.percentile(ci_nsfw, 2.5, axis=0)
ci_nsfw_upper = np.percentile(ci_nsfw, 97.5, axis=0)

# Confidence intervals for SFW
ax_main.fill_between(
    weekly_dates,
    ci_sfw_lower,
    ci_sfw_upper,
    color=colors["SFW"],
    alpha=0.2,
    label="95% CI SFW",
)

# Confidence intervals for NSFW
ax_main.fill_between(
    weekly_dates,
    ci_nsfw_lower,
    ci_nsfw_upper,
    color=colors["NSFW"],
    alpha=0.2,  # Fixed alpha value
    label="95% CI NSFW",
)

# Add text to the right of the most recent data point for each category
ax_main.text(
    weekly_proportions["dt"].iloc[-1],
    p_sfw(mdates.date2num(weekly_proportions["dt"]))[-1],
    "SFW",
    color=colors["SFW"],
    fontsize=16,
    ha="left",
    va="center",
    zorder=0,
)

ax_main.text(
    weekly_proportions["dt"].iloc[-1],
    p_nsfw(mdates.date2num(weekly_proportions["dt"]))[-1],
    "NSFW",
    color=colors["NSFW"],
    fontsize=16,
    ha="left",
    va="center",
    zorder=0,
)

# Add vertical lines that mark the beginning of 2024 and 2025
ax_main.axvline(pd.Timestamp("2024-01-01"), color="k", linestyle="--", linewidth=1)
ax_main.axvline(pd.Timestamp("2025-01-01"), color="k", linestyle="--", linewidth=1)

# Label the vertical lines
ax_main.text(
    pd.Timestamp("2024-01-01"),
    ax_main.get_ylim()[1],
    "2024",
    color="k",
    fontsize=16,
    ha="left",
    va="top",
)
ax_main.text(
    pd.Timestamp("2025-01-01"),
    ax_main.get_ylim()[1],
    "2025",
    color="k",
    fontsize=16,
    ha="left",
    va="top",
)


# Format the xaxis scale nicely
ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

ax_main.set_ylabel("Proportion of bounties", fontsize=16)
ax_main.set_ylim(0, 1)
ax_main.yaxis.grid(True)
ax_main.spines["top"].set_visible(False)
ax_main.spines["right"].set_visible(False)

from matplotlib.lines import Line2D

legend_elements = [
    Line2D([0], [0], color=colors["SFW"], linewidth=2, label="SFW"),
    Line2D([0], [0], color=colors["NSFW"], linewidth=2, label="NSFW"),
]
ax_main.legend(handles=legend_elements, loc="upper center", frameon=False, fontsize=16)

# Plot the bar plot

bars_type = ax_right1.barh(
    range(len(count_data_proportions)), count_data_proportions, color="k", zorder=3
)

cleaned_types = [
    label.replace("_", " ").title().replace("Lora", "LoRA")
    for label in count_data_proportions.keys()
]

# Put the x-axis on top
ax_right1.xaxis.set_ticks_position("top")
ax_right1.xaxis.set_label_position("top")
ax_right1.set_xlabel("Proportion of bounties", fontsize=16)

ax_right1.set_yticks(range(len(cleaned_types)))  # Changed from xticks to yticks
ax_right1.set_yticklabels(cleaned_types)  # Changed from xticklabels, removed rotation
ax_right1.set_xlim(0, max(count_data_proportions) * 1.15)  # Changed from ylim to xlim
ax_right1.set_axisbelow(True)

# Add a grid
ax_right1.grid(axis="x", linestyle="--", alpha=0.6, zorder=-1)

# Reformat the x-axis values to be in proportions with 1 decimal place
ax_right1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.1f}"))

ax_right1.spines["bottom"].set_visible(False)
ax_right1.spines["right"].set_visible(False)

# Add count values to the right of each bar (where the bar ends)
for i, (index, row) in enumerate(count_data.iterrows()):
    proportion = count_data_proportions.iloc[i]
    ax_right1.text(
        proportion,  # Position at the end of the bar
        i,
        f"{row['total']:,}",
        va="center",
        ha="left",
        color="black",
        fontsize=16,
    )

# CREATE BOTTOM LEFT HORIZONTAL PROPORTIONS PLOT
# --------------------------------------------

# Plot a stacked bar chart for each bounty type (already sorted by total count)

# Plot the NSFW bar
ax_right2.barh(
    proportions_data.index,
    proportions_data["NSFW"],
    color=colors["NSFW"],
    label="NSFW",
    zorder=3,
)

# Plot the SFW bar
ax_right2.barh(
    proportions_data.index,
    proportions_data["SFW"],
    left=proportions_data["NSFW"],
    color=colors["SFW"],
    label="SFW",
    zorder=3,
)

# Add the proportions of each bar to the right and inside of the left most point of the bar
for i, (index, row) in enumerate(proportions_data.iterrows()):
    ax_right2.text(
        row["NSFW"] + row["SFW"],  # Position to the right of the SFW bar
        i,
        f"{row['SFW']:.0%}",
        va="center",
        ha="right",
        color="white",
        fontsize=16,
    )
    ax_right2.text(
        0,
        i,
        f"{row['NSFW']:.0%}",
        va="center",
        ha="left",
        color="white",
        fontsize=16,
    )

# Add a vertical line at .5
ax_right2.axvline(0.5, color="k", linestyle="-", linewidth=1)

# Remove the top and left spines
ax_right2.spines["top"].set_visible(False)
ax_right2.spines["right"].set_visible(False)

# Add x-axis label
ax_right2.set_xlabel("Proportion of bounties", fontsize=16)

# CREATE BOTTOM Right HORIZONTAL PROPORTIONS PLOT
# --------------------------------------------

if "human_deepfake" in updated_theme_counts:
    updated_theme_counts["sfw_human_deepfake"] = updated_theme_counts.pop(
        "human_deepfake"
    )

# Clean up x-tick labels: remove underscores and capitalize
cleaned_labels = [
    label.replace("_", " ").title().replace("Nsfw", "NSFW").replace("Sfw", "SFW")
    for label in updated_theme_counts.keys()
]

# Calculate proportions
total_count = sum(updated_theme_counts.values())
proportions = [count / total_count for count in updated_theme_counts.values()]

bar_colors = [
    "firebrick" if ("nsfw_human_deepfake" in key or key == "nsfw") else "dodgerblue"
    for key in updated_theme_counts.keys()
]


bars = ax_left2.barh(  # Changed from bar to barh
    range(len(proportions)),
    proportions,
    color=bar_colors,
    edgecolor="white",
    linewidth=1.5,
)

ax_left2.set_xlabel("Proportion of bounties", fontsize=16)  # Swapped xlabel/ylabel
# ax_left2.set_ylabel('Bounty theme', fontsize=16)
ax_left2.set_yticks(range(len(cleaned_labels)))  # Changed from xticks to yticks
ax_left2.set_yticklabels(cleaned_labels)  # Changed from xticklabels, removed rotation
ax_left2.set_xlim(0, max(proportions) * 1.15)  # Changed from ylim to xlim
ax_left2.set_axisbelow(True)
ax_left2.xaxis.grid(True)  # Changed from yaxis to xaxis

# Move x-axis to top
ax_left2.xaxis.set_ticks_position("top")
ax_left2.xaxis.set_label_position("top")

# Remove bottom spine and show top spine
ax_left2.spines["bottom"].set_visible(False)
ax_left2.spines["top"].set_visible(True)
ax_left2.spines["right"].set_visible(False)

for i, (bar, count) in enumerate(zip(bars, updated_theme_counts.values())):
    ax_left2.text(
        bar.get_width(),
        bar.get_y() + bar.get_height() / 2.0,
        f"{int(count):,}",
        ha="left",
        va="center",
        fontsize=16,  # Changed ha/va
    )

# --- Add legend for the two hatch styles ---
legend_handles = [
    plt.Rectangle((0, 0), 1, 1, color="firebrick", ec="white", lw=0.5, label="NSFW"),
    plt.Rectangle((0, 0), 1, 1, color="dodgerblue", ec="white", lw=0.5, label="SFW"),
]
ax_left2.legend(handles=legend_handles, fontsize=12, loc="best", frameon=False)

ax_left2.invert_yaxis()  # Changed from invert_xaxis

# Add letters to the top left of each axis
ax_main.text(
    -0.3,
    1.1,
    "(d)",
    transform=ax_main.transAxes,
    fontsize=16,
    va="top",
    ha="right",
)

ax_right1.text(
    -0.1,
    1.1,
    "(a)",
    transform=ax_right1.transAxes,
    fontsize=16,
    va="top",
    ha="right",
)

ax_right2.text(
    -0.1,
    1.1,
    "(c)",
    transform=ax_right2.transAxes,
    fontsize=16,
    va="top",
    ha="right",
)
ax_left2.text(
    -0.3,
    1.1,
    "(b)",
    transform=ax_left2.transAxes,
    fontsize=16,
    va="top",
    ha="right",
)


# Save the figure
fig_fp_png = os.path.join(FIG_DIR, "bounty_ts_count_props.png")
fig_fp_pdf = os.path.join(FIG_DIR, "bounty_ts_count_props.pdf")
fig.savefig(fig_fp_png, dpi=300, bbox_inches="tight")
fig.savefig(fig_fp_pdf, dpi=300, bbox_inches="tight")
