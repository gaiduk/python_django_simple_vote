# polls/forms.py
from django import forms
from .models import Poll, Option # Імпортуємо моделі Poll та Option

class NicknameForm(forms.Form):
    nickname = forms.CharField(label='Ваш нікнейм', max_length=100,
                               widget=forms.TextInput(attrs={'placeholder': 'Введіть ваш нікнейм'}))

class VoteForm(forms.Form):
    # Ця форма буде динамічно генерувати поля для голосування
    # Її використання трохи змінилось, оскільки ми перейшли на кнопки
    # але ми залишаємо її тут, якщо вона буде потрібна в майбутньому.
    # Наразі її використання мінімальне, оскільки бали передаються через кнопки.
    pass