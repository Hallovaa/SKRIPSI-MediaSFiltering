from django import template
register = template.Library()

@register.filter
def dict_get(dictionary, key):
    if dictionary:
        return dictionary.get(str(key))
    return None