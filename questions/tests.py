import re
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from core.models import Profile

from .models import Answer, Question, Tag
from .utils import paginate

OBJECTS = list(range(1, 36))   # 35 объектов = 4 страницы по 10
MANY_OBJECTS = list(range(1, 101))   # 10 страниц


class PaginateTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def get_page(self, query='', per_page=10):
        request = self.factory.get('/', query)
        return paginate(OBJECTS, request, per_page)

    def test_default_is_first_page(self):
        page = self.get_page()
        self.assertEqual(page.number, 1)
        self.assertEqual(list(page), OBJECTS[:10])

    def test_valid_page(self):
        page = self.get_page({'page': 4})
        self.assertEqual(page.number, 4)
        self.assertEqual(list(page), OBJECTS[30:])

    def test_per_page(self):
        self.assertEqual(len(self.get_page(per_page=5)), 5)

    def test_bad_params_give_first_page(self):
        for value in ('abc', '99999', '-1', '0', '', '1.5'):
            with self.subTest(page=value):
                self.assertEqual(self.get_page({'page': value}).number, 1)


    def test_page_numbers_have_edges_and_gap(self):
        request = self.factory.get('/', {'page': 1})
        page = paginate(MANY_OBJECTS, request)
        self.assertEqual(page.page_numbers, [1, 2, 3, None, 10])


class EmptyDatabaseTests(TestCase):
    def test_empty_states(self):
        self.assertContains(self.client.get(reverse('index')), 'Пока нет ни одного вопроса')
        self.assertContains(self.client.get(reverse('hot')), 'Пока нет ни одного вопроса')
        self.assertContains(self.client.get(reverse('index')), 'Пока нет ни одного тега')

    def test_unknown_question_and_tag_are_404(self):
        self.assertEqual(self.client.get(reverse('question', args=[999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('tag', args=['no-such-tag'])).status_code, 404)


class PagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pupkin', 'pupkin@example.com', 'password')
        Profile.objects.create(user=cls.user, nickname='V. Pupkin')
        cls.tag = Tag.objects.create(name='django')
        cls.question = Question.objects.create(title='How to build a moon park?', text='Text', author=cls.user)
        cls.question.tags.add(cls.tag)
        cls.empty_question = Question.objects.create(title='Second question', text='Text', author=cls.user)
        Answer.objects.create(question=cls.question, author=cls.user, text='First answer')

    def test_all_pages_open(self):
        urls = [
            reverse('index'), reverse('hot'), reverse('tag', args=['django']),
            reverse('question', args=[self.question.id]), reverse('login'), reverse('signup'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        # страницы только для вошедших
        for name in ('profile', 'ask'):
            with self.subTest(url=name):
                self.assertRedirects(self.client.get(reverse(name)), f"{reverse('login')}?next={reverse(name)}")
        self.client.force_login(self.user)
        for name in ('profile', 'ask'):
            with self.subTest(url=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_pages_show_data(self):
        self.assertContains(self.client.get(reverse('index')), 'How to build a moon park?')
        self.assertContains(self.client.get(reverse('tag', args=['django'])), 'How to build a moon park?')
        self.assertContains(self.client.get(self.question.get_absolute_url()), 'First answer')
        self.assertContains(self.client.get(self.empty_question.get_absolute_url()),
                            'Пока нет ни одного ответа к этому вопросу')

    def test_bad_page_param_is_not_500(self):
        for value in ('abc', '99999', '-1', '0'):
            with self.subTest(page=value):
                self.assertEqual(self.client.get(reverse('index'), {'page': value}).status_code, 200)

    def test_number_of_queries_does_not_grow(self):
        # 15 новых вопросов с тегами: число запросов на странице не должно зависеть от количества вопросов
        for i in range(15):
            Question.objects.create(title=f'Question {i}', text='Text', author=self.user).tags.add(self.tag)
        self.client.get(reverse('index'))
        with self.assertNumQueries(7):
            self.client.get(reverse('index'))
        # у вошедшего пользователя добавляются сессия, пользователь, профиль в шапке и его оценки — тоже не от числа вопросов
        self.client.force_login(self.user)
        self.client.get(reverse('index'))
        with self.assertNumQueries(11):
            self.client.get(reverse('index'))
        for i in range(7):
            Answer.objects.create(question=self.question, author=self.user, text=f'Answer {i}')
        with self.assertNumQueries(13):
            self.client.get(self.question.get_absolute_url())

    def test_user_block(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'register')
        self.assertContains(response, 'title="Войдите, чтобы задать вопрос"')
        self.assertContains(response, 'title="Войдите, чтобы оценивать"')
        self.assertContains(self.client.get(self.question.get_absolute_url()), 'title="Войдите, чтобы ответить"')
        self.client.force_login(self.user)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Logout')
        self.assertContains(response, 'V. Pupkin')
        self.assertNotContains(response, 'Войдите, чтобы')

    def test_post_forms_with_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for name in ('login', 'signup', 'profile', 'ask'):
            with self.subTest(form=name):
                url = reverse(name)
                html = client.get(url).content.decode()
                self.assertIn('method="post"', html)
                token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
                response = client.post(url, {'csrfmiddlewaretoken': token, 'login': 'x'})
                self.assertEqual(response.status_code, 200)

    def test_post_without_token_is_forbidden(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('login')).status_code, 403)


class AskAndAnswerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pupkin', 'pupkin@example.com', 'password')
        Profile.objects.create(user=cls.user, nickname='V. Pupkin')
        cls.question = Question.objects.create(title='How to build a moon park?', text='Text', author=cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def test_ask_creates_question_with_tags(self):
        response = self.client.post(reverse('ask'), {'title': 'New question', 'text': 'Some long question text',
                                                     'tags': 'Django, python, django'})
        question = Question.objects.get(title='New question')
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(question.author, self.user)
        self.assertEqual(sorted(question.tags.values_list('name', flat=True)), ['django', 'python'])

    def test_ask_more_than_three_tags(self):
        response = self.client.post(reverse('ask'), {'title': 'New question', 'text': 'Some long question text',
                                                     'tags': 'a, b, c, d'})
        self.assertTrue(response.context['form'].has_error('tags'))
        self.assertContains(response, 'value="New question"')
        self.assertFalse(Question.objects.filter(title='New question').exists())

    def test_answer_redirects_to_last_page_with_anchor(self):
        for i in range(5):
            Answer.objects.create(question=self.question, author=self.user, text=f'Answer {i}')
        response = self.client.post(self.question.get_absolute_url(), {'text': 'My new long answer'})
        answer = Answer.objects.get(text='My new long answer')
        self.assertRedirects(response, f'{self.question.get_absolute_url()}?page=2#answer-{answer.id}')
        self.question.refresh_from_db()
        self.assertEqual(self.question.answers_count, 1)   # счётчик увеличился с 0 через F()

    def test_anonymous_cannot_answer(self):
        self.client.logout()
        response = self.client.post(self.question.get_absolute_url(), {'text': 'My new long answer'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Answer.objects.exists())


class AjaxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user('author', 'author@example.com', 'password')
        cls.other = User.objects.create_user('other', 'other@example.com', 'password')
        cls.question = Question.objects.create(title='Question', text='Text', author=cls.author)
        cls.answer = Answer.objects.create(question=cls.question, author=cls.other, text='Answer')
        cls.answer2 = Answer.objects.create(question=cls.question, author=cls.other, text='Answer 2', is_correct=True)

    def vote(self, type_, url_name='question_vote', object_id=None):
        return self.client.post(reverse(url_name), {'id': object_id or self.question.id, 'type': type_})

    def test_like_dislike_and_repeat(self):
        self.client.force_login(self.other)
        self.assertEqual(self.vote('like').json()['rating'], 1)
        response = self.vote('like')
        self.assertEqual(response.status_code, 400)
        self.assertIn('уже', response.json()['error'])
        self.assertEqual(self.vote('dislike').json()['rating'], -1)
        self.assertEqual(self.vote('like', 'answer_vote', self.answer.id).json()['rating'], 1)
        self.question.refresh_from_db()
        self.assertEqual(self.question.rating, -1)

    def test_vote_errors(self):
        self.assertEqual(self.vote('like').status_code, 401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('question_vote')).status_code, 405)
        self.assertEqual(self.vote('superlike').status_code, 400)
        self.assertEqual(self.client.post(reverse('question_vote'), {'id': 'abc', 'type': 'like'}).status_code, 400)
        self.assertEqual(self.vote('like', object_id=999999).status_code, 404)

    def test_vote_needs_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.other)
        self.assertEqual(client.post(reverse('question_vote'), {'id': self.question.id, 'type': 'like'}).status_code, 403)

    def test_correct_answer(self):
        data = {'question_id': self.question.id, 'answer_id': self.answer.id}
        self.assertEqual(self.client.post(reverse('answer_correct'), data).status_code, 401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('answer_correct'), data).status_code, 403)
        self.client.force_login(self.author)
        self.assertEqual(self.client.post(reverse('answer_correct'), {**data, 'answer_id': 999999}).status_code, 404)
        self.assertEqual(self.client.post(reverse('answer_correct'), {'answer_id': 'x'}).status_code, 400)
        response = self.client.post(reverse('answer_correct'), data)
        self.assertEqual(response.json(), {'answer_id': self.answer.id, 'is_correct': True})
        self.answer2.refresh_from_db()
        self.assertFalse(self.answer2.is_correct)   # правильный ответ у вопроса один
        self.assertFalse(self.client.post(reverse('answer_correct'), data).json()['is_correct'])

    def test_page_shows_user_vote(self):
        self.client.force_login(self.other)
        self.vote('like')
        response = self.client.get(self.question.get_absolute_url())
        self.assertContains(response, 'data-type="like" aria-label="Like"\n                aria-pressed="true" disabled')
        self.assertNotContains(response, 'correct-checkbox')   # чекбокс только у автора вопроса
        self.client.force_login(self.author)
        self.assertContains(self.client.get(self.question.get_absolute_url()), 'correct-checkbox')


class FillDbTests(TestCase):
    def test_fill_db(self):
        call_command('fill_db', 2, stdout=StringIO())
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(Tag.objects.count(), 2)
        self.assertEqual(Question.objects.count(), 20)
        self.assertEqual(Answer.objects.count(), 200)
        question = Question.objects.order_by('?').first()
        self.assertEqual(question.answers_count, question.answers.count())
        self.assertEqual(question.rating, sum(question.likes.values_list('value', flat=True)))
