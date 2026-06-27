"""
Purpose: Scrape bounties information from the CivitAI website.
    - Ref: https://civitai.com/bounties

Notes:
- When running this script, the selenium browser page must be present on your machine's screen.
    Otherwise, the 404 page will not be loaded and the script will time out.
- If the script breaks for some reason, you can simply rerun it as the script will continue
    from where it left off smoothly. It does this by checking for the existence of the bounty
    files and 404 pages in the `../../data/bounties` directory.
- Make sure to set the WITH_BLUR variable to True or False depending on whether you want
    the NSFW blur to be enabled or not. This is important as it dictates whether you can
    retrieve nsfw image URLs (False) nsfw ratings (True) from the collected HTML.

Inputs:
- None.

Outputs:
- Each bounty is saved as a .json file in the `../../data/bounties` directory.
    - Filenames are of the form: `bounty_{bounty_id}.json`
        - `bounty_id` represents the bounty page number of the URL
            - E.g. `bounty_28.json` is the 28th bounty at https://civitai.com/bounty/28
        - Contents of the .json file are:
            - url (str): URL of the bounty
            - html_text (str): HTML content of the bounty
- All 404 URLs are saved in a .txt file in the `../../data/bounties` directory.
    - CivitAI provides a 404 page if a bounty page does not exist. It is not clear
        why this happens. It is not because the bounty has been awarded or expired
        as these bounties are still available on the site.

Author:
- Matthew DeVerna
"""

import glob
import json
import os
import random
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Ensure the current working directory is the same directory as this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

NUM_PAGES_TO_CHECK = 6701
COOKIES_PATH = "./cookies/cookies.jsonl"
CIVITAI_URL = "https://civitai.com"
BOUNTIES_URL = f"{CIVITAI_URL}/bounties"

# Update CivitAI settings to enable NSFW blur or not
WITH_BLUR = True

OUTDIR = "../../data/bounties_with_blur" if WITH_BLUR else "../../data/bounties"
FILE_404 = os.path.join(OUTDIR, f"404s.txt")
os.makedirs(OUTDIR, exist_ok=True)


def load_cookies(path):
    """
    Cookies are saved in a new-line delimited JSON file. This function
    loads them.

    Parameters
    ----------
    path (str) : path to the new-line delimited JSON file

    Returns
    -------
    cookies List[dicts] : list of cookies
        - form: {'name': str, 'value': str}
    """
    with open(path, "r") as f:
        cookies = [json.loads(line) for line in f]
    return cookies


def get_successful_bounties(outdir=OUTDIR):
    """
    Gets the pagenums of successful bounties from saved fiels.

    Parameters
    ----------
    outdir (str) : path to the output directory.

    Returns
    -------
    pagenums_to_skip (set) : set of pagenums of successful bounties
    """
    successful_files = glob.glob(os.path.join(outdir, "bounty_*.json"))
    pagenums_to_skip = set()
    for file in successful_files:
        pagenum = int(file.split("_")[-1].split(".")[0])
        pagenums_to_skip.add(pagenum)
    return pagenums_to_skip


def get_404s_to_skip(outdir=OUTDIR):
    """
    Gets the pagenums of 404s from saved fiels.

    Parameters
    ----------
    None.

    Returns
    -------
    pagenums_to_skip (set) : set of pagenums of 404s.
    """
    full_404_file = os.path.join(outdir, "404s.txt")
    if not os.path.exists(full_404_file):
        return set()

    pagenums_to_skip = set()
    with open(full_404_file, "r") as f:
        for line in f:
            pagenum = int(line.split("/")[-1])
            pagenums_to_skip.add(pagenum)
    return pagenums_to_skip


def check_for_404_soup(soup):
    """
    Check whether the returned page is a 404 CivitAI page.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        Parsed HTML soup object from bs4.

    Returns
    -------
    bool : True if it's a 404 page, False otherwise.
    """
    if soup.find_all("h1")[0].text == "404":
        return True
    return False


def random_sleep():
    """
    Sleep between 1 and 3 seconds.
    """
    time.sleep(random.uniform(1, 3))


def check_for_no_entries(driver, timeout=5):
    """Waits for specific text to appear anywhere in the page body."""
    try:
        print("\t- Checking if there are no entries...")
        driver.refresh()
        WebDriverWait(driver, timeout, 1).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"), "No submissions yet"
            )
        )
        print(f"No entries!")
        return True
    except TimeoutException:
        print("\t- No entries check timed out.")
        return False


def check_for_404_page(driver, timeout=5):
    """Check if the page is a 404 page."""
    try:
        driver.refresh()
        WebDriverWait(driver, timeout, 1).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        is_404 = check_for_404_soup(soup)
        if is_404:
            print("\t- 404 page detected.")
            return None, True  # True means it's a 404
    except TimeoutException:
        print("\t- 404 check timed out.")

    print("\t- Neither content nor 404 detected, treating as 404.")
    return None, True  # Treat as 404


def fetch_page_content(driver, url, timeout=15):
    """
    Fetches the page content and checks if it is a 404 page or valid content.
    """
    print(f"Working on: {url}")
    driver.get(url)

    try:
        # Wait for the specific content class ("mantine-SimpleGrid-root")
        WebDriverWait(driver, timeout, 1).until(
            EC.presence_of_element_located((By.CLASS_NAME, "mantine-SimpleGrid-root"))
        )
        return driver.page_source, False  # False means it's not a 404

    except TimeoutException:
        print("\t- Content not found (mantine-SimpleGrid-root)")
        if check_for_no_entries(driver):
            return driver.page_source, False

        return check_for_404_page(driver)  # Check for 404 page


def main():
    """
    Main function to set up WebDriver with cookies,
    visit pages and save content of non-404 pages.
    """
    print("Getting bounty pagenums to skip...")
    bountynums_to_skip = get_successful_bounties()
    num_404s_to_skip = get_404s_to_skip()
    pagenums_to_skip = bountynums_to_skip.union(num_404s_to_skip)
    print(f"\t- Number of bounties to skip: {len(pagenums_to_skip)}")

    print("Setting up driver...")
    driver = webdriver.Firefox()

    print("Loading up cookies...")
    cookies = load_cookies(COOKIES_PATH)
    driver.get(CIVITAI_URL)
    for cookie_dict in cookies:
        driver.add_cookie(cookie_dict)

    print("Visiting pages...\n")
    for pagenum in range(1, NUM_PAGES_TO_CHECK):
        # Skip those already processed
        if pagenum in pagenums_to_skip:
            print(f"\t- Skipping pagenum {pagenum}, already processed...")
            continue

        url = f"{BOUNTIES_URL}/{pagenum}"

        html_content, is_404 = fetch_page_content(driver, url)

        if is_404:
            print("\t- Skipping 404 page and saving bounty URL to file...")
            with open(FILE_404, "a") as f:
                f.write(f"{url}\n")
            continue

        print("\t- Page found!")
        data_dict = {"url": url, "html_text": html_content}

        outpath = os.path.join(OUTDIR, f"bounty_{pagenum}.json")
        print(f"\t- Saving: {outpath}")
        with open(outpath, "w") as f:
            json.dump(data_dict, f)

    driver.quit()


if __name__ == "__main__":
    main()
    print("Script Complete!")
