from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

@register.filter
def get_month_name(month_num):
    """Convert month number to month name."""
    month_names = {
        1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
        5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
        9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
    }
    if month_num is None:
        return None
    try:
        return month_names.get(int(month_num))
    except (ValueError, TypeError):
        return None

@register.filter
def get_last(sequence):
    """Get last item from sequence (list, tuple, etc.)."""
    if sequence is None:
        return None
    try:
        return sequence[-1]
    except (IndexError, TypeError):
        return None

@register.filter
def get_key(dictionary, key):
    """Get value from dict by string key."""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def divide_by(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def pct_of(value, total):
    try:
        return round(float(value) / float(total) * 100, 2)
    except (ValueError, ZeroDivisionError):
        return 0

@register.simple_tag
def months_list():
    return [
        (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
        (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
        (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
    ]
