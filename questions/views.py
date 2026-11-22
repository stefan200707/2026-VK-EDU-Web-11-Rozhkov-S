from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AnswerForm, AnswerVoteForm, CorrectAnswerForm, QuestionForm, QuestionVoteForm
from .models import ANSWERS_PER_PAGE, Answer, Question, Tag
from .utils import paginate


def questions_page(request, questions, template, context=None):
    page = paginate(questions, request)
    Question.objects.mark_votes(list(page), request.user)
    return render(request, template, {'page': page, **(context or {})})


def index(request):
    return questions_page(request, Question.objects.new(), 'questions/index.html')


def hot(request):
    return questions_page(request, Question.objects.best(), 'questions/hot.html')


def tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    return questions_page(request, Question.objects.by_tag(tag), 'questions/tag.html', {'tag': tag})


def question(request, question_id):
    question = get_object_or_404(Question.objects.with_relations(), pk=question_id)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        form = AnswerForm(request.user, question, request.POST)
        if form.is_valid():
            answer = form.save()
            return redirect(answer.get_absolute_url())
    else:
        form = AnswerForm(request.user, question)

    page = paginate(Answer.objects.for_question(question), request, per_page=ANSWERS_PER_PAGE)
    Question.objects.mark_votes([question], request.user)
    Answer.objects.mark_votes(list(page), request.user)
    return render(request, 'questions/question.html', {'question': question, 'page': page, 'form': form})


@login_required
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.user, request.POST)
        if form.is_valid():
            question = form.save()
            return redirect(question)
    else:
        form = QuestionForm(request.user)
    return render(request, 'questions/ask.html', {'form': form})


def ajax_login_required(view):
    # вместо редиректа на страницу входа — JSON с кодом 401, клиент сам отправит на /login/
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Войдите, чтобы выполнить это действие', 'login_url': reverse('login')},
                                status=401)
        return view(request, *args, **kwargs)
    return wrapper


def form_errors_response(form):
    # код ошибки берём из ValidationError формы: not_found — 404, forbidden — 403, остальное — 400
    status = 400
    for error in form.non_field_errors().as_data():
        status = {'not_found': 404, 'forbidden': 403}.get(error.code, status)
    messages = [f'{name}: {message}' if name != '__all__' else message
                for name, errors in form.errors.items() for message in errors]
    return JsonResponse({'error': '; '.join(messages)}, status=status)


def vote(request, form_class):
    form = form_class(request.user, request.POST)
    if not form.is_valid():
        return form_errors_response(form)
    rating = form.save()
    return JsonResponse({'id': form.object.id, 'rating': rating, 'vote': form.cleaned_data['value']})


@require_POST
@ajax_login_required
def question_vote(request):
    return vote(request, QuestionVoteForm)


@require_POST
@ajax_login_required
def answer_vote(request):
    return vote(request, AnswerVoteForm)


@require_POST
@ajax_login_required
def answer_correct(request):
    form = CorrectAnswerForm(request.user, request.POST)
    if not form.is_valid():
        return form_errors_response(form)
    is_correct = form.save()
    return JsonResponse({'answer_id': form.answer.id, 'is_correct': is_correct})
