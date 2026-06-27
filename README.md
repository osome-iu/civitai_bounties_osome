# civitai-bounties

Explore the CivitAI.com bounties marketplace — data collection, cleaning, OpenAI-based analysis, and figure generation.

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Astral's fast Python package manager)
- Google Chrome (required for Selenium-based data collection)
- An OpenAI API key (required for scripts 03 and 04)
- Valid CivitAI session cookies saved to `code/collect/cookies/cookies.jsonl`

---

## Environment Setup

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env   # or restart your shell
```

### 2. Sync the environment

From the project root:

```bash
uv sync
```

This reads `pyproject.toml` + `uv.lock`, creates `.venv`, and installs all dependencies (including the local `civitai-bounties-lib` package under `code/package/`).

The pipeline scripts use `uv run`, so no manual activation is required.

---

## Environment Variables

Export your OpenAI API key before running scripts 03 or 04:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

---

## Pipeline Scripts

Run each script from the project root in order. Each script depends on the outputs of the previous one.

### 01 — Data Collection

Scrapes bounty HTML from CivitAI using Selenium.

```bash
bash 01_run_data_collection.sh
```

**Prerequisites:**
- A Chrome browser window controlled by Selenium must be visible on screen during the run.
- Valid CivitAI session cookies must be present at `code/collect/cookies/cookies.jsonl`.

**Outputs:** `data/bounties_with_blur/bounty_<id>.json`

---

### 02 — Data Cleaning

Parses raw HTML and builds structured Parquet dataframes.

```bash
bash 02_run_data_cleaning.sh
```

**Outputs:**
- `bounties_frame_w_blur_published.parquet`
- `bounties_example_images_frame_w_blur_published.parquet`
- `bounties_in_blur_and_non_blur.txt`
- `common_bounties_ratings.parquet`

---

### 03 — General Theme Pipeline

Samples bounties, calls the OpenAI API for theme extraction, and runs reliability analysis (Krippendorff's alpha).

```bash
bash 03_run_general_theme_pipeline.sh
```

> **Note:** Stage 2 calls the OpenAI API and will incur costs. Stage 3 (human annotation) is a manual step — see the script for details.

**Outputs:**
- `data/intermediate/YYYY-MM-DD_bounties_sample.csv`
- `data/openai_responses/bounty_themes/raw/general_theme_responses__gpt-4.1.jsonl`
- `results/krippendorff_alpha_results_with_f1.txt`

---

### 04 — Full OpenAI Analysis

Runs three sub-pipelines: general theme extraction (full dataset), content moderation, and NSFW deepfake detection.

```bash
bash 04_run_openai_analysis.sh
```

> **Warning:** All three stages call the OpenAI API and will incur costs.

**Outputs:**
- `data/clean/general_theme_frame_published.parquet`
- `data/clean/content_moderation_frame_published.parquet`
- `data/openai_responses/deepfakes/clean/deepfake_bounties_from_nsfw.csv`

---

### 05 — Analysis & Figure Generation

Runs robustness analysis and generates all paper figures.

```bash
bash 05_run_analysis_figures.sh
```

**Outputs** (saved to `results/figures/`):
- `bounty_ts_count_props.pdf/.png` — Fig. 2: bounty type, theme, and temporal trends
- `deepfake_analysis_revised.pdf` — Fig. 3: deepfake analysis
- `user_concentration_analysis.pdf/.png` — Fig. 4: user concentration analysis
- `deepfake_nsfw_sfw_stacked.pdf` — Fig. 5: deepfake moderation breakdown
- `results/content_moderation_robustness_analysis_<scheme>.txt` — one file per rating scheme (default, R-as-SFW, R-and-X-as-SFW)

---

## Project Structure

```
civitai-bounties/
├── code/
│   ├── analyze/          # Analysis scripts (figures, OpenAI calls, reliability, sampling)
│   ├── clean/            # Data cleaning scripts
│   ├── collect/          # Data collection scripts (Selenium scraper)
│   └── package/          # Local reusable Python package
├── data/
│   ├── clean/            # Cleaned data ready for analysis
│   ├── intermediate/     # Sampled data
│   ├── manual_coding/    # Human annotation files
│   └── openai_responses/ # cleaned OpenAI API responses
├── pyproject.toml        # Project metadata and dependencies
├── uv.lock               # Locked dependency versions
└── .venv/                # Virtual environment (not committed)
```

This repository is to replicate the research published in the following paper:

```
@inproceedings{10.1145/3805689.3812321,
author = {Ghosh, Shalmoli and DeVerna, Matthew R. and Menczer, Filippo},
title = {A Marketplace for AI-Generated Adult Content and Deepfakes},
year = {2026},
isbn = {9798400725968},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3805689.3812321},
doi = {10.1145/3805689.3812321},
booktitle = {Proceedings of the 2026 ACM Conference on Fairness, Accountability, and Transparency},
pages = {3466–3485},
numpages = {20},
keywords = {Civitai, Marketplace, Generative AI, Safety, Deepfakes, Adult content, Ethics},
location = {
},
series = {FAccT '26}
}
```