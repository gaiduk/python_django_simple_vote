# polls/admin.py

from django.contrib import admin
from .models import Option, Vote, VotedUser
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Sum


# Це новий клас для відображення голосів як "вбудованих" на сторінці Option
class VoteInline(admin.TabularInline):  # TabularInline виглядає як таблиця, StackedInline - як блок
    model = Vote
    extra = 0  # Не показувати порожні форми для додавання нових голосів
    fields = ('voter_nickname', 'score', 'timestamp',)  # Які поля показувати
    readonly_fields = ('voter_nickname', 'score', 'timestamp',)  # Зробити їх тільки для читання
    can_delete = False  # Заборонити видалення голосів прямо звідси

    # Можна також додати можливість відображати посилання на редагування голосу,
    # але для цього потрібно трохи більше налаштувань.
    # Наразі ми просто відображаємо дані.


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'total_score_display')
    search_fields = ('text',)
    inlines = [VoteInline]  # <--- ДОДАЙТЕ ЦЕЙ РЯДОК!

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(total_score=Sum('vote__score'))

    def total_score_display(self, obj):
        return obj.total_score if obj.total_score is not None else 0

    total_score_display.short_description = 'Загальні бали'
    total_score_display.admin_order_field = 'total_score'


# Решта класів Admin залишаються без змін
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter_nickname', 'option', 'score', 'timestamp')
    list_filter = ('option', 'score', 'timestamp')
    search_fields = ('voter_nickname', 'option__text')
    list_display_links = ('voter_nickname', 'option',)


@admin.register(VotedUser)
class VotedUserAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'action_links')
    search_fields = ('nickname',)

    def action_links(self, obj):
        return format_html(
            '<a href="{}">Видалити голоси</a>',
            reverse('admin:delete_user_votes', args=[obj.nickname])
        )

    action_links.short_description = "Дії"

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('delete-user-votes/<str:nickname>/', self.admin_site.admin_view(self.delete_user_votes),
                 name='delete_user_votes'),
        ]
        return custom_urls + urls

    def delete_user_votes(self, request, nickname):
        if request.method == 'POST':
            pass

        Vote.objects.filter(voter_nickname=nickname).delete()
        VotedUser.objects.filter(nickname=nickname).delete()

        self.message_user(request,
                          f"Усі голоси для нікнейму '{nickname}' були видалені. Користувач тепер може голосувати знову.",
                          messages.SUCCESS)
        return redirect('admin:polls_voteduser_changelist')