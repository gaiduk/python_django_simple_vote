# polls/templatetags/poll_filters.py
from django import template

register = template.Library()

@register.filter
def get_option_by_id(options_list, option_id_str):
    """
    Повертає текст варіанта зі списку options_list за заданим option_id.
    Приймає список/queryset об'єктів Option та option_id як рядок.
    Цей фільтр може бути не потрібен, якщо ми передаємо мапу ID -> Text з view.
    """
    try:
        option_id = int(option_id_str)
        for option in options_list:
            if option.id == option_id:
                return option.text
        return "Невідомий варіант"
    except (ValueError, AttributeError): # Додано AttributeError для безпеки
        return "Некоректний ID варіанта або список об'єктів"

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Повертає значення з словника за ключем.
    Використання: {{ my_dict|get_item:key }}
    """
    return dictionary.get(key)