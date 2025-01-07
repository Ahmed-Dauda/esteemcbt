from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """
    Safely get a value from a dictionary by its key.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}
