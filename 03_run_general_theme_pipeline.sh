#!/bin/bash

# Purpose:
#   Run the data sampling, general theme extraction, and reliability analysis pipeline
#   for the CivitAI bounties project.
#
# Inputs:
#   - bounties_frame_w_blur.parquet: cleaned bounty metadata
#   - bounties_example_images_frame_w_blur.parquet: cleaned example image metadata
#   - bounties_in_blur_and_non_blur.txt: list of bounties common to both blurred and non-blurred data
#   - data/manual_coding/bounties_sample_clean_shalmoli_latest_round.csv: human-assigned labels
#
# Outputs:
#   - data/intermediate/YYYY-MM-DD_bounties_sample.csv: sampled bounties for annotation
#   - data/openai_responses/bounty_themes/raw/general_theme_responses__<model>.jsonl: raw OpenAI API responses
#   - results/krippendorff_alpha_results_with_f1.txt: Krippendorff's alpha scores and F1 metrics between GPT and human annotators
#
# Prerequisites:
#   - OpenAI API key (OPENAI_API_KEY) must be set in the environment
#   - Run run_data_cleaning.sh first to generate the required input files
#
# How to call:
#   bash run_general_theme_pipeline.sh
#
# Author: Shalmoli Ghosh

set -e  # Exit immediately if a command exits with a non-zero status

# Change to the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo ""
echo "================================================================================"
echo "  GENERAL THEME EXTRACTION PIPELINE"
echo "================================================================================"
echo ""

#------------------------------------------------------------------------------
# STAGE 1: Sample Bounties by Type
# NOTE: We comment this out because the script includes a date stamp in the output filename which breaks the pipeline.
# However, the script leverages a random seed, so reruns generate identical files.
# If you want to perform sampling from scratch, please uncomment the lines below.
#------------------------------------------------------------------------------
echo "STAGE 1: Sampling bounties by type — SKIPPED (see 03_run_general_theme_pipeline.sh for details)"
echo ""
# echo "STAGE 1: Sampling bounties by type"
# echo "================================================================================"
# echo "Executing code/analyze/sampling/bounty_types_sampling.py"
# uv run python code/analyze/sampling/bounty_types_sampling.py
# echo "Completed: YYYY-MM-DD_bounties_sample.csv saved to data/intermediate/"
# echo ""

#------------------------------------------------------------------------------
# STAGE 2: General Theme Extraction via OpenAI
#------------------------------------------------------------------------------
# NOTE: This stage calls the OpenAI API and will incur API costs.
# The script is run in "sample" mode, operating only on the sampled bounties.
# Change --mode to "full" to process the entire dataset.
# Change --model to "gpt-4o" to use GPT-4o instead of GPT-4.1.
# WARNING: Running the following step will incur costs based on the number of API calls made. Please ensure you have your OPENAI_API_KEY environment variable set up and be aware of potential costs before running this step.
echo "STAGE 2: Extracting general themes via OpenAI API — SKIPPED (see 03_run_general_theme_pipeline.sh for details)"
echo ""
# echo "STAGE 2: Extracting general themes via OpenAI API"
# echo "================================================================================"
# echo "Executing code/analyze/openai/general_theme_extraction.py --mode sample --model gpt-4.1"
# echo "  WARNING: This step calls the OpenAI API and will incur costs. So if you want to test this please make sure to set up your OPENAI_API_KEY environment variable and be aware of potential costs."
# echo "Make sure you are in the code/analyze/openai directory before running this command."
# uv run python general_theme_extraction.py --mode sample --model gpt-4.1
# cd "$SCRIPT_DIR"
# echo "Completed: general_theme_responses__gpt-4.1.jsonl saved to data/openai_responses/bounty_themes/raw/"
# echo ""

#------------------------------------------------------------------------------
# STAGE 3: Human Annotation (manual step — not automated)
#------------------------------------------------------------------------------
echo "STAGE 3: Human annotation (manual step)"
echo "================================================================================"
echo "  Annotated files for Stage 4 are saved here:"
echo "    data/manual_coding/bounties_sample_clean_shalmoli_latest_round.csv"
echo ""

#------------------------------------------------------------------------------
# STAGE 4: Reliability Analysis (Krippendorff's Alpha)
#------------------------------------------------------------------------------
echo "STAGE 4: Running reliability analysis (Krippendorff's alpha)"
echo "================================================================================"
echo "Executing code/analyze/reliability-analysis/calculate_krip_f1.py"
cd code/analyze/reliability-analysis
uv run python calculate_krip_f1.py
cd "$SCRIPT_DIR"
echo "Completed: krippendorff_alpha_results_with_f1.txt saved to results/"
echo ""

echo "================================================================================"
echo "  GENERAL THEME EXTRACTION PIPELINE COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
