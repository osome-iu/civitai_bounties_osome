"""
Purpose:
- Process and clean the OpenAI content moderation responses about the bounties.

Inputs:
- Data is read via constants defined below.

Outputs:
- `content_moderation_frame.parquet`: cleaned dataframe with the following columns:
    - bounty_number (int): Unique identifier for the bounty.
    - flagged (str): Set to true if the model classifies the content as potentially harmful, false otherwise.
    - harassment_flagged (str): Content that expresses, incites, or promotes harassing language towards any target. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - harassment_threatening_flagged (str): Harassment content that also includes violence or serious harm towards any target. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - hate_flagged (str): Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g. chess players) is harassment. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - hate_threatening_flagged (str): Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - illicit_flagged (str): Content that gives advice or instruction on how to commit illicit acts. A phrase like "how to shoplift" would fit this category. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - illicit_violent_flagged (str): The same types of content flagged by the illicit category, but also includes references to violence or procuring a weapon. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - self_harm_flagged (str): Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - self_harm_instructions_flagged (str): Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - self_harm_intent_flagged (str): Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - sexual_flagged (str): Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness). Set to true if the model classifies the content as potentially harmful, false otherwise.
    - sexual_minors_flagged (str): Sexual content that includes an individual who is under 18 years old. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - violence_flagged (str): Content that depicts death, violence, or physical injury. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - violence_graphic_flagged (str): Content that depicts death, violence, or physical injury in graphic detail. Set to true if the model classifies the content as potentially harmful, false otherwise.
    - harassment_score (float): Content that expresses, incites, or promotes harassing language towards any target. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - harassment_threatening_score (float): Harassment content that also includes violence or serious harm towards any target. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - hate_score (float): Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g. chess players) is harassment. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - hate_threatening_score (float): Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - illicit_score (float): Content that gives advice or instruction on how to commit illicit acts. A phrase like "how to shoplift" would fit this category. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - illicit_violent_score (float): The same types of content flagged by the illicit category, but also includes references to violence or procuring a weapon.The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - self_harm_score (float): Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - self_harm_instructions_score (float): Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - self_harm_intent_score (float): Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - sexual_score (float): Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness). The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - sexual_minors_score (float): Sexual content that includes an individual who is under 18 years old. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - violence_score (float): Content that depicts death, violence, or physical injury. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - violence_graphic_score (float): Content that depicts death, violence, or physical injury in graphic detail. The value is between 0 and 1, where higher values denote higher confidence  that the input violates the OpenAI's policy for the category.
    - id (str): Unique identifier given by the OpenAI model.
    - model (str): LLM model used for the task.

References:
    - https://platform.openai.com/docs/guides/moderation/overview

Author:
- Matthew DeVerna & Shalmoli Ghosh
"""

import json
import os

import pandas as pd

# Ensure we are in the directory where the script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

OPENAI_DATA_DIR = "../../data/openai_responses/content_moderation/"
OPENAI_CONTENT_MODERATION_FILE = os.path.join(
    OPENAI_DATA_DIR, "raw", "content_moderation_responses.jsonl"
)
OPENAI_CLEAN_DIR = os.path.join(OPENAI_DATA_DIR, "clean")
os.makedirs(OPENAI_CLEAN_DIR, exist_ok=True)
CLEAN_CONTENT_MODERATION_FNAME = "content_moderation_frame.parquet"


def flatten_response(response: dict) -> dict:
    """
    Flattens a nested response into a clear and concise dictionary.
    Meant to work with the OpenAI content moderation responses.

    Parameters:
    ----------
    response (dict): The nested OpenAI content moderation response to be flattened.

    Returns:
    ----------
    dict: A flattened version of the input response with only what we need.
    """
    flattened = {}

    # Extract details from results
    results = response.get("results", [{}])[0]

    # Metadata we want in early rows
    flattened["bounty_number"] = response.get("bounty_number")
    flattened["image_url"] = response.get("image_url")
    flattened["flagged"] = results.get("flagged")

    # Category flagged?
    categories = results.get("categories", {})
    for category, is_flagged in categories.items():
        clean_catergory = category.replace("-", "_").replace("/", "_").lower()
        flattened[f"{clean_catergory}_flagged"] = is_flagged

    # Category scores
    scores = results.get("category_scores", {})
    for category, score in scores.items():
        clean_catergory = category.replace("-", "_").replace("/", "_").lower()
        flattened[f"{clean_catergory}_score"] = score

    # Other OpenAi-specific metadata
    flattened["id"] = response.get("id")
    flattened["model"] = response.get("model")

    return flattened


if __name__ == "__main__":
    print("Loading OpenAI content moderation responses...")
    with open(OPENAI_CONTENT_MODERATION_FILE, "r") as f:
        records = [json.loads(line) for line in f]

    print("Flattening responses and extracting relevant info...")
    flattened_records = [flatten_response(response) for response in records]

    print("Creating and saving the dataframe...")
    df = pd.DataFrame.from_records(flattened_records)
    df.to_parquet(
        os.path.join(OPENAI_CLEAN_DIR, CLEAN_CONTENT_MODERATION_FNAME), index=False
    )
