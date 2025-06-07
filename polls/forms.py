# polls/forms.py
from django import forms

class NicknameForm(forms.Form):
    nickname = forms.CharField(
        label="Введіть ваш нікнейм",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ваш нікнейм'})
    )