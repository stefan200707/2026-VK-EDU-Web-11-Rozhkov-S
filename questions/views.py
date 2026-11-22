from django.shortcuts import get_object_or_404, render

from .models import Answer, Question, Tag
from .utils import paginate


def index(request):
    page = paginate(Question.objects.new(), request)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    page = paginate(Question.objects.best(), request)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    page = paginate(Question.objects.by_tag(tag), request)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag})


def question(request, question_id):
    question = get_object_or_404(Question.objects.with_relations(), pk=question_id)
    page = paginate(Answer.objects.for_question(question), request, per_page=5)
    return render(request, 'questions/question.html', {'question': question, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
