"""
OpenAI response structures should be saved here.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


ThemeLiteral = Literal[
    "human_attributes",
    "human_deepfake",
    "nsfw",
    "fictional_characters",
    "scene_objects_clothing",
    "style_and_culture",
    "open_request",
    "miscellaneous",
]


class ThemeWithRationale(BaseModel):
    theme: ThemeLiteral
    rationale: str


class BountyClassifierOutput(BaseModel):

    best_fit_theme: ThemeWithRationale
    relevant_themes: List[ThemeWithRationale]


class PersonEntityStructure(BaseModel):
    deepfake: bool = Field(
        ...,
        description="True if the bounty requests a deepfake of a real person, False otherwise",
    )
    name: Optional[str] = Field(
        None, description="Full name of the person, or None if not identified"
    )
    occupation: Optional[str] = Field(
        None, description="Person's occupation or role, or None"
    )
    real_human: bool = Field(
        ..., description="True if the person is a real human, False otherwise"
    )

    rationale: str = Field(
        ...,
        description="Brief explanation (≤50 words) of the classification decision",
    )