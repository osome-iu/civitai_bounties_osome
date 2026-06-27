"""
This script provides some convinient functions for the project.
"""
import inspect


############################################################
############################################################
# Utilities
############################################################
def get_dict_val(dictionary: dict, key_list: list = []):
    """
    Return `dictionary` value at the end of the key path provided
    in `key_list`.
    Indicate what value to return based on the key_list provided.
    For example, from left to right, each string in the key_list
    indicates another nested level further down in the dictionary.
    If no value is present, a `None` is returned.
    Parameters:
    ----------
    - dictionary (dict) : the dictionary object to traverse
    - key_list (list) : list of strings indicating what dict_obj
        item to retrieve
    Returns:
    ----------
    - key value (if present) or None (if not present)
    Raises:
    ----------
    - TypeError
    Examples:
    ---------
    # Create dictionary
    dictionary = {
        "a" : 1,
        "b" : {
            "c" : 2,
            "d" : 5
        },
        "e" : {
            "f" : 4,
            "g" : 3
        },
        "h" : 3
    }
    ### 1. Finding an existing value
    # Create key_list
    key_list = ['b', 'c']
    # Execute function
    get_dict_val(dictionary, key_list)
    # Returns
    2
    ~~~
    ### 2. When input key_path doesn't exist
    # Create key_list
    key_list = ['b', 'k']
    # Execute function
    value = get_dict_val(dictionary, key_list)
    # Returns NoneType because the provided path doesn't exist
    type(value)
    NoneType
    """
    if not isinstance(dictionary, dict):
        raise TypeError("`dictionary` must be of type `dict`")

    if not isinstance(key_list, list):
        raise TypeError("`key_list` must be of type `list`")

    retval = dictionary
    for k in key_list:
        # If retval is not a dictionary, we're going too deep
        if not isinstance(retval, dict):
            return None

        if k in retval:
            retval = retval[k]

        else:
            return None
    return retval


def get_class_property_dict(obj):
    """
    Return a dictionary of a class's @properties.
    """
    properties = {}
    for name, attribute in inspect.getmembers(type(obj)):
        if isinstance(attribute, property):
            properties[name] = getattr(obj, name)
    return properties
