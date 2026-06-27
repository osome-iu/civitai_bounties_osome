#!/bin/bash

# Purpose:
#   Run the data collection pipeline for the CivitAI bounties project.
#   Scrapes bounty HTML from the CivitAI website using Selenium.
#
# Inputs:
#   - None. URLs are constructed programmatically up to NUM_PAGES_TO_CHECK.
#   - code/collect/cookies/cookies.jsonl: CivitAI session cookies for authentication.
#
# Outputs:
#   - data/bounties_with_blur/bounty_<id>.json: bounty HTML with NSFW blur enabled
#   - data/bounties_with_blur/404s.txt: bounty URLs that returned 404 pages (blur run)
#   (Set WITH_BLUR=False in collect_bounties.py to collect to data/bounties/ instead)
#
# Prerequisites:
#   - Selenium and BeautifulSoup must be installed
#   - A browser window controlled by Selenium MUST be visible on screen during the run;
#     otherwise 404 pages will not load and the script will time out
#   - Valid CivitAI session cookies must be present at code/collect/cookies/cookies.jsonl
#   - If the script is interrupted, it can be safely rerun — it will resume from where
#     it left off by checking for already-collected bounty files in the output directory
#
# How to call:
#   bash run_data_collection.sh
#
# Author: Matthew DeVerna

set -e  # Exit immediately if a command exits with a non-zero status

# Change to the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Failed to change directory to $SCRIPT_DIR"; exit 1; }

echo ""
echo "================================================================================"
echo "  CIVITAI BOUNTIES DATA COLLECTION PIPELINE"
echo "================================================================================"
echo ""

#------------------------------------------------------------------------------
# STAGE 1: Scrape CivitAI Bounties
#------------------------------------------------------------------------------
# NOTE: The Selenium browser window MUST be visible on your screen while this runs.
# The script checks up to bounty page 6701 and skips already-collected bounties,
# so it is safe to rerun after an interruption.
# To collect non-blurred data, set WITH_BLUR = False in collect_bounties.py before running.
# If you want to collect the data from scratch, please uncomment the following lines.
echo "STAGE 1: Scraping CivitAI bounties — SKIPPED (see 01_run_data_collection.sh for details)"
echo ""

# echo "STAGE 1: Scraping CivitAI bounties"
# echo "================================================================================"
# echo "  NOTE: Ensure the Selenium browser window is visible on screen before proceeding."
# echo "Executing code/collect/collect_bounties.py"
# cd code/collect
# uv run python collect_bounties.py
# cd "$SCRIPT_DIR"
# echo "Completed: bounty JSON files saved to data/bounties_with_blur/"
# echo ""

echo "================================================================================"
echo "  DATA COLLECTION PIPELINE COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo ""
