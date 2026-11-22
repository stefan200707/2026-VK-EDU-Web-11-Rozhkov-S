from django.db import models


class QuestionManager(models.Manager):
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
    def for_question(self, question):
        # старые ответы сверху, новый ответ попадает на последнюю страницу
        return self.filter(question=question).select_related('author__profile').order_by('created_at', 'id')

    def best_author_ids(self, since, limit):
        return self.filter(created_at__gte=since).order_by('-rating').values_list('author_id', 'rating')[:limit]


class TagManager(models.Manager):
    def popular(self, limit=20):
        return self.annotate(questions_count=models.Count('questions')).order_by('-questions_count', 'name')[:limit]
