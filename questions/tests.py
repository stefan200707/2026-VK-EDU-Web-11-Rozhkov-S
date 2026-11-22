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
            reverse('profile'), reverse('ask'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

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

    def test_user_block(self):
        self.assertContains(self.client.get(reverse('index')), 'register')
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('profile')), 'Logout')
        self.assertContains(self.client.get(reverse('profile')), 'V. Pupkin')

    def test_post_forms_with_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
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
