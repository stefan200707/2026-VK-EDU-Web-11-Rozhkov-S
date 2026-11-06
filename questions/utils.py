from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Возвращает страницу из ?page=N; неверный номер заменяется первой страницей."""
    paginator = Paginator(objects_list, per_page)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        # ?page=abc, ?page=0, ?page=-1, ?page=99999
        page = paginator.page(1)

    # Номера для шаблона: первая, последняя и две соседние с текущей, между ними пропуск (None).
    # Пример: 1 2 3 None 10
    page.page_numbers = []
    previous = 0
    for number in paginator.page_range:
        if number in (1, paginator.num_pages) or abs(number - page.number) <= 2:
            if number - previous > 1:
                page.page_numbers.append(None)
            page.page_numbers.append(number)
            previous = number
    return page
