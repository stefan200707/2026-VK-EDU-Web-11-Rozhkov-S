from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .managers import AnswerManager, QuestionManager, TagManager

LIKE_CHOICES = [(1, 'Лайк'), (-1, 'Дизлайк')]


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')

    objects = TagManager()

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', args=[self.name])


class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions', verbose_name='Автор')
    # default вместо auto_now_add, чтобы fill_db мог задать дату в прошлом
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Дата создания')
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True, verbose_name='Теги')
    # денормализованные поля: пересчитываются при лайках и новых ответах, чтобы не считать агрегаты на каждой странице
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')
    answers_count = models.PositiveIntegerField(default=0, verbose_name='Количество ответов')

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        indexes = [
            models.Index(fields=['-rating', '-id'], name='question_rating_idx'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question', args=[self.id])


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers', verbose_name='Автор')
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Дата создания')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    rating = models.IntegerField(default=0, db_index=True, verbose_name='Рейтинг')

    objects = AnswerManager()

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        indexes = [
            models.Index(fields=['question', 'created_at'], name='answer_question_created_idx'),
        ]

    def __str__(self):
        return f'Ответ #{self.id} на вопрос #{self.question_id}'


class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_likes', verbose_name='Пользователь')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='likes', verbose_name='Вопрос')
    value = models.SmallIntegerField(choices=LIKE_CHOICES, verbose_name='Оценка')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата')

    class Meta:
        verbose_name = 'Оценка вопроса'
        verbose_name_plural = 'Оценки вопросов'
        unique_together = ['user', 'question']   # один пользователь — одна оценка вопроса

    def __str__(self):
        return f'{self.value:+d} вопросу #{self.question_id} от пользователя #{self.user_id}'


class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answer_likes', verbose_name='Пользователь')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='likes', verbose_name='Ответ')
    value = models.SmallIntegerField(choices=LIKE_CHOICES, verbose_name='Оценка')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата')

    class Meta:
        verbose_name = 'Оценка ответа'
        verbose_name_plural = 'Оценки ответов'
        unique_together = ['user', 'answer']

    def __str__(self):
        return f'{self.value:+d} ответу #{self.answer_id} от пользователя #{self.user_id}'
