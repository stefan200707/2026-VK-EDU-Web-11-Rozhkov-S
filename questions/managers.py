from django.db import models


def mark_votes(items, likes, field, user):
    """Проставляет item.user_vote (1, -1 или 0) — оценку текущего пользователя, одним запросом на страницу."""
    votes = {}
    if user.is_authenticated and items:
        votes = dict(likes.filter(user=user, **{f'{field}__in': items}).values_list(f'{field}_id', 'value'))
    for item in items:
        item.user_vote = votes.get(item.id, 0)
    return items


class QuestionManager(models.Manager):
    def mark_votes(self, questions, user):
        from .models import QuestionLike
        return mark_votes(questions, QuestionLike.objects, 'question', user)

    def with_relations(self):
        # автор с профилем — одним JOIN, теги — одним отдельным запросом на всю страницу
        return self.select_related('author__profile').prefetch_related('tags')

    def new(self):
        return self.with_relations().order_by('-created_at', '-id')

    def best(self):
        return self.with_relations().order_by('-rating', '-id')

    def by_tag(self, tag):
        return self.new().filter(tags=tag)

    def best_author_ids(self, since, limit):
        return self.filter(created_at__gte=since).order_by('-rating').values_list('author_id', 'rating')[:limit]


class AnswerManager(models.Manager):
    def mark_votes(self, answers, user):
        from .models import AnswerLike
        return mark_votes(answers, AnswerLike.objects, 'answer', user)

    def for_question(self, question):
        # старые ответы сверху, новый ответ попадает на последнюю страницу
        return self.filter(question=question).select_related('author__profile').order_by('created_at', 'id')

    def best_author_ids(self, since, limit):
        return self.filter(created_at__gte=since).order_by('-rating').values_list('author_id', 'rating')[:limit]


class TagManager(models.Manager):
    def popular(self, limit=20):
        return self.annotate(questions_count=models.Count('questions')).order_by('-questions_count', 'name')[:limit]
