# polls/templatetags/poll_filters.py
from django import template
from ..models import Option

register = template.Library()

@register.filter
def get_option_by_id(options_queryset, option_id_str):
    """
    Повертає текст варіанта за його ID.
    Приймає queryset Options та option_id як рядок.
    """
    try:
        option_id = int(option_id_str)
        # Важливо: options_queryset - це QuerySet. Якщо ви передаєте Option.objects.all(),
        # то можна шукати прямо в ньому.
        # Але щоб уникнути зайвих запитів до БД, якщо ви передали весь QuerySet з options
        # у контекст, краще знайти елемент у ньому.
        # Однак, QuerySet.get() завжди зробить запит до БД, тому це не найкращий спосіб.
        # Краще було б передати map {id: text} з view.
        # Для простоти, залишимо як є, але майте на увазі, що це може бути неефективно для великої кількості опцій.
        option = Option.objects.get(pk=option_id) # Запит до БД
        return option.text
    except (ValueError, Option.DoesNotExist):
        return "Невідомий варіант"