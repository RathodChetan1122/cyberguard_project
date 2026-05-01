from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return a list. Usage: "a,b,c"|split:"," """
    return [item.strip() for item in str(value).split(delimiter)]
