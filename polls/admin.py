# polls/admin.py

from django.contrib import admin
from .models import Poll, Option, VotedUser, Vote


# Реєстрація моделі Poll
class OptionInline(admin.TabularInline):
    model = Option
    extra = 3  # Кількість порожніх форм для додавання варіантів


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    # Визначаємо групи полів для кращої організації в адмінці
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_active', 'created_at')
        }),
        ('Налаштування голосування', {
            'fields': ('allow_negative_scores', 'min_score_value', 'max_score_value', 'num_options_to_vote'),
            'description': 'Встановіть діапазон балів та кількість унікальних балів для розподілу.'
        }),
    )

    list_display = ('title', 'is_active', 'num_options_to_vote', 'get_score_range_display', 'created_at')
    list_filter = ('is_active', 'allow_negative_scores', 'created_at')  # Додано фільтр для негативних балів
    search_fields = ('title', 'description')
    inlines = [OptionInline]
    readonly_fields = ('created_at',)

    # Метод для відображення діапазону балів у list_display
    def get_score_range_display(self, obj):
        return f"Від {obj.min_score_value} до {obj.max_score_value}"

    get_score_range_display.short_description = "Діапазон балів"


# Реєстрація моделі VotedUser
@admin.register(VotedUser)
class VotedUserAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'poll', 'voted_at')
    list_filter = ('poll', 'voted_at')
    search_fields = ('nickname', 'poll__title')
    readonly_fields = ('voted_at',)


# Реєстрація моделі Vote
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('get_voted_user_nickname', 'get_poll_title', 'option', 'score')
    list_filter = ('option__poll', 'score')
    search_fields = ('voted_user__nickname', 'option__text', 'option__poll__title')
    raw_id_fields = ('voted_user', 'option')

    def get_poll_title(self, obj):
        return obj.option.poll.title

    get_poll_title.short_description = 'Опитування'

    def get_voted_user_nickname(self, obj):
        return obj.voted_user.nickname

    get_voted_user_nickname.short_description = 'Користувач'