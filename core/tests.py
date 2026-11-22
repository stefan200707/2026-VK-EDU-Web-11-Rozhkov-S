import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Profile

MEDIA_ROOT = tempfile.mkdtemp()


def make_png(name='avatar.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buffer, 'PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('pupkin', 'pupkin@example.com', 'Strong-pass-123')
        Profile.objects.create(user=cls.user, nickname='V. Pupkin')

    def test_login_redirects_to_next(self):
        response = self.client.post(reverse('login') + '?next=/hot/', {'username': 'pupkin', 'password': 'Strong-pass-123'})
        self.assertRedirects(response, '/hot/')

    def test_external_next_is_ignored(self):
        response = self.client.post(reverse('login'), {'username': 'pupkin', 'password': 'Strong-pass-123',
                                                       'next': 'https://evil.com/'})
        self.assertRedirects(response, reverse('index'))

    def test_wrong_password_shows_error_and_keeps_login(self):
        response = self.client.post(reverse('login'), {'username': 'pupkin', 'password': 'wrong'})
        self.assertContains(response, 'Неверный логин или пароль')
        self.assertContains(response, 'value="pupkin"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_stays_on_page(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'), {'next': '/hot/?page=2'})
        self.assertRedirects(response, '/hot/?page=2')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)


class SignupTests(TestCase):
    data = {'username': 'newbie', 'email': 'newbie@example.com', 'nickname': 'Newbie',
            'password': 'Strong-pass-123', 'password2': 'Strong-pass-123'}

    def test_signup_creates_user_with_profile(self):
        response = self.client.post(reverse('signup'), self.data)
        self.assertRedirects(response, reverse('index'))
        user = User.objects.get(username='newbie')
        self.assertEqual(user.profile.nickname, 'Newbie')
        self.assertTrue(user.check_password('Strong-pass-123'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_weak_password_shows_validator_errors(self):
        response = self.client.post(reverse('signup'), {**self.data, 'password': '123', 'password2': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('password'))
        self.assertContains(response, 'value="newbie@example.com"')
        self.assertFalse(User.objects.filter(username='newbie').exists())

    def test_passwords_must_match(self):
        response = self.client.post(reverse('signup'), {**self.data, 'password2': 'Other-pass-123'})
        self.assertTrue(response.context['form'].has_error('password2'))


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user('pupkin', 'pupkin@example.com', 'Strong-pass-123')
        Profile.objects.create(user=self.user, nickname='V. Pupkin')

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('profile'), fetch_redirect_response=False)

    def test_profile_form_is_prefilled(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'value="pupkin@example.com"')
        self.assertContains(response, 'value="V. Pupkin"')

    def test_upload_avatar(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {'email': 'new@example.com', 'nickname': 'Pupkin',
                                                         'avatar': make_png()})
        self.assertRedirects(response, reverse('profile'))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.user.email, 'new@example.com')
        self.assertRegex(profile.avatar.name, r'^avatars/[0-9a-f]{32}\.png$')

    def test_bad_avatar_shows_error(self):
        self.client.force_login(self.user)
        files = {
            'text': SimpleUploadedFile('avatar.txt', b'hello', content_type='text/plain'),
            'big': SimpleUploadedFile('avatar.png', make_png().read() + b'0' * 3 * 1024 * 1024, content_type='image/png'),
        }
        for name, file in files.items():
            with self.subTest(file=name):
                response = self.client.post(reverse('profile'), {'email': 'pupkin@example.com', 'nickname': 'Pupkin',
                                                                 'avatar': file})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].has_error('avatar'))
                self.assertContains(response, 'value="Pupkin"')
