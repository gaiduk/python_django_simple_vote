# polls/models.py

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError  # Імпортуємо ValidationError


class Poll(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    # Кількість опцій, яким користувач може присвоїти бали
    # Це буде КІЛЬКІСТЬ УНІКАЛЬНИХ БАЛІВ, ЯКІ ТРЕБА РОЗПОДІЛИТИ (наприклад, 3 для -1,+1,+2)
    num_options_to_vote = models.IntegerField(default=1,
                                              help_text="Кількість унікальних балів, які користувач повинен призначити.")

    # Нові поля для контролю діапазону балів
    allow_negative_scores = models.BooleanField(default=False,
                                                help_text="Дозволити голосування з від'ємними балами (0 буде виключено, якщо діапазон включає 0).")
    min_score_value = models.IntegerField(default=1,
                                          help_text="Мінімальне значення балу (наприклад, -2).")
    max_score_value = models.IntegerField(default=1,
                                          help_text="Максимальне значення балу (наприклад, +2).")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        # Перевірка, що min_score_value менше або дорівнює max_score_value
        if self.min_score_value > self.max_score_value:
            raise ValidationError('Мінімальне значення балу не може бути більшим за максимальне.')

        # Формуємо повний список можливих балів у заданому діапазоні
        all_possible_scores_in_range = list(range(self.min_score_value, self.max_score_value + 1))

        # Якщо дозволені негативні бали І 0 присутній у діапазоні, виключаємо 0
        if self.allow_negative_scores and 0 in all_possible_scores_in_range:
            filtered_scores = [score for score in all_possible_scores_in_range if score != 0]
        else:
            filtered_scores = all_possible_scores_in_range

        # Обчислюємо очікувану кількість унікальних балів після фільтрації
        calculated_num_options_to_vote = len(filtered_scores)

        # Перевірка, що num_options_to_vote відповідає кількості унікальних балів
        if self.num_options_to_vote != calculated_num_options_to_vote:
            error_message_suffix = ""
            if self.allow_negative_scores and 0 in all_possible_scores_in_range:
                error_message_suffix = " (без 0)"

            raise ValidationError(
                f"Кількість опцій для голосування ({self.num_options_to_vote}) має дорівнювати "
                f"кількості унікальних балів у діапазоні від {self.min_score_value} до {self.max_score_value}"
                f"{error_message_suffix} (тобто {calculated_num_options_to_vote})."
            )

    def save(self, *args, **kwargs):
        # Якщо це нове опитування або воно стає активним,
        # переконаємося, що всі інші опитування неактивні.
        if self.is_active:
            Poll.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text


class VotedUser(models.Model):
    nickname = models.CharField(max_length=100)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname} ({self.poll.title})"

    class Meta:
        unique_together = ('nickname', 'poll')


class Vote(models.Model):
    voted_user = models.ForeignKey(VotedUser, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.voted_user.nickname} voted {self.score} for {self.option.text} in {self.option.poll.title}"

    class Meta:
        unique_together = ('voted_user', 'option')