"""
Purpose:
- Calculate the Krippendorff's alpha score between the best fit theme as labels by GPT 4.1, GPT 4o, and the human annotator.
- Calculate macro F1 and per-class F1 scores for both GPT models vs human annotations.

Inputs:
- Data is read via constants defined below.

Output:
- "krippendorff_alpha_results.txt" file containing:
    - krippendorff_alpha_score (float) value for each of the two GPT models.
    - macro F1 scores for each GPT model vs human
    - per-class F1 scores and sample counts

Author:
- Shalmoli Ghosh & Matthew DeVerna
"""

import os
import pandas as pd
import numpy as np
import krippendorff
from sklearn.metrics import f1_score, classification_report
from collections import Counter

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constants
OPENAI_DATA_DIR = "../../../data/openai_responses/bounty_themes/"
OPENAI_CLEAN_DIR = os.path.join(OPENAI_DATA_DIR, "clean")
MANUAL_CODING_DIR = "../../../data/manual_coding"

RESULT_DIR = "../../../results"
OUTPUT_PATH = os.path.join(RESULT_DIR, "krippendorff_alpha_results_with_f1.txt")

# Create results directory if it doesn't exist
os.makedirs(RESULT_DIR, exist_ok=True)


# Function to calculate Krippendorff's Alpha for two columns
def calculate_krippendorff_two_cols(df, col1, col2):
    """
    Calculates Krippendorff's Alpha for two columns in a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing the two columns.
        col1 (str): Name of the first column.
        col2 (str): Name of the second column.

    Returns:
        float: Krippendorff's Alpha score.
    """
    # Drop rows where either column has NaN values
    df_clean = df.dropna(subset=[col1, col2]).copy()

    # Get the unique labels from both columns
    all_labels = pd.concat([df_clean[col1], df_clean[col2]]).astype(str).unique()
    label_to_int = {label: i for i, label in enumerate(all_labels)}

    # Create a list of lists for krippendorff library
    # Each item is a rating unit (e.g., a bounty), each rating unit has ratings from different coders
    ratings = []
    for _, row in df_clean.iterrows():
        ratings.append([label_to_int[str(row[col1])], label_to_int[str(row[col2])]])

    # Transpose the ratings so each row is a coder and each column is a unit
    # krippendorff library expects shape (coders, units)
    ratings_transposed = np.array(ratings).T

    # Calculate Krippendorff's Alpha
    alpha_score = krippendorff.alpha(ratings_transposed, level_of_measurement="nominal")

    return alpha_score


def calculate_f1_metrics(df, true_col, pred_col):
    """
    Calculate macro F1 and per-class F1 scores.

    Args:
        df (pd.DataFrame): DataFrame containing both columns.
        true_col (str): Name of the ground truth column (human annotations).
        pred_col (str): Name of the predictions column (GPT annotations).

    Returns:
        dict: Dictionary containing macro_f1, per_class_f1, and class_counts.
    """
    # Drop rows where either column has NaN values
    df_clean = df.dropna(subset=[true_col, pred_col]).copy()

    y_true = df_clean[true_col].astype(str)
    y_pred = df_clean[pred_col].astype(str)

    # Calculate macro F1
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    # Get detailed classification report
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    # Extract per-class F1 scores (excluding 'accuracy', 'macro avg', 'weighted avg')
    per_class_f1 = {}
    for label, metrics in report.items():
        if label not in ["accuracy", "macro avg", "weighted avg"]:
            per_class_f1[label] = {
                "f1": metrics["f1-score"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "support": int(metrics["support"]),
            }

    # Get class counts from ground truth
    class_counts = Counter(y_true)

    weighted_f1 = report["weighted avg"]["f1-score"]

    return {
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class_f1": per_class_f1,
        "class_counts": class_counts,
    }


if __name__ == "__main__":
    df = pd.read_parquet(
        os.path.join(OPENAI_CLEAN_DIR, "general_theme_clean_published.parquet")
    )
    df_gpt_41 = df[df["model"] == "gpt-4.1-2025-04-14"]
    df_gpt_4o = df[df["model"] == "gpt-4o-2024-08-06"]

    # As the dataframes were exploded to store the results for the multiple themes - every bounty has multiple entries while we need only one.
    df_gpt_41 = df_gpt_41[["bounty_number", "best_fit_theme"]].drop_duplicates()
    df_gpt_4o = df_gpt_4o[["bounty_number", "best_fit_theme"]].drop_duplicates()

    df_shalmoli = pd.read_csv(
        os.path.join(
            MANUAL_CODING_DIR, "bounties_sample_clean_shalmoli_latest_round_published.csv"
        )
    )
    df_shalmoli_best = df_shalmoli[["bounty_number", "main_theme"]]

    merged_df_41 = pd.merge(
        df_gpt_41, df_shalmoli_best, on="bounty_number", how="right"
    )
    merged_df_4o = pd.merge(
        df_gpt_4o, df_shalmoli_best, on="bounty_number", how="right"
    )

    # Calculate Krippendorff's Alpha for both models
    krippendorff_alpha_score_41 = calculate_krippendorff_two_cols(
        merged_df_41, "main_theme", "best_fit_theme"
    )
    krippendorff_alpha_score_4o = calculate_krippendorff_two_cols(
        merged_df_4o, "main_theme", "best_fit_theme"
    )

    # Calculate F1 metrics for both models
    f1_metrics_41 = calculate_f1_metrics(merged_df_41, "main_theme", "best_fit_theme")
    f1_metrics_4o = calculate_f1_metrics(merged_df_4o, "main_theme", "best_fit_theme")

    # Write results to file
    with open(OUTPUT_PATH, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("INTER-RATER RELIABILITY AND CLASSIFICATION PERFORMANCE METRICS\n")
        f.write("=" * 80 + "\n\n")

        # Krippendorff's Alpha
        f.write("%%%%%%%%% Krippendorff's Alpha Scores %%%%%%%%%\n\n")
        f.write(f"GPT-4.1 vs Human: {krippendorff_alpha_score_41:.4f}\n")
        f.write(f"GPT-4o vs Human:  {krippendorff_alpha_score_4o:.4f}\n\n")

        # Macro F1 Scores
        f.write("=" * 80 + "\n")
        f.write("%%%%%%%%% Macro F1 Scores %%%%%%%%%\n\n")
        f.write(f"GPT-4.1 vs Human: {f1_metrics_41['macro_f1']:.4f}\n")
        f.write(f"GPT-4o vs Human:  {f1_metrics_4o['macro_f1']:.4f}\n\n")

        f.write("=" * 80 + "\n")
        f.write("%%%%%%%%% Weighted F1 Scores %%%%%%%%%\n\n")
        f.write(f"GPT-4.1 vs Human: {f1_metrics_41['weighted_f1']:.4f}\n")
        f.write(f"GPT-4o vs Human:  {f1_metrics_4o['weighted_f1']:.4f}\n\n")

        # GPT-4.1 Per-Class Results
        f.write("=" * 80 + "\n")
        f.write("%%%%%%%%% GPT-4.1 Per-Class Performance %%%%%%%%%\n\n")
        f.write(f"{'Class':<40} | {'F1':>6} | {'Prec':>6} | {'Rec':>6} | {'N':>5}\n")
        f.write("-" * 80 + "\n")

        # Sort by F1 score descending
        sorted_classes_41 = sorted(
            f1_metrics_41["per_class_f1"].items(),
            key=lambda x: x[1]["f1"],
            reverse=True,
        )

        for class_name, metrics in sorted_classes_41:
            f.write(
                f"{class_name:<40} | "
                f"{metrics['f1']:>6.3f} | "
                f"{metrics['precision']:>6.3f} | "
                f"{metrics['recall']:>6.3f} | "
                f"{metrics['support']:>5}\n"
            )

        # GPT-4o Per-Class Results
        f.write("\n" + "=" * 80 + "\n")
        f.write("%%%%%%%%% GPT-4o Per-Class Performance %%%%%%%%%\n\n")
        f.write(f"{'Class':<40} | {'F1':>6} | {'Prec':>6} | {'Rec':>6} | {'N':>5}\n")
        f.write("-" * 80 + "\n")

        # Sort by F1 score descending
        sorted_classes_4o = sorted(
            f1_metrics_4o["per_class_f1"].items(),
            key=lambda x: x[1]["f1"],
            reverse=True,
        )

        for class_name, metrics in sorted_classes_4o:
            f.write(
                f"{class_name:<40} | "
                f"{metrics['f1']:>6.3f} | "
                f"{metrics['precision']:>6.3f} | "
                f"{metrics['recall']:>6.3f} | "
                f"{metrics['support']:>5}\n"
            )

        # Class Distribution (from human annotations)
        f.write("\n" + "=" * 80 + "\n")
        f.write("%%%%%%%%% Class Distribution (Human Annotations) %%%%%%%%%\n\n")
        f.write(f"{'Class':<40} | {'Count':>6}\n")
        f.write("-" * 80 + "\n")

        total_samples = sum(f1_metrics_41["class_counts"].values())
        sorted_counts = sorted(
            f1_metrics_41["class_counts"].items(), key=lambda x: x[1], reverse=True
        )

        for class_name, count in sorted_counts:
            percentage = (count / total_samples) * 100
            f.write(f"{class_name:<40} | {count:>6} ({percentage:>5.1f}%)\n")

        f.write(f"\n{'TOTAL':<40} | {total_samples:>6} (100.0%)\n")

        f.write("\n" + "=" * 80 + "\n")

    print(f"✓ Results saved to: {OUTPUT_PATH}")
    print("\nSummary:")
    print(f"  Krippendorff's Alpha (GPT-4.1): {krippendorff_alpha_score_41:.4f}")
    print(f"  Krippendorff's Alpha (GPT-4o):  {krippendorff_alpha_score_4o:.4f}")
    print(f"  Macro F1    (GPT-4.1): {f1_metrics_41['macro_f1']:.4f}")
    print(f"  Macro F1    (GPT-4o):  {f1_metrics_4o['macro_f1']:.4f}")
    print(f"  Weighted F1 (GPT-4.1): {f1_metrics_41['weighted_f1']:.4f}")
    print(f"  Weighted F1 (GPT-4o):  {f1_metrics_4o['weighted_f1']:.4f}")
    print(f"  Total samples: {total_samples}")
    print(f"  Number of classes: {len(f1_metrics_41['class_counts'])}")
