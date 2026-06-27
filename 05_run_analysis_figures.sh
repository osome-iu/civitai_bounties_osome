#!/bin/bash

# Purpose:
#   Run the results generation pipeline for the CivitAI bounties project,
#   including content moderation robustness analysis and all paper figures.
#
# Inputs:
#   - bounties_frame_w_blur_published.parquet: cleaned bounty metadata
#   - bounties_example_images_frame_w_blur_published.parquet: cleaned example image metadata
#   - bounties_in_blur_and_non_blur.txt: list of bounties common to both blurred and non-blurred data
#   - common_bounties_ratings_published.parquet: SFW/NSFW rating labels for common bounties
#   - general_theme_clean_published.parquet: GPT-assigned general theme labels
#   - overall_deepfake_validation_published.csv: validated deepfake labels
#   - data/openai_responses/content_moderation/: raw and cleaned content moderation responses
#
# Outputs:
#   Robustness Analysis:
#   - results/content_moderation_robustness_analysis_<scheme>.txt: classification report, Cohen's kappa, MCC (one file per rating scheme: default, R-as-SFW, R-and-X-as-SFW)
#
#   Figures (saved to results/figures/):
#   - bounty_ts_count_props.pdf/.png (Fig. 2): bounty type, theme, and temporal trends
#   - deepfake_analysis_revised.pdf (Fig. 3): deepfake analysis
#   - user_concentration_analysis.pdf/.png (Fig. 4): user concentration analysis
#   - deepfake_nsfw_sfw_stacked.pdf (Fig. 5): deepfake moderation breakdown
#
# Prerequisites:
#   - Run run_data_cleaning.sh and run_openai_analysis.sh first to generate required input files
#
# How to call:
#   bash run_analysis_figures.sh
#
# Author: Shalmoli Ghosh

set -e  # Exit immediately if a command exits with a non-zero status

# Change to the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo ""
echo "================================================================================"
echo "  ANALYSIS AND FIGURE GENERATION PIPELINE"
echo "================================================================================"
echo ""

#------------------------------------------------------------------------------
# STAGE 1: Content Moderation Robustness Analysis
#------------------------------------------------------------------------------
echo "STAGE 1: Content moderation robustness analysis"
echo "================================================================================"
echo "Executing code/analyze/content-mod-robustness-analysis/robustness.py"
cd code/analyze/content-mod-robustness-analysis
uv run python robustness.py
cd "$SCRIPT_DIR"
echo "Completed: content_moderation_robustness_analysis_<scheme>.txt saved to results/"
echo ""

#------------------------------------------------------------------------------
# STAGE 2: Figure 2 — Bounty Type, Theme, and Temporal Trends
#------------------------------------------------------------------------------
echo "STAGE 2: Generating Figure 2 (bounty type, theme, and temporal trends)"
echo "================================================================================"
echo "Executing code/analyze/figure-generation/fig2.py"
cd ../figure-generation
uv run python fig2.py
cd "$SCRIPT_DIR"
echo "Completed: bounty_ts_count_props.pdf/.png saved to results/figures/"
echo ""

#------------------------------------------------------------------------------
# STAGE 3: Figure 3 — Deepfake Analysis
#------------------------------------------------------------------------------
echo "STAGE 3: Generating Figure 3 (deepfake analysis)"
echo "================================================================================"
echo "Executing code/analyze/figure-generation/fig3.py"
uv run python fig3.py
cd "$SCRIPT_DIR"
echo "Completed: deepfake_analysis_revised.pdf saved to results/figures/"
echo ""

#------------------------------------------------------------------------------
# STAGE 4: Figure 4 — User Concentration Analysis
#------------------------------------------------------------------------------
echo "STAGE 4: Generating Figure 4 (user concentration analysis)"
echo "================================================================================"
echo "Executing code/analyze/figure-generation/fig4.py"
uv run python fig4.py
cd "$SCRIPT_DIR"
echo "Completed: user_concentration_analysis.pdf/.png saved to results/figures/"
echo ""

#------------------------------------------------------------------------------
# STAGE 5: Figure 5 — Deepfake Moderation Breakdown
#------------------------------------------------------------------------------
echo "STAGE 5: Generating Figure 5 (deepfake intervention by the platform)"
echo "================================================================================"
echo "Executing code/analyze/figure-generation/fig5.py"
uv run python fig5.py
cd "$SCRIPT_DIR"
echo "Completed: deepfake_nsfw_sfw_stacked.pdf saved to results/figures/"
echo ""

echo "================================================================================"
echo "  ANALYSIS AND FIGURE GENERATION PIPELINE COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
