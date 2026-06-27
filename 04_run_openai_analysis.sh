#!/bin/bash

# Purpose:
#   Run the full OpenAI-based analysis pipeline for the CivitAI bounties project,
#   covering general theme extraction, content moderation, and NSFW deepfake detection.
#   Each sub-pipeline consists of an OpenAI API call stage followed by a post-processing
#   (cleaning) stage.
#
# Inputs:
#   - bounties_frame_w_blur.parquet: cleaned bounty metadata (blurred)
#   - bounties_frame_wo_blur.parquet: cleaned bounty metadata (non-blurred)
#   - bounties_example_images_frame_w_blur.parquet: cleaned example image metadata (blurred)
#   - bounties_example_images_frame_wo_blur.parquet: cleaned example image metadata (non-blurred)
#   - common_bounties_ratings.parquet: SFW/NSFW rating labels for common bounties
#
# Outputs:
#   General Theme Extraction:
#   - data/openai_responses/bounty_themes/raw/general_theme_responses__<model>.jsonl: raw API responses
#   - data/clean/general_theme_frame.parquet: cleaned general theme annotations
#
#   Content Moderation:
#   - data/openai_responses/content_moderation/raw/content_moderation_responses.jsonl: raw API responses
#   - data/clean/content_moderation_frame.parquet: cleaned content moderation scores and flags
#
#   NSFW Deepfake Detection:
#   - data/openai_responses/deepfakes/raw/deepfake_bounties_from_nsfw__<model>.jsonl: raw API responses
#   - data/openai_responses/deepfakes/clean/deepfake_bounties_from_nsfw.csv: cleaned deepfake labels
#
# Prerequisites:
#   - OpenAI API key (OPENAI_API_KEY) must be set in the environment
#   - Run run_data_cleaning.sh first to generate required input files
#
# How to call:
#   bash run_openai_analysis.sh
#
# Author: Matthew DeVerna & Shalmoli Ghosh

set -e  # Exit immediately if a command exits with a non-zero status

# Change to the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo ""
echo "================================================================================"
echo "  OPENAI ANALYSIS PIPELINE"
echo "================================================================================"
echo ""

#------------------------------------------------------------------------------
# SUB-PIPELINE 1: General Theme Extraction
#------------------------------------------------------------------------------
echo "SUB-PIPELINE 1: General Theme Extraction"
echo "================================================================================"
echo ""

# STAGE 1A: Call OpenAI API for general theme extraction (full mode)
# NOTE: This stage calls the OpenAI API and will incur API costs.
# Change --model to "gpt-4o" to use GPT-4o instead of GPT-4.1.
# Change --mode to "sample" to run on the sampled subset only.
# WARNING: Running the following step will incur costs based on the number of API calls made. Please ensure you have your OPENAI_API_KEY environment variable set up and be aware of potential costs before running this step. If you want to run this step uncomment the following lines.
echo "STAGE 1A: Extracting general themes via OpenAI API — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 1A: Extracting general themes via OpenAI API"
# echo "Executing code/analyze/openai/general_theme_extraction.py --mode full --model gpt-4.1"
# cd code/analyze/openai
# uv run python general_theme_extraction.py --mode full --model gpt-4.1
# cd "$SCRIPT_DIR"
# echo "Completed: general_theme_responses__gpt-4.1.jsonl saved to data/openai_responses/bounty_themes/raw/"
# echo ""

# STAGE 1B: Post-process general theme extraction responses (Please uncomment to run)
echo "STAGE 1B: Post-processing general theme extraction responses — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 1B: Post-processing general theme extraction responses"
# echo "Executing code/clean/build_general_theme_df.py"
# echo "NOTE: If you want to run only the post-processing stage for general theme extraction, please ensure you have the required input files and ensure you are at the correct folder."
# uv run python build_general_theme_df.py
# echo "Completed: general_theme_frame.parquet saved to data/clean/"
# echo ""

#------------------------------------------------------------------------------
# SUB-PIPELINE 2: Content Moderation
#------------------------------------------------------------------------------
echo "SUB-PIPELINE 2: Content Moderation"
echo "================================================================================"
echo ""

# STAGE 2A: Call OpenAI API for content moderation
# NOTE: This stage calls the OpenAI API and but will not incur API costs. In case you want to run this step, please ensure you have your OPENAI_API_KEY environment variable set up. If you want to run this step uncomment the following lines and make sure you are at the correct folder.
echo "STAGE 2A: Running content moderation via OpenAI API — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 2A: Running content moderation via OpenAI API"
# echo "Executing code/analyze/openai/content_moderation.py"
# uv run python content_moderation.py
# cd "$SCRIPT_DIR"
# echo "Completed: content_moderation_responses.jsonl saved to data/openai_responses/content_moderation/raw/"
# echo ""

# STAGE 2B: Post-process content moderation responses. To run this step, please ensure you have the required input files and ensure you are at the correct folder.
echo "STAGE 2B: Post-processing content moderation responses — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 2B: Post-processing content moderation responses"
# echo "Executing code/clean/build_content_moderation_df.py"
# uv run python build_content_moderation_df.py
# echo "Completed: content_moderation_frame.parquet saved to data/clean/"
# echo ""

#------------------------------------------------------------------------------
# SUB-PIPELINE 3: NSFW Deepfake Detection
#------------------------------------------------------------------------------
echo "SUB-PIPELINE 3: NSFW Deepfake Detection"
echo "================================================================================"
echo ""

# STAGE 3A: Call OpenAI API for deepfake detection (NSFW bounties only)
# NOTE: This stage calls the OpenAI API and will incur API costs.
# Change --model to "gpt-4o" to use GPT-4o instead of GPT-4.1.
#WARNING: This step calls the OpenAI API and will incur costs. Running this from scratch might change results. Please uncomment and run the script if you want to run this step, and make sure that you are at the correct folder."
echo "STAGE 3A: Extracting deepfake labels via OpenAI API — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 3A: Extracting deepfake labels via OpenAI API"
# echo "Executing code/analyze/openai/deepfake_extraction.py --model gpt-4.1"
# uv run python deepfake_extraction.py --model gpt-4.1
# cd "$SCRIPT_DIR"
# echo "Completed: deepfake_bounties_from_nsfw__gpt-4.1.jsonl saved to data/openai_responses/deepfakes/raw/"
# echo ""

# STAGE 3B: Post-process deepfake detection responses. To run this step, please ensure you have the required input files and ensure you are at the correct folder.
echo "STAGE 3B: Post-processing deepfake detection responses — SKIPPED (see 04_run_openai_analysis.sh for details)"
echo ""
# echo "STAGE 3B: Post-processing deepfake detection responses"
# echo "Executing code/clean/build_deepfake_nsfw_df.py"
# uv run python build_deepfake_nsfw_df.py
# echo "Completed: deepfake_bounties_from_nsfw.csv saved to data/openai_responses/deepfakes/clean/"
# echo ""

echo "================================================================================"
echo "  OPENAI ANALYSIS PIPELINE COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
