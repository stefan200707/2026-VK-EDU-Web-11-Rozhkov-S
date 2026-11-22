from django import forms
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import UploadedFile

from .models import Profile

AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
AVATAR_MAX_SIZE = 2 * 1024 * 1024   # 2 МБ


def validate_avatar(avatar):
    # проверяем только новый загруженный файл, а не уже сохранённую аватарку
    if not isinstance(avatar, UploadedFile):
        return avatar
    ext = avatar.name.rsplit('.', 1)[-1].lower() if '.' in avatar.name else ''
    if ext not in AVATAR_EXTENSIONS:
        raise forms.ValidationError('Можно загрузить только картинку: ' + ', '.join(AVATAR_EXTENSIONS))
    if avatar.size > AVATAR_MAX_SIZE:
        raise forms.ValidationError('Файл слишком большой, максимум 2 МБ')
    return avatar


class BootstrapFormMixin:
    """Bootstrap-классы для полей и подсветка полей с ошибками."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def is_valid(self):
        valid = super().is_valid()
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs['class'] += ' is-invalid'
        return valid


class LoginForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(label='Login', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            self.user = auth.authenticate(self.request, username=username, password=password)
            if self.user is None:
                raise forms.ValidationError('Неверный логин или пароль')
        return cleaned_data


class SignupForm(BootstrapFormMixin, forms.ModelForm):
    nickname = forms.CharField(label='NickName', max_length=30, help_text='Имя, которое видно рядом с вопросами и ответами')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    avatar = forms.ImageField(label='Upload avatar', required=False, widget=forms.FileInput(attrs={'accept': 'image/*'}),
                              help_text='JPG, PNG, GIF или WEBP, до 2 МБ')

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {'username': 'Login', 'email': 'Email'}
        help_texts = {'username': 'Буквы, цифры и @/./+/-/_, до 150 символов'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        return email

    def clean_avatar(self):
        return validate_avatar(self.cleaned_data.get('avatar'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            self.add_error('password2', 'Пароли не совпадают')
        if password:
            # валидаторы из AUTH_PASSWORD_VALIDATORS, похожесть на логин и email тоже проверяется
            user = User(username=cleaned_data.get('username'), email=cleaned_data.get('email'))
            try:
                validate_password(password, user)
            except forms.ValidationError as error:
                self.add_error('password', error)
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
        )
        Profile.objects.create(user=user, nickname=self.cleaned_data['nickname'], avatar=self.cleaned_data.get('avatar'))
        return user


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    email = forms.EmailField(label='Email')

    class Meta:
        model = Profile
        fields = ['email', 'nickname', 'avatar']
        labels = {'nickname': 'NickName', 'avatar': 'Upload avatar'}
        help_texts = {'avatar': 'JPG, PNG, GIF или WEBP, до 2 МБ'}
        widgets = {'avatar': forms.FileInput(attrs={'accept': 'image/*'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].required = True
        self.fields['email'].initial = self.instance.user.email
        self.old_avatar = self.instance.avatar.name

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован')
        return email

    def clean_avatar(self):
        return validate_avatar(self.cleaned_data.get('avatar'))

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.email = self.cleaned_data['email']
        if commit:
            profile.user.save(update_fields=['email'])
            profile.save()
            # старый файл аватарки больше не нужен
            if 'avatar' in self.changed_data and self.old_avatar:
                profile.avatar.storage.delete(self.old_avatar)
        return profile
