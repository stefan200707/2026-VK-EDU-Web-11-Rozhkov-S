import re

from django.test import Client, RequestFactory, SimpleTestCase
from django.urls import reverse

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


class PagesTests(SimpleTestCase):
    def test_all_pages_open(self):
        urls = [
            reverse('index'), reverse('hot'), reverse('tag', args=['django']), reverse('tag', args=['blablabla']),
            reverse('question', args=[1]), reverse('login'), reverse('signup'),
            reverse('profile'), reverse('ask'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_bad_page_param_is_not_500(self):
        for value in ('abc', '99999', '-1', '0'):
            with self.subTest(page=value):
                self.assertEqual(self.client.get(reverse('index'), {'page': value}).status_code, 200)

    def test_unknown_question_and_tag_are_404(self):
        self.assertEqual(self.client.get(reverse('question', args=[999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('tag', args=['no-such-tag'])).status_code, 404)

    def test_user_block_only_on_profile(self):
        self.assertContains(self.client.get(reverse('profile')), 'Logout')
        self.assertNotContains(self.client.get(reverse('index')), 'Logout')
        self.assertContains(self.client.get(reverse('index')), 'register')

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
