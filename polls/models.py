# polls/models.py
from django.db import models
from django.utils import timezone

class Option(models.Model):
    """Модель для варіантів голосування."""
    text = models.CharField(max_length=200, verbose_name="Текст варіанта")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Варіант голосування"
        verbose_name_plural = "Варіанти голосування"

class Vote(models.Model):
    """Модель для збереження голосів."""
    option = models.ForeignKey(Option, on_delete=models.CASCADE, verbose_name="Варіант")
    voter_nickname = models.CharField(max_length=100, verbose_name="Нікнейм голосуючого")
    score = models.IntegerField(verbose_name="Оцінка (бали)") # 1, 2, або 3 бали
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Час голосування")

    def __str__(self):
        return f"{self.voter_nickname} проголосував за '{self.option.text}' з {self.score} балами"

    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоси"

class VotedUser(models.Model):
    """Модель для відстеження користувачів, які вже проголосували."""
    nickname = models.CharField(max_length=100, unique=True, verbose_name="Нікнейм")
    # Ця модель просто фіксує, що даний нікнейм завершив голосування.
    # Фактичні голоси зберігаються у моделі Vote.

    def __str__(self):
        return self.nickname

    class Meta:
        verbose_name = "Проголосований користувач"
        verbose_name_plural = "Проголосовані користувачі"