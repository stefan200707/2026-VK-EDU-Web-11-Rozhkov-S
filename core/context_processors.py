from questions.models import Tag

from .models import Profile


def sidebar(request):
    """Контекстный процессор добавляет эти данные в каждый шаблон: сайдбар есть на всех страницах,
    и не нужно передавать теги и пользователей из каждой view.
    Выборки ленивые: запросы идут, только если шаблон их выводит (в админке их нет)."""
    return {'popular_tags': Tag.objects.popular(), 'best_members': Profile.objects.best}
