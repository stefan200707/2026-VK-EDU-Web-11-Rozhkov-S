import re

from django import forms
from django.db import transaction
from django.db.models import F

from core.forms import BootstrapFormMixin

from .models import Answer, Question, Tag

MAX_TAGS = 3
TAG_RE = re.compile(r'^[\w+#.-]+$')


class QuestionForm(BootstrapFormMixin, forms.ModelForm):
    tags = forms.CharField(label='Tags', required=False, max_length=200,
                           help_text='Через запятую, не больше 3 тегов',
                           widget=forms.TextInput(attrs={'placeholder': 'moon, park, puzzle'}))

    class Meta:
        model = Question
        fields = ['title', 'text']   # теги — отдельное текстовое поле, сохраняются в save()
        labels = {'title': 'Title', 'text': 'Text'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'How to build a moon park?'}),
            'text': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Describe your problem in detail'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise forms.ValidationError('Заголовок слишком короткий, минимум 5 символов')
        return title

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 10:
            raise forms.ValidationError('Опишите вопрос подробнее, минимум 10 символов')
        return text

    def clean_tags(self):
        names = []
        for name in self.cleaned_data['tags'].split(','):
            name = name.strip().lower()
            if name and name not in names:
                names.append(name)
        if len(names) > MAX_TAGS:
            raise forms.ValidationError(f'Можно указать не больше {MAX_TAGS} тегов')
        for name in names:
            if len(name) > 50 or not TAG_RE.match(name):
                raise forms.ValidationError(f'Неверный тег «{name}»: только буквы, цифры и символы _ - + # ., до 50 символов')
        return names

    def save(self, commit=True):
        question = super().save(commit=False)
        question.author = self.user
        with transaction.atomic():
            question.save()
            tags = [Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data['tags']]
            question.tags.set(tags)
        return question


class AnswerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        labels = {'text': 'Answer'}
        widgets = {'text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter your answer here..'})}

    def __init__(self, user, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.question = question

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 10:
            raise forms.ValidationError('Ответ слишком короткий, минимум 10 символов')
        return text

    def save(self, commit=True):
        answer = super().save(commit=False)
        answer.author = self.user
        answer.question = self.question
        with transaction.atomic():
            answer.save()
            Question.objects.filter(pk=self.question.pk).update(answers_count=F('answers_count') + 1)
        return answer


class VoteForm(forms.Form):
    """Лайк/дизлайк через AJAX: id объекта и тип оценки."""
    model = None   # Question или Answer
    id = forms.IntegerField(min_value=1)
    type = forms.ChoiceField(choices=[('like', 'Лайк'), ('dislike', 'Дизлайк')])

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.object = None

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data
        self.object = self.model.objects.filter(pk=cleaned_data['id']).first()
        if self.object is None:
            raise forms.ValidationError('Объект не найден', code='not_found')
        cleaned_data['value'] = 1 if cleaned_data['type'] == 'like' else -1
        if self.object.likes.filter(user=self.user, value=cleaned_data['value']).exists():
            raise forms.ValidationError('Вы уже поставили эту оценку', code='already_voted')
        return cleaned_data

    def save(self):
        return self.object.vote(self.user, self.cleaned_data['value'])


class QuestionVoteForm(VoteForm):
    model = Question


class AnswerVoteForm(VoteForm):
    model = Answer


class CorrectAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    answer_id = forms.IntegerField(min_value=1)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.answer = None

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data
        self.answer = Answer.objects.select_related('question').filter(
            pk=cleaned_data['answer_id'], question_id=cleaned_data['question_id']).first()
        if self.answer is None:
            raise forms.ValidationError('Ответ не найден', code='not_found')
        if self.answer.question.author_id != self.user.id:
            raise forms.ValidationError('Отмечать правильный ответ может только автор вопроса', code='forbidden')
        return cleaned_data

    def save(self):
        return self.answer.toggle_correct()
