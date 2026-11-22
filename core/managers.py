from datetime import timedelta

from django.db import models
from django.utils import timezone


class ProfileManager(models.Manager):
    def best(self, limit=10, days=7):
        """Авторы самых популярных вопросов и ответов за последние days дней."""
        from questions.models import Answer, Question

        since = timezone.now() - timedelta(days=days)
        rows = list(Question.objects.best_author_ids(since, limit)) + list(Answer.objects.best_author_ids(since, limit))
        rows.sort(key=lambda row: row[1], reverse=True)
        author_ids = list(dict.fromkeys(author_id for author_id, rating in rows))[:limit]
        profiles = self.select_related('user').in_bulk(author_ids, field_name='user_id')
        return [profiles[author_id] for author_id in author_ids if author_id in profiles]
