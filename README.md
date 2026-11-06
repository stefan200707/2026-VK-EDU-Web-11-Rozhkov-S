# AskPupkin

Учебный проект по курсу «Веб-технологии» (VK Education): сайт вопросов и ответов, клон Stack Overflow.

- **Автор:** Стефан Рожков, группа WEB-11
- **Преподаватель:** Салохиддин Рахмонкулов ([@Infinity10K](https://github.com/Infinity10K))
- **Ментор:** Егор Яковлев ([@klef99](https://github.com/klef99))
- **ДЗ 1:** статическая вёрстка на HTML, CSS и Bootstrap 5.3 (папка `public/`)
- **ДЗ 2:** Django-проект с данными-заглушками, шаблонами, маршрутами и пагинацией

## ДЗ 1: как открыть вёрстку

Сервер не нужен. Откройте в браузере `public/index.html` двойным кликом. Bootstrap, стили и картинки лежат локально в `public/static/`.

| Файл | Страница |
|---|---|
| `public/base.html` | общий каркас: шапка, колонка контента, правая колонка, подвал |
| `public/index.html` | главная: новые вопросы, пагинатор |
| `public/hot.html` | лучшие вопросы |
| `public/tag.html` | вопросы по тегу |
| `public/question.html` | вопрос, ответы, форма ответа |
| `public/ask.html` | создание вопроса |
| `public/login.html` | вход |
| `public/signup.html` | регистрация |
| `public/profile.html` | настройки профиля |

## ДЗ 2: запуск Django

### Локально (venv + requirements)

```bash
python3 -m venv .venv             # или: uv venv --python 3.12 .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # или: uv pip install -r requirements.txt
cp .env.example .env              # необязательно: без .env тоже работает (режим разработки)
python manage.py migrate          # создаёт db.sqlite3 (нужен встроенным admin и auth)
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/. Данные страниц в ДЗ 2 берутся из заглушек, своих моделей пока нет.

Ошибки в формах показаны намеренно: это «рыба», формы пока ничего не проверяют.

### Через Docker Compose

```bash
docker compose up --build
```

Сайт: http://127.0.0.1:8000/. Код проекта и папка `media/` подключены как volume.

### Тесты

```bash
python manage.py test
```

## Страницы и маршруты

| URL | Имя маршрута | Страница |
|---|---|---|
| `/` | `index` | новые вопросы |
| `/hot/` | `hot` | лучшие вопросы |
| `/tag/<тег>/` | `tag` | вопросы по тегу |
| `/question/<id>/` | `question` | вопрос и ответы |
| `/ask/` | `ask` | создание вопроса |
| `/login/` | `login` | вход |
| `/signup/` | `signup` | регистрация |
| `/profile/` | `profile` | редактирование профиля |

Пагинация: `?page=N`, по 10 вопросов на странице, по 5 ответов. Неверный номер (`abc`, `0`, `-1`, `99999`) заменяется первой страницей. Несуществующий вопрос или тег даёт 404.

## Структура

```
application/   настройки и корневой urls.py
core/          вход, регистрация, профиль; base.html и общие include; static/core
questions/     списки вопросов, вопрос, ask; paginate() в utils.py; static/questions
public/        статическая вёрстка (ДЗ 1)
static/        сюда collectstatic собирает статику
media/         загруженные пользователями файлы
```
