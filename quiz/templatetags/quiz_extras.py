from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key. Tries both the original key and string version."""
    if not isinstance(dictionary, dict):
        return ''
    # Try the key directly first
    if key in dictionary:
        return dictionary[key]
    # Try string version of the key (since JSON serialization converts int keys to strings)
    str_key = str(key)
    if str_key in dictionary:
        return dictionary[str_key]
    return ''


@register.filter
def penalty_display(value):
    """Convert negative_marking_value to a display-friendly percentage.
    Old system stored values as marks (e.g. 0.2 = 20%).
    New system stores as percentage (e.g. 20 = 20%).
    If value < 1, multiply by 100 to convert from marks to percentage.
    """
    try:
        val = float(value)
    except (TypeError, ValueError):
        return '20'
    if 0 < val < 1:
        val = val * 100
    if val <= 0:
        val = 20
    # Remove .0 for whole numbers
    if val == int(val):
        return str(int(val))
    return str(round(val, 1))
