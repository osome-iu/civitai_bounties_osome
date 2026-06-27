"""
Data models for the CivitAI data objects.

Classes:
- Bounty
- Creator
"""

from bs4 import BeautifulSoup

from civitai import get_dict_val

# TODO: REMOVE EXISTING CLASSES, ADD THOSE LISTED IN THE DOCSTRING ABOVE.

# For stat requests
STAT_TYPE_OPTIONS = ["tuple", "dict"]

# Model stat fields
STAT_FIELD_OPTIONS = [
    "downloadCount",
    "favoriteCount",
    "commentCount",
    "ratingCount",
    "rating",
    "tippedAmountCount",
]
MODEL_STAT_OPTION_MAP = {"type": STAT_TYPE_OPTIONS, "field": STAT_FIELD_OPTIONS}

# Image stat fields
IMG_STAT_FIELD_OPTIONS = [
    "cryCount",
    "laughCount",
    "likeCount",
    "dislikeCount",
    "heartCount",
    "commentCount",
]
IMG_STAT_OPTION_MAP = {"type": STAT_TYPE_OPTIONS, "field": IMG_STAT_FIELD_OPTIONS}


class Model:
    """
    Class for representing a model in the CivitAI API.
    """

    def __init__(self, model_obj=None) -> None:
        if model_obj is None:
            raise ValueError("Model object cannot be None")
        self._model_obj = model_obj
        self._model_versions = get_dict_val(self._model_obj, ["modelVersions"])
        self._latest_version = None
        if self._model_versions:
            self._latest_version = self._model_versions[0]
        self._base_url = "https://civitai.com/models/"

    @property
    def model_id(self) -> int:
        return get_dict_val(self._model_obj, ["id"])

    @property
    def name(self) -> str:
        return get_dict_val(self._model_obj, ["name"])

    @property
    def description_raw(self) -> str:
        return get_dict_val(self._model_obj, ["description"])

    @property
    def description_html_parsed(self) -> str:
        if self.description_raw is None:
            return None
        soup = BeautifulSoup(self.description_raw, "html.parser")
        return soup.text

    @property
    def type(self) -> str:
        return get_dict_val(self._model_obj, ["type"])

    @property
    def poi(self) -> bool:
        return get_dict_val(self._model_obj, ["poi"])

    @property
    def is_nsfw(self) -> bool:
        return get_dict_val(self._model_obj, ["nsfw"])

    @property
    def model_url(self) -> str:
        return f"{self._base_url}{self.model_id}"

    @property
    def creator_username(self) -> str:
        return get_dict_val(self._model_obj, ["creator", "username"])

    @property
    def num_versions(self) -> int:
        if self._model_versions:
            return len(self._model_versions)
        return 0

    @property
    def date_created(self) -> bool:
        if self._latest_version is not None:
            return get_dict_val(self._latest_version, ["createdAt"])
        return None

    def get_latest_version_images(self):
        if self._latest_version is not None:
            return get_dict_val(self._latest_version, ["images"])

    def get_tags(self, type=None, delimiter=","):
        """
        Return tags based on the specified type.

        `type` options are:
        - 'list'
        - 'str'

        Parameters:
        ------------
        - type (str): How you'd like the tags returned.
        - delimiter (str): The delimiter to use if "type" is "str". Defaults to ","

        Returns:
        ------------
        - list(strings): if "type" is "list"
        - str: if "type" is "str" all tags are concatenated by the specified delimiter

        Raises:
        -----------
        - ValueError: If `type` is not a valid option.
        """
        type_options = ["list", "str"]
        if type not in type_options:
            raise ValueError(f"`type` must be one of {type_options}")

        tags_list = get_dict_val(self._model_obj, ["tags"])
        if type == "list":
            return tags_list

        return delimiter.join(tags_list)

    def get_stats(self, type=None, field=None):
        """
        Return statistics based on the specified type or field.

        `field` options are:
        - 'downloadCount'
        - 'favoriteCount'
        - 'commentCount'
        - 'ratingCount'
        -'rating'
        - 'tippedAmountCount'

        Parameters:
        ------------
        - type (str): The format of the retrieved statistics.
            - Options: ["dict", "tuple", "specific"]
        - field (str): The field for which to retrieve statistics.
            - Can only be passed on its own

        Returns:
        ------------
        - "dict" : {stat_field1:value1, stat_field2:value2}
        - "tuple": [(stat_field1,value1), (stat_field2,value2)]
        - "specific": value1 (corresponding to stat_field1)

        Raises:
        -----------
        - ValueError: If both `field` and `type` are None or if both are specified.
        - ValueError: If either `field` or `type` is not a valid option.
        """
        # Only one of `type` or `field` can be specified
        if field is None and type is None:
            raise ValueError("`field` and `type` cannot both be None")
        if field is not None and type is not None:
            raise ValueError("`field` and `type` cannot both be specified")

        # Check if `type` and `field` are valid
        for name, input_val in [("field", field), ("type", type)]:
            if input_val is not None:
                if input_val not in MODEL_STAT_OPTION_MAP[name]:
                    raise ValueError(
                        f"`{name}` must be one of {MODEL_STAT_OPTION_MAP[name]}"
                    )

        stat_dict = get_dict_val(self._model_obj, ["stats"])
        if type == "dict":
            return stat_dict
        elif type == "tuple":
            return [(k, v) for k, v in stat_dict.items()]
        else:
            return get_dict_val(stat_dict, [field])

    def __repr__(self) -> str:
        return f"Model: {self.name}\nURL: {self.model_url}"

    def __str__(self) -> str:
        return f"Model: {self.name}\nURL: {self.model_url}"


class ModelImage:
    """
    Class for representing an image extracted from a Model.
    """

    def __init__(self, image_obj=None) -> None:
        if image_obj is None:
            raise ValueError("Model object cannot be None")
        self._image_obj = image_obj

    @property
    def image_id(self) -> int:
        return get_dict_val(self._image_obj, ["id"])

    @property
    def image_url(self) -> str:
        return get_dict_val(self._image_obj, ["url"])

    @property
    def nsfw_level(self) -> str:
        return get_dict_val(self._image_obj, ["nsfw"])

    @property
    def media_type(self) -> str:
        return get_dict_val(self._image_obj, ["type"])

    @property
    def prompt(self) -> str:
        return get_dict_val(self._image_obj, ["meta", "prompt"])

    def __repr__(self) -> str:
        return f"ModelImage: {self.image_url}"

    def __str__(self) -> str:
        return f"ModelImage: {self.image_url}"


class Image:
    """
    Class for representing a CivitaAI image object.
    """

    def __init__(self, image_obj=None) -> None:
        if image_obj is None:
            raise ValueError("Model object cannot be None")
        self._image_obj = image_obj

    @property
    def image_id(self) -> int:
        return get_dict_val(self._image_obj, ["id"])

    @property
    def post_id(self) -> int:
        return get_dict_val(self._image_obj, ["postId"])

    @property
    def image_url(self) -> str:
        return get_dict_val(self._image_obj, ["url"])

    @property
    def is_nsfw(self) -> str:
        return get_dict_val(self._image_obj, ["nsfw"])

    @property
    def nsfw_level(self) -> str:
        return get_dict_val(self._image_obj, ["nsfwLevel"])

    @property
    def created_at(self) -> str:
        return get_dict_val(self._image_obj, ["createdAt"])

    @property
    def prompt(self) -> str:
        return get_dict_val(self._image_obj, ["meta", "Model"])

    @property
    def prompt(self) -> str:
        return get_dict_val(self._image_obj, ["meta", "prompt"])

    @property
    def negative_prompt(self) -> str:
        return get_dict_val(self._image_obj, ["meta", "negativePrompt"])

    def get_resources(self) -> str:
        return get_dict_val(self._image_obj, ["meta", "resources"])

    def get_stats(self, type=None, field=None):
        """
        Return statistics based on the specified type or field.

        `field` options are:
        - "cryCount"
        - "laughCount"
        - "likeCount"
        - "dislikeCount"
        - "heartCount"
        - "commentCount"

        Parameters:
        ------------
        - type (str): The format of the retrieved statistics.
            - Options: ["dict", "tuple", "specific"]
        - field (str): The field for which to retrieve statistics.
            - Can only be passed on its own

        Returns:
        ------------
        - "dict" : {stat_field1:value1, stat_field2:value2}
        - "tuple": [(stat_field1,value1), (stat_field2,value2)]
        - "specific": value1 (corresponding to stat_field1)

        Raises:
        -----------
        - ValueError: If both `field` and `type` are None or if both are specified.
        - ValueError: If either `field` or `type` is not a valid option.
        """
        # Only one of `type` or `field` can be specified
        if field is None and type is None:
            raise ValueError("`field` and `type` cannot both be None")
        if field is not None and type is not None:
            raise ValueError("`field` and `type` cannot both be specified")

        # Check if `type` and `field` are valid
        for name, input_val in [("field", field), ("type", type)]:
            if input_val is not None:
                if input_val not in IMG_STAT_OPTION_MAP[name]:
                    raise ValueError(
                        f"`{name}` must be one of {IMG_STAT_OPTION_MAP[name]}"
                    )

        stat_dict = get_dict_val(self._image_obj, ["stats"])
        if type == "dict":
            return stat_dict
        elif type == "tuple":
            return [(k, v) for k, v in stat_dict.items()]
        else:
            return get_dict_val(stat_dict, [field])

    def __repr__(self) -> str:
        return f"Image: {self.image_url}"

    def __str__(self) -> str:
        return f"Image: {self.image_url}"
