"""
Purpose:
- Generate the deepfake figure (fig 3) presented in the paper.

Inputs:
- bounties_frame_w_blur.parquet: cleaned dataframe containing the complete bounty data .
- overall_deepfake_validation.csv: cleaned dataframe containing the validated deepfake data.
- bounties_in_blur_and_non_blur.txt: list of common bounty numbers in the blurred and non-blurred version of the data.

Outputs:
- deepfake_analysis_revised.pdf

Author:
- Shalmoli Ghosh
"""

import os
import matplotlib.pyplot as plt
import pandas as pd

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
DATA_DIR = "../../../data/clean"
INTERMEDIATE_DIR = "../../../data/intermediate"

FIG_DIR = "../../../results/figures"
os.makedirs(FIG_DIR, exist_ok=True)

df = pd.read_parquet(
    os.path.join(DATA_DIR, "bounties_frame_w_blur_published.parquet"), engine="pyarrow"
)

temp_fp = os.path.join(INTERMEDIATE_DIR, "bounties_in_blur_and_non_blur.txt")

with open(temp_fp, "r") as f:
    common_bounties = [int(line) for line in f]

filtered_df = df[df["bounty_number"].isin(common_bounties)]
df_deepfake = pd.read_csv(
    os.path.join(INTERMEDIATE_DIR, "overall_deepfake_validation_published.csv")
)
merged_df = pd.merge(df_deepfake, filtered_df, on="bounty_number", how="inner")
valid_deepfake = df_deepfake[df_deepfake["Deepfake"] == "yes"]

# Set font properties for better visibility in papers
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 14
plt.rcParams["axes.labelsize"] = 16
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["xtick.labelsize"] = 14
plt.rcParams["ytick.labelsize"] = 14
plt.rcParams["legend.fontsize"] = 14
plt.rcParams["figure.titlesize"] = 18


fig = plt.figure(figsize=(16, 6))
gs = fig.add_gridspec(2, 2, wspace=0.45, hspace=0.15, width_ratios=[1, 2], figure=fig)
ax1_top = fig.add_subplot(gs[0, 0])
ax1_bottom = fig.add_subplot(gs[1, 0])
ax2 = fig.add_subplot(gs[:, 1])
axes = [ax1_top, ax1_bottom, ax2]

# ============= SUBPLOT 1: Gender Distribution - Split by Category =============
deepfakes_df = merged_df[merged_df["Deepfake"] == "yes"].copy()

deepfakes_df["Gender"] = deepfakes_df["Gender"].str.capitalize()

gender_category = pd.crosstab(deepfakes_df["Gender"], deepfakes_df["Category"])

# Calculate percentages based on category totals
category_totals = gender_category.sum(axis=0)
gender_category_pct = {}
for category in gender_category.columns:
    gender_category_pct[category] = (
        gender_category[category] / category_totals[category]
    ) * 100

colors = {"NSFW": "firebrick", "SFW": "dodgerblue"}

# Reorder genders to ensure consistent display
gender_order = sorted(gender_category.index.tolist())
gender_order_nsfw = ["Female", "Male"]
y_pos = range(len(gender_order))
y_pos_nsfw = range(len(gender_order_nsfw))

# --- TOP SUBPLOT: NSFW (horizontal bars at position 0,0) ---
if "NSFW" in gender_category.columns:
    nsfw_values = [
        gender_category.loc[g, "NSFW"] if g in gender_category.index else 0
        for g in gender_order_nsfw
    ]
    nsfw_pct = [
        gender_category_pct["NSFW"].loc[g] if g in gender_category.index else 0
        for g in gender_order_nsfw
    ]

    bars = ax1_top.barh(
        y_pos_nsfw,
        nsfw_values,
        height=0.5,  # Bar width
        color=colors["NSFW"],
        edgecolor="white",
        linewidth=1.5,
    )

    # Add percentages at the end of bars
    for i, (bar, val, pct) in enumerate(zip(bars, nsfw_values, nsfw_pct)):
        if val > 0:
            ax1_top.text(
                val * 1.02,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%",
                ha="left",
                va="center",
                fontsize=16,
            )

    # ax1_top.set_ylabel('Gender', fontsize=16, color='black')
    ax1_top.set_xlabel("Number of Bounties", fontsize=16)
    ax1_top.set_yticks(y_pos_nsfw)
    ax1_top.set_yticklabels(gender_order_nsfw, fontsize=16)
    ax1_top.invert_yaxis()
    ax1_top.xaxis.tick_top()
    ax1_top.xaxis.set_label_position("top")
    ax1_top.spines["bottom"].set_visible(False)
    ax1_top.spines["right"].set_visible(False)
    ax1_top.grid(axis="x", alpha=0.6, linewidth=1.2, linestyle="--", color="gray")
    ax1_top.set_axisbelow(True)


# --- BOTTOM SUBPLOT: SFW (horizontal bars at position 1,0) ---
if "SFW" in gender_category.columns:
    sfw_values = [
        gender_category.loc[g, "SFW"] if g in gender_category.index else 0
        for g in gender_order
    ]
    sfw_pct = [
        gender_category_pct["SFW"].loc[g] if g in gender_category.index else 0
        for g in gender_order
    ]

    bars = ax1_bottom.barh(
        y_pos,
        sfw_values,
        height=0.6,  # Bar width
        color=colors["SFW"],
        edgecolor="white",
        linewidth=1.5,
    )

    # Add percentages at the end of bars
    for i, (bar, val, pct) in enumerate(zip(bars, sfw_values, sfw_pct)):
        if val > 0:
            ax1_bottom.text(
                val * 1.02,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%",
                ha="left",
                va="center",
                fontsize=16,
            )

    # ax1_bottom.set_ylabel('Gender', fontsize=16, color='black')
    # ax1_bottom.set_xlabel('Number of Bounties', fontsize=16)
    ax1_bottom.set_yticks(y_pos)
    ax1_bottom.set_yticklabels(gender_order, fontsize=16)
    ax1_bottom.invert_yaxis()  # Invert y-axis to match profession plot style
    # ax1_bottom.set_xscale('log')
    ax1_bottom.xaxis.tick_top()
    ax1_bottom.xaxis.set_label_position("top")
    ax1_bottom.spines["bottom"].set_visible(False)
    ax1_bottom.spines["right"].set_visible(False)
    ax1_bottom.grid(axis="x", alpha=0.6, linewidth=1.2, linestyle="--", color="gray")
    ax1_bottom.set_axisbelow(True)
    # ax1_bottom.set_ylim(-0.5, len(gender_order) - 0.5)  # Reduce vertical space around bars

ax1_top.text(
    -0.2, 1.12, "(a)", transform=ax1_top.transAxes, fontsize=18, va="top", ha="right"
)

# ============= SUBPLOT 2: Profession Distribution (Stacked by Category) =============
deepfakes_df["Final Professon Label"] = deepfakes_df["Final Professon Label"].replace(
    {
        "Actress": "Actor/Actress",
        "Actor": "Actor/Actress",
        "actress": "Actor/Actress",
        "actor": "Actor/Actress",
        "associated with adult industry": "Adult Worker",
        "not found": "Self/Spouse",
        "sportsman": "Athlete",
    }
)

# Capitalize profession labels
deepfakes_df["Final Professon Label"] = deepfakes_df[
    "Final Professon Label"
].str.capitalize()

# Create crosstab for profession vs category
profession_category = pd.crosstab(
    deepfakes_df["Final Professon Label"], deepfakes_df["Category"]
)

profession_totals = profession_category.sum(axis=1).sort_values(ascending=False)
profession_category = profession_category.loc[profession_totals.index]

# Calculate percentages
total_profession = profession_totals.sum()
profession_percentages = (profession_totals / total_profession) * 100

# Plot stacked horizontal bars
y_pos_prof = range(len(profession_category.index))
left = None

for category in profession_category.columns:
    if left is None:
        ax2.barh(
            y_pos_prof,
            profession_category[category],
            label=category,
            color=colors.get(category, "gray"),
            edgecolor="white",
            linewidth=1.5,
        )
        left = profession_category[category].values
    else:
        ax2.barh(
            y_pos_prof,
            profession_category[category],
            left=left,
            label=category,
            color=colors.get(category, "gray"),
            edgecolor="white",
            linewidth=1.5,
        )
        left = left + profession_category[category].values

ax2.set_xlabel("Number of Bounties", fontsize=16)
ax2.set_yticks(y_pos_prof)
ax2.set_yticklabels(profession_category.index, fontsize=16)
ax2.invert_yaxis()
ax2.set_xlim(0, max(profession_totals.values) * 1.25)
ax2.set_axisbelow(True)
ax2.grid(axis="x", alpha=0.6, linewidth=1.2, linestyle="--", color="gray")
ax2.xaxis.tick_top()
ax2.xaxis.set_label_position("top")

# Add overall percentage at the end of each bar
for i, pct in enumerate(profession_percentages.values):
    ax2.text(
        profession_totals.values[i] + max(profession_totals.values) * 0.015,
        i,
        f"{pct:.1f}%",
        va="center",
        ha="left",
        fontsize=16,
    )

ax2.text(-0.15, 1.07, "(b)", transform=ax2.transAxes, fontsize=18, va="top", ha="right")
ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.legend(loc="best", fontsize=16)

fig_fp_pdf = os.path.join(FIG_DIR, "deepfake_analysis_revised.pdf")
fig_fp_png = os.path.join(FIG_DIR, "deepfake_analysis_revised.png")
fig.savefig(fig_fp_pdf, dpi=600, bbox_inches="tight")
fig.savefig(fig_fp_png, dpi=600, bbox_inches="tight")
