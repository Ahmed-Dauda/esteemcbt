# from django import template

# register = template.Library()

# @register.filter
# def get_item(dictionary, key):
#     return dictionary.get(key, 'No comment available')

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 'N/A')


