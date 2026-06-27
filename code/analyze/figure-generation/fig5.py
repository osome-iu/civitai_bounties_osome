"""
Purpose:
- Generate the deepfake moderation figure (fig 5) presented in the paper.

Inputs:
- overall_deepfake_validation_published.csv: cleaned dataframe containing the validated deepfake data.

Outputs:
- deepfake_nsfw_sfw_stacked.pdf

Author:
- Shalmoli Ghosh
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
INTERMEDIATE_DIR = "../../../data/intermediate"

FIG_DIR = "../../../results/figures"
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 14

# Load the deepfake validation data
df_deepfake = pd.read_csv(os.path.join(INTERMEDIATE_DIR, "overall_deepfake_validation_published.csv"))

deepfakes_df = df_deepfake[df_deepfake['Deepfake'] == "yes"].copy()

# Create a crosstab of Deepfake (yes/no) by Category (NSFW/SFW)
deepfake_category = pd.crosstab(deepfakes_df['Category'], deepfakes_df['Marked in Platform'])

# Reorder columns to have 'no' first, then 'yes' (SWAPPED ORDER)
if 'yes' in deepfake_category.columns and 'no' in deepfake_category.columns:
    deepfake_category = deepfake_category[['no', 'yes']]

# Calculate percentages for each category (row-wise)
deepfake_category_pct = deepfake_category.div(deepfake_category.sum(axis=1), axis=0) * 100

# Keep the counts for reference
deepfake_category_counts = deepfake_category.copy()

fig, ax = plt.subplots(figsize=(6, 3.5))
colors = {'no': '#926390', 'yes': '#4B3B66'}
legend_labels = {'no': 'Not marked', 'yes': 'Marked'}

# Plot stacked horizontal bar chart using percentages with increased height
left = None
for col in deepfake_category_pct.columns:
    if left is None:
        bars = ax.barh(
            deepfake_category_pct.index,
            deepfake_category_pct[col],
            height=0.7, 
            label=legend_labels[col],
            color=colors.get(col, 'gray'),
            edgecolor='white',
            linewidth=1.5
        )
        left = deepfake_category_pct[col].values
    else:
        bars = ax.barh(
            deepfake_category_pct.index,
            deepfake_category_pct[col],
            left=left,
            height=0.7,
            label=legend_labels[col],
            color=colors.get(col, 'gray'),
            edgecolor='white',
            linewidth=1.5
        )
        left = left + deepfake_category_pct[col].values

# Add percentage and count labels inside bars
for i, category in enumerate(deepfake_category_pct.index):
    cumsum = 0
    for col in deepfake_category_pct.columns:
        pct_value = deepfake_category_pct.loc[category, col]
        count_value = deepfake_category_counts.loc[category, col]
        if pct_value > 0:
            ax.text(
                cumsum + pct_value / 2,
                i,
                f'{pct_value:.1f}%',
                ha='center',
                va='center',
                fontsize=12,
                
                color='white'
            )
        cumsum += pct_value

# Formatting
ax.set_xlabel('Percentage', fontsize=16)

# Position legend above the plot area
ax.legend(loc='upper left', fontsize=14, frameon=False, bbox_to_anchor=(0, 1.15), ncol=2)
ax.set_xlim(0, 100)

# Add % sign to x-axis tick labels
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))

ax.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.set_axisbelow(True)

fig_fp_pdf = os.path.join(FIG_DIR, "deepfake_nsfw_sfw_stacked.pdf")
fig_fp_png = os.path.join(FIG_DIR, "deepfake_nsfw_sfw_stacked.png")
fig.savefig(fig_fp_pdf, dpi=600, bbox_inches="tight")
fig.savefig(fig_fp_png, dpi=600, bbox_inches="tight")