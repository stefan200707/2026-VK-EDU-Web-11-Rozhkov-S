from .stubs import BEST_MEMBERS, POPULAR_TAGS


def sidebar(request):
    """Контекстный процессор добавляет эти данные в каждый шаблон: сайдбар есть на всех страницах,
    и не нужно передавать теги и пользователей из каждой view."""
    return {'popular_tags': POPULAR_TAGS, 'best_members': BEST_MEMBERS}
