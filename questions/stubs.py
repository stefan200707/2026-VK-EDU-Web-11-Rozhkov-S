"""Вопросы и ответы-заглушки (позже заменим выборкой из БД)."""
from datetime import datetime, timedelta

from core.stubs import BEST_MEMBERS

TAG_NAMES = ['blablabla', 'perl', 'python', 'Technopark', 'MySQL', 'django', 'Mail.Ru', 'Voloshin', 'Firefox', 'black-jack', 'bender']
AVATARS = ['questions/img/avatar-1.svg', 'questions/img/avatar-2.svg', 'questions/img/avatar-3.svg']
LIKE_STATES = ['up', 'down', 'none']   # три состояния виджета лайков
LIKE_COUNTS = {'up': 5, 'down': -2, 'none': 0}

ANSWERS = []
for i in range(1, 24):
    state = LIKE_STATES[i % 3]
    ANSWERS.append({
        'id': i,
        'text': 'First of all I would like to thank you for the invitation to participate in such a ... Russia is the '
                'huge territory which in many respects needs to be render habitable.',
        'author': BEST_MEMBERS[i % len(BEST_MEMBERS)],
        'avatar': AVATARS[i % 3],
        'rating': LIKE_COUNTS[state],
        'like_state': state,
        'is_correct': i == 1,
        'created': datetime(2026, 10, 26, 8, 30) + timedelta(hours=i),
    })

QUESTIONS = []
for i in range(1, 101):
    state = LIKE_STATES[i % 3]
    QUESTIONS.append({
        'id': i,
        'title': f'How to build a moon park? ({i})',
        'text': f'Guys, I have trouble with a moon park number {i}. Can\'t find the black-jack and the rest of the '
                f'entertainment. Has anyone built one before and can share the plans?',
        'author': BEST_MEMBERS[i % len(BEST_MEMBERS)],
        'avatar': AVATARS[i % 3],
        'rating': LIKE_COUNTS[state] + i % 4,
        'like_state': state,
        'answers_count': len(ANSWERS),
        'tags': [TAG_NAMES[i % len(TAG_NAMES)], TAG_NAMES[(i + 3) % len(TAG_NAMES)]],
        'created': datetime(2026, 10, 25, 18, 0) - timedelta(hours=7 * i),
    })
