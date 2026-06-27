"""
Purpose: Collect all the creators on civitai.com using the REST API.
- API Ref: https://github.com/civitai/civitai/wiki/REST-API-Reference

Description:
This script fetches creator data from the civitai.com API, handling HTTP requests with
exponential backoff in case of failures. It paginates through the API responses to
gather all creators and then saves all creator data at once to a parquet file.

Usage:
    python collect_creators.py

Output:
    A pandas dataframe (.parquet) of all the creators on civitai.com.

Author: Matthew DeVerna
"""

import datetime
import os
import requests

import pandas as pd

from tenacity import retry, wait_exponential, stop_after_attempt


BASE_URL = "https://civitai.com/api/v1/creators"
OUTPUT_DIR = "../../data/raw_civitai"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@retry(wait=wait_exponential(multiplier=1, min=1, max=60), stop=stop_after_attempt(5))
def fetch_creators(url):
    response = requests.get(url, headers={"Content-Type": "application/json"})
    response.raise_for_status()  # Raises an error for bad responses
    return response.json()


def get_all_creators(base_url, limit=200, page=1):
    """
    Retrieves all creators from a given base URL for civitai.

    Handles bad HTTP responses and retries if necessary with exponential backoff.

    Parameters
    -----------
    - base_url (str): The base URL to retrieve creators from.
    - limit (int, optional): The maximum number of creators to retrieve per page.
        - Default (for function): 200
        - Default (for REST API): 20
        - Possible range: [0, 200]
    - page (int, optional): The page number to start retrieving creators.

    Returns
    ---------
    creators (list): A list of all creators retrieved from the base URL.
        - Creator items look like:
        {
            'username': 'JustMaier',
            'modelCount': 4,
            'link': 'https://civitai.com/api/v1/models?username=JustMaier',
            'image': 'https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6046154e-6d32-4500-8772-602edb4a4600/width=96/JustMaier.jpeg'
        }
    """
    creators = []
    total_pages = 1  # Initial assumption
    first_call = True

    while page <= total_pages:
        msg = (
            f"Working on page #{page}..."
            if first_call
            else f"Working on page #{page}/{total_pages}..."
        )
        print(msg)

        url = f"{base_url}?limit={limit}&page={page}"
        response_data = fetch_creators(url)

        # Check if items exist in the response
        if "items" in response_data and response_data["items"]:
            creators.extend(response_data["items"])

            # Default to 1 if not present
            total_pages = response_data["metadata"].get("totalPages", 1)
            page += 1
        else:
            print("No more creators found or unexpected response structure.")
            break

        first_call = False

    return creators


if __name__ == "__main__":
    all_creators = get_all_creators(BASE_URL)
    creators_df = pd.DataFrame.from_records(all_creators)

    # If creators have NaN modelCount, fill with 0
    creators_df.modelCount = creators_df.modelCount.fillna(0)

    # Create date string for fname
    dt = datetime.datetime.today()
    date_str = dt.strftime("%Y_%m_%d")

    # Save to parquet
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    creators_df.to_parquet(
        os.path.join(OUTPUT_DIR, f"{date_str}__creators_raw.parquet")
    )
