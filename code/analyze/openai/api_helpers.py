"""
Helper functions for calling the OpenAI API.
"""

from openai import OpenAI

from tenacity import retry, stop_after_attempt, wait_random_exponential


class OpenAIClient:
    """Client for interacting with the OpenAI API."""

    def initialize_client(self, api_key):
        self.client = OpenAI(api_key=api_key)

    @retry(stop=stop_after_attempt(6), wait=wait_random_exponential(min=1, max=60))
    def query_model(self, model, system_prompt, user_instruction, format_class):
        """
        Query the OpenAI API with the given parameters.

        Parameters:
        - model: The model to use for the query. Must be GPT-4o or later.
        - system_prompt: The system prompt to provide to the model.
        - user_instruction: The user instruction to provide to the model.
        - format_class: The pydantic class to use for formatting the response.
        """
        if not self.client:
            raise ValueError(
                "OpenAI client not initialized. Please call `initialize_client` first."
            )

        completion = self.client.beta.chat.completions.parse(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instruction},
            ],
            response_format=format_class,
        )
        return completion

    @retry(stop=stop_after_attempt(6), wait=wait_random_exponential(min=1, max=60))
    def query_moderation(self, url):
        """
        Query the OpenAI content moderation endpoint.

        Parameters:
        - text: Text to classify
        """
        if not self.client:
            raise ValueError(
                "OpenAI client not initialized. Please call `initialize_client` first."
            )

        completion = self.client.moderations.create(
            model="omni-moderation-latest",
            input=[{"type": "image_url", "image_url": {"url": url}}],
        )
        return completion


def chunk_list(lst, n):
    """
    Splits a list 'lst' into smaller lists of size 'n'.

    Parameters:
    - lst: The list to be chunked.
    - n: The size of each chunk.

    Returns:
    - A list of smaller lists, each of size 'n'.
    """
    chunks = []
    for i in range(0, len(lst), n):
        chunks.append(lst[i : i + n])
    return chunks
