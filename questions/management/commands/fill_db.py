import random
import time
from datetime import timedelta
from itertools import batched

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag

BATCH_SIZE = 5000
POOL_SIZE = 1000


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными: python manage.py fill_db [ratio]'

    def add_arguments(self, parser):
        parser.add_argument('ratio', nargs='?', type=int, default=10)

    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 1:
            raise CommandError('ratio должен быть больше 0')

        self.fake = Faker()
        self.now = timezone.now()
        self.started = time.monotonic()
        # Faker медленный, на миллион ответов его не хватит: заранее делаем пул текстов и берём из него случайные
        self.titles = [self.fake.sentence(nb_words=8)[:-1] + '?' for _ in range(POOL_SIZE)]
        self.texts = [self.fake.paragraph(nb_sentences=5) for _ in range(POOL_SIZE)]

        user_ids = self.create_users(ratio)
        tag_ids = self.create_tags(ratio)
        question_ids, question_dates = self.create_questions(ratio * 10, user_ids, tag_ids)
        answer_ids = self.create_answers(ratio * 100, user_ids, question_ids, question_dates)
        # оценки: четверть вопросам, остальное ответам
        self.create_likes(QuestionLike, 'question_id', ratio * 50, user_ids, question_ids)
        self.create_likes(AnswerLike, 'answer_id', ratio * 150, user_ids, answer_ids)
        self.update_counters()

    def log(self, message):
        self.stdout.write(f'[{time.monotonic() - self.started:6.1f} с] {message}')

    def save(self, model, objects):
        """Сохраняет объекты из генератора пачками через bulk_create и возвращает их id (по порядку)."""
        ids = []
        for batch in batched(objects, BATCH_SIZE):
            ids += [obj.id for obj in model.objects.bulk_create(batch)]
        return ids

    def random_date(self, start=None):
        start = start or self.now - timedelta(days=365)
        seconds = int((self.now - start).total_seconds())
        return start + timedelta(seconds=random.randint(0, max(seconds, 0)))

    def create_users(self, count):
        password = make_password('password')   # хэшируем один раз: make_password специально медленный
        last_id = User.objects.order_by('-id').values_list('id', flat=True).first() or 0

        def users():
            for i in range(last_id + 1, last_id + count + 1):
                username = f'{self.fake.user_name()}{i}'
                yield User(username=username, email=f'{username}@example.com', password=password,
                           date_joined=self.random_date())

        user_ids = self.save(User, users())
        self.save(Profile, (Profile(user_id=user_id, nickname=self.fake.first_name()) for user_id in user_ids))
        self.log(f'пользователи и профили: {len(user_ids)}')
        return user_ids

    def create_tags(self, count):
        names = set(Tag.objects.values_list('name', flat=True))
        new_names = []
        while len(new_names) < count:
            name = f'{self.fake.word()}-{self.fake.word()}'
            if name not in names:
                names.add(name)
                new_names.append(name)
        tag_ids = self.save(Tag, (Tag(name=name) for name in new_names))
        self.log(f'теги: {len(tag_ids)}')
        return tag_ids

    def create_questions(self, count, user_ids, tag_ids):
        dates = [self.random_date() for _ in range(count)]
        questions = (
            Question(title=random.choice(self.titles), text=random.choice(self.texts),
                     author_id=random.choice(user_ids), created_at=created_at)
            for created_at in dates
        )
        question_ids = self.save(Question, questions)

        Through = Question.tags.through
        links = (
            Through(question_id=question_id, tag_id=tag_id)
            for question_id in question_ids
            for tag_id in random.sample(tag_ids, min(random.randint(1, 3), len(tag_ids)))
        )
        self.save(Through, links)
        self.log(f'вопросы: {len(question_ids)}')
        return question_ids, dates

    def create_answers(self, count, user_ids, question_ids, question_dates):
        def answers():
            for _ in range(count):
                index = random.randrange(len(question_ids))
                yield Answer(question_id=question_ids[index], author_id=random.choice(user_ids),
                             text=random.choice(self.texts), is_correct=random.random() < 0.1,
                             created_at=self.random_date(question_dates[index]))

        answer_ids = self.save(Answer, answers())
        self.log(f'ответы: {len(answer_ids)}')
        return answer_ids

    def create_likes(self, model, field, count, user_ids, object_ids):
        # каждому объекту — k разных пользователей, поэтому пары (пользователь, объект) не повторяются
        per_object, extra = divmod(count, len(object_ids))

        def likes():
            for index, object_id in enumerate(object_ids):
                k = min(per_object + (index < extra), len(user_ids))
                for user_id in random.sample(user_ids, k):
                    yield model(user_id=user_id, value=1 if random.random() < 0.75 else -1,
                                created_at=self.random_date(), **{field: object_id})

        like_ids = self.save(model, likes())
        self.log(f'{model._meta.verbose_name_plural}: {len(like_ids)}')

    def update_counters(self):
        # рейтинг и число ответов пересчитываем тремя UPDATE на всю таблицу, а не по одному объекту
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE questions_question q SET rating = s.total
                FROM (SELECT question_id, SUM(value) AS total FROM questions_questionlike GROUP BY question_id) s
                WHERE q.id = s.question_id
            ''')
            cursor.execute('''
                UPDATE questions_answer a SET rating = s.total
                FROM (SELECT answer_id, SUM(value) AS total FROM questions_answerlike GROUP BY answer_id) s
                WHERE a.id = s.answer_id
            ''')
            cursor.execute('''
                UPDATE questions_question q SET answers_count = s.total
                FROM (SELECT question_id, COUNT(*) AS total FROM questions_answer GROUP BY question_id) s
                WHERE q.id = s.question_id
            ''')
        self.log('рейтинги и количество ответов пересчитаны')
