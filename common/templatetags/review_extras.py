from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря по ключу"""
    if isinstance(key, str):
        key = int(key)
    return dictionary.get(key, 0)

@register.filter
def mul(value, arg):
    """Умножить значение на аргумент"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Разделить значение на аргумент"""
    try:
        if int(arg) == 0:
            return 0
        return int(value) / int(arg)
    except (ValueError, TypeError):
        return 0