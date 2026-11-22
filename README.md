# AskPupkin

Учебный проект по курсу «Веб-технологии» (VK Education): сайт вопросов и ответов, клон Stack Overflow.

- **Автор:** Стефан Рожков, группа WEB-11
- **Преподаватель:** Салохиддин Рахмонкулов ([@Infinity10K](https://github.com/Infinity10K))
- **Ментор:** Егор Яковлев ([@klef99](https://github.com/klef99))
- **ДЗ 1:** статическая вёрстка на HTML, CSS и Bootstrap 5.3 (папка `public/`)
- **ДЗ 2:** Django-проект с данными-заглушками, шаблонами, маршрутами и пагинацией
- **ДЗ 3:** модели и PostgreSQL, админка, наполнение базы командой `fill_db`, страницы на данных из БД
- **ДЗ 4:** вход, регистрация, профиль с аватаркой, формы вопроса и ответа, лайки и правильный ответ через AJAX

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

## ДЗ 3: база данных PostgreSQL

Схема базы: `schema.png`.

Настройки берутся из переменных окружения: локально из `.env.local`, в Docker Compose из `.env.docker`. Оба файла не попадают в git, шаблон со всеми переменными — `.env.example`.

### Локально (база в Docker, Django в venv)

```bash
cp .env.example .env.local          # DB_HOST=localhost, DB_PORT=5433, свой пароль
cp .env.example .env.docker         # DB_HOST=db, DB_PORT=5432, тот же пароль в DB_PASSWORD и POSTGRES_PASSWORD
docker compose up -d db             # PostgreSQL 16 на порту 5433, данные в volume pgdata
pip install -r requirements.txt
python manage.py migrate
python manage.py fill_db 10000      # пользователи 10 000, вопросы 100 000, ответы 1 000 000, теги 10 000, оценки 2 000 000
python manage.py createsuperuser    # вход в админку /admin/
python manage.py runserver
```

`fill_db [ratio]` добавляет ratio пользователей и тегов, ratio * 10 вопросов, ratio * 100 ответов и ratio * 200 оценок. При ratio = 10000 команда работает несколько минут.

При `DEBUG=True` подключается django-debug-toolbar (панель справа на странице).

### Всё в Docker Compose

```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py fill_db 100
```

## ДЗ 4: авторизация, формы и AJAX

Запуск тот же, что в ДЗ 3, плюс `python manage.py migrate` (новая миграция для имён файлов аватарок).

- `/login/` — вход, поддерживает `?next=` (только адреса нашего сайта), ошибки и введённый логин сохраняются.
- `/signup/` — регистрация: логин, email, ник, пароль с проверкой по `AUTH_PASSWORD_VALIDATORS`, аватарка; создаётся `Profile`, после — вход и главная.
- `/logout/` — выход POST-запросом из шапки, пользователь остаётся на текущей странице.
- `/profile/` — email, ник и аватарка, только для вошедших (`login_required`, `LOGIN_URL = 'login'`).
- `/ask/` и форма ответа на `/question/<id>/` — `ModelForm`, не больше 3 тегов; после ответа переход на его страницу с якорем `#answer-<id>`.
- Аватарки сохраняются в `media/avatars/` под случайным именем (uuid), допустимы jpg, jpeg, png, gif и webp до 2 МБ; без аватарки показывается картинка по умолчанию.
- AJAX (`questions/static/questions/js/votes.js`, `fetch` с заголовком `X-CSRFToken`): лайк/дизлайк вопроса и ответа, отметка правильного ответа (только автор вопроса, правильный ответ один). Повторная та же оценка — ошибка, уже поставленная кнопка отключена. Ответы в JSON, ошибки: 400, 401, 403, 404, 405.
- Неавторизованному лайки, «ASK!» и форма ответа недоступны, подсказка в `title`.

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
| `/logout/` | `logout` | выход (POST) |
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
