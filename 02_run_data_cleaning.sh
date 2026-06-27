#!/bin/bash

# Purpose:
#   Run the full data cleaning pipeline for the CivitAI bounties project.
#   Scripts are executed sequentially, each building on the outputs of the previous step.
#
# Inputs:
#   - Raw CivitAI bounty HTML data (paths defined within each script)
#
# Outputs:
#   - bounties_frame_w_blur.parquet: cleaned bounty metadata from blurred data
#   - bounties_frame_wo_blur.parquet: cleaned bounty metadata from non-blurred data
#   - bounties_example_images_frame_w_blur.parquet: cleaned example image metadata from blurred data
#   - bounties_example_images_frame_wo_blur.parquet: cleaned example image metadata from non-blurred data
#   - bounties_in_blur_and_non_blur.txt: bounties present in both blurred and non-blurred data
#   - bounties_in_w_blur_not_in_wo_blur.txt: bounties only in blurred data
#   - bounties_in_wo_blur_not_in_w_blur.txt: bounties only in non-blurred data
#   - common_bounties_ratings.parquet: SFW/NSFW rating labels for common bounties
#
# How to call:
#   bash run_data_cleaning.sh
#
# NOTE: All pipeline stages below are commented out by default because the
#       underlying raw data contains sensitive information about deepfakes
#       and is not distributed with this repository. Uncomment the relevant
#       stages only after obtaining the raw data through appropriate channels.
#
# Author: Shalmoli Ghosh

set -e  # Exit immediately if a command exits with a non-zero status

# Change to the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo ""
echo "================================================================================"
echo "  CIVITAI BOUNTIES DATA CLEANING PIPELINE"
echo "================================================================================"
echo ""

#------------------------------------------------------------------------------
# STAGE 1: Build Bounties DataFrame
# Please uncomment the following lines to run the data cleaning pipeline.
#------------------------------------------------------------------------------
echo "STAGE 1: Building bounties dataframe — SKIPPED (see 02_run_data_cleaning.sh for details)"
echo ""
# echo "STAGE 1: Building bounties dataframe"
# echo "================================================================================"
# echo "Executing code/clean/build_bounties_df.py"
# cd code/clean
# uv run python build_bounties_df.py --with_blur True
# echo "Completed: bounties_frame_w_blur.parquet saved"
# echo ""

#------------------------------------------------------------------------------
# STAGE 2: Build Bounties Example Images DataFrame
#------------------------------------------------------------------------------
echo "STAGE 2: Building bounties example images dataframe — SKIPPED (see 02_run_data_cleaning.sh for details)"
echo ""
# echo "STAGE 2: Building bounties example images dataframe"
# echo "================================================================================"
# echo "Executing code/clean/build_bounties_example_images_df.py"
# uv run python build_bounties_example_images_df.py --with_blur True
# echo "Completed: bounties_example_images_frame_w_blur.parquet saved"
# echo ""

#------------------------------------------------------------------------------
# STAGE 3: Create Bounty Intersection and Difference Files
#------------------------------------------------------------------------------
echo "STAGE 3: Creating bounty intersection and difference files — SKIPPED (see 02_run_data_cleaning.sh for details)"
echo ""
# echo "STAGE 3: Creating bounty intersection and difference files"
# echo "================================================================================"
# echo "Executing code/clean/create_bounty_intersection_diff_files.py"
# uv run python create_bounty_intersection_diff_files.py
# echo "Completed: bounties_in_blur_and_non_blur.txt, bounties_in_w_blur_not_in_wo_blur.txt, bounties_in_wo_blur_not_in_w_blur.txt files saved"
# echo ""

#------------------------------------------------------------------------------
# STAGE 4: Build Cleaned Rating DataFrame
#------------------------------------------------------------------------------
echo "STAGE 4: Building cleaned rating dataframe — SKIPPED (see 02_run_data_cleaning.sh for details)"
echo ""
# echo "STAGE 4: Building cleaned rating dataframe"
# echo "================================================================================"
# echo "Executing code/clean/build_cleaned_rating_df.py"
# uv run python build_cleaned_rating_df.py
# echo "Completed: common_bounties_ratings{,_R_SFW,_R_X_SFW}.parquet saved"
# echo ""

echo "================================================================================"
echo "  DATA CLEANING PIPELINE COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
