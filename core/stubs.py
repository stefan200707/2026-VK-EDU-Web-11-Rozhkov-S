"""Данные-заглушки для правой колонки и юзерблока (позже заменим выборкой из БД)."""

# name — слово тега, css — класс размера/цвета из style.css
POPULAR_TAGS = [
    {'name': 'perl', 'css': 'tag-small'},
    {'name': 'python', 'css': 'tag-red'},
    {'name': 'Technopark', 'css': ''},
    {'name': 'MySQL', 'css': 'tag-big tag-red'},
    {'name': 'django', 'css': 'tag-green'},
    {'name': 'Mail.Ru', 'css': ''},
    {'name': 'Voloshin', 'css': 'tag-small'},
    {'name': 'Firefox', 'css': 'tag-yellow'},
]

BEST_MEMBERS = ['Mr. Freeman', 'Dr. House', 'Bender', 'Queen Victoria', 'V. Pupkin']

# Авторизованный пользователь (показывается на странице профиля)
CURRENT_USER = {
    'login': 'dr_pepper',
    'email': 'dr.pepper',   # намеренно неверный: на странице профиля показываем ошибку поля
    'nickname': 'Dr. Pepper',
    'avatar': 'core/img/avatar-1.svg',
}
