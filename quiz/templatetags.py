# Create a file called templatetags.py inside your app directory (e.g., myapp/templatetags.py)

from django import template

register = template.Library()

@register.filter
def split_string(value, delimiter):
    return value.split(delimiter)
