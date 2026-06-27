"""
Purpose:
- Perform a robustness analysis to validate the accuracy and reliability of NSFW/SFW content ratings assigned by the CivitAI platform.

Input:
- Data is read via constants defined below.

Outputs:
- Comprehensive performance analysis report (one per rating scheme):
  results/content_moderation_robustness_analysis_<scheme>.txt

Author:
- Shalmoli Ghosh
"""

import os
import glob
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, cohen_kappa_score, matthews_corrcoef

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
DATA_DIR = "../../../data/clean"
BOUNTIES_IN_BLUR_AND_NON_BLUR_FILES = glob.glob(
    os.path.join(DATA_DIR, "common_bounties_ratings*_published.parquet")
)

OPENAI_DATA_DIR = "../../../data/openai_responses/content_moderation/"
CLEAN_CONTENT_MODERATION_FNAME = "clean/content_moderation_frame_published.parquet"
BAD_URLS_PATH = os.path.join(
    OPENAI_DATA_DIR, "raw", "content_moderation_bad_urls.jsonl"
)

RESULT_DIR = "../../../results"

# Create results directory if it doesn't exist
os.makedirs(RESULT_DIR, exist_ok=True)


def write_to_file(content, mode="a"):
    """Write content to the output file"""
    with open(OUTPUT_FILE, mode, encoding="utf-8") as f:
        f.write(content + "\n")


def generate_detailed_analysis_report(y_true_binary, y_pred_binary):
    """
    Generate comprehensive analysis report
    """

    total_samples = len(y_true_binary)
    nsfw_actual = np.sum(y_true_binary)
    sfw_actual = total_samples - nsfw_actual

    # Write detailed analysis header
    write_to_file("=" * 80)
    write_to_file("NSFW CONTENT CLASSIFICATION PERFORMANCE ANALYSIS")
    write_to_file("=" * 80)

    # Dataset Overview
    write_to_file("DATASET OVERVIEW")
    write_to_file("=" * 80)
    write_to_file(f"Total samples analyzed: {total_samples:,}")
    write_to_file(
        f"Actual NSFW content: {nsfw_actual:,} ({nsfw_actual / total_samples * 100:.1f}%)"
    )
    write_to_file(
        f"Actual SFW content: {sfw_actual:,} ({sfw_actual / total_samples * 100:.1f}%)"
    )

    # Classification Report
    write_to_file("\nCLASSIFICATION REPORT")
    write_to_file("=" * 80)
    class_report = classification_report(
        y_true_binary, y_pred_binary, target_names=["SFW", "NSFW"]
    )
    write_to_file(class_report)
    write_to_file("=" * 80)

    # Cohen's Kappa
    kappa = cohen_kappa_score(y_true_binary, y_pred_binary)
    write_to_file(f"Cohen's Kappa: {kappa:.4f}")

    # Matthews Correlation Coefficient
    mcc = matthews_corrcoef(y_true_binary, y_pred_binary)
    write_to_file(f"MCC: {mcc:.4f}")


if __name__ == "__main__":
    # Load the data
    df = pd.read_parquet(os.path.join(OPENAI_DATA_DIR, CLEAN_CONTENT_MODERATION_FNAME))

    for infile in BOUNTIES_IN_BLUR_AND_NON_BLUR_FILES:
        # Derive output file name from input file
        base = os.path.splitext(os.path.basename(infile))[0]
        OUTPUT_FILE = os.path.join(
            RESULT_DIR, f"content_moderation_robustness_analysis_{base}.txt"
        )

        # Reset the output file at the start of each scheme iteration so re-runs
        # don't accumulate duplicate reports.
        open(OUTPUT_FILE, "w").close()

        # Load bounty ratings file
        common_bounties_df = pd.read_parquet(infile)

        final_df = (
            df.groupby("bounty_number")[
                [
                    "flagged",
                    "sexual_flagged",
                    "sexual_minors_flagged",
                    "violence_flagged",
                    "violence_graphic_flagged",
                ]
            ]
            .any()  # returns True if any row in the group has True
            .reset_index()
            .rename(
                columns={
                    "flagged": "flagged_",
                    "sexual_flagged": "sexually_explicit",
                    "sexual_minors_flagged": "sexual_minors_explicit",
                    "violence_flagged": "violence_",
                    "violence_graphic_flagged": "violence_graphic_",
                }
            )
        )

        merged_common_df = pd.merge(
            common_bounties_df, final_df, on="bounty_number", how="inner"
        )
        merged_common_df["rating_cm"] = merged_common_df["flagged_"].apply(
            lambda x: "NSFW" if x else "SFW"
        )

        y_true_binary = merged_common_df["rating"].map({"NSFW": 1, "SFW": 0})
        y_pred_binary = merged_common_df["rating_cm"].map({"NSFW": 1, "SFW": 0})

        # Generate detailed analysis report
        generate_detailed_analysis_report(y_true_binary, y_pred_binary)
