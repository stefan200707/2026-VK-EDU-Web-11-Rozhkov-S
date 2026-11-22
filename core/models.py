import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from .managers import ProfileManager


def avatar_upload_to(instance, filename):
    # случайное имя файла: по ссылке нельзя перебрать чужие аватарки
    ext = os.path.splitext(filename)[1].lower()
    return f'avatars/{uuid.uuid4().hex}{ext}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    nickname = models.CharField(max_length=30, blank=True, verbose_name='Никнейм')
    avatar = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True, verbose_name='Аватарка')

    objects = ProfileManager()

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.nickname or self.user.username

    @property
    def avatar_url(self):
        # если аватарки нет, в шаблоне подставится картинка по умолчанию
        return self.avatar.url if self.avatar else ''
