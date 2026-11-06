from django.http import Http404
from django.shortcuts import render

from .stubs import ANSWERS, QUESTIONS, TAG_NAMES
from .utils import paginate


def index(request):
    new_questions = sorted(QUESTIONS, key=lambda q: q['created'], reverse=True)
    page = paginate(new_questions, request)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    best_questions = sorted(QUESTIONS, key=lambda q: q['rating'], reverse=True)
    page = paginate(best_questions, request)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    if tag_name not in TAG_NAMES:
        raise Http404('Unknown tag')
    tagged = [q for q in QUESTIONS if tag_name in q['tags']]
    page = paginate(tagged, request)
    return render(request, 'questions/tag.html', {'page': page, 'tag_name': tag_name})


def question(request, question_id):
    found = [q for q in QUESTIONS if q['id'] == question_id]
    if not found:
        raise Http404('No such question')
    page = paginate(ANSWERS, request, per_page=5)
    return render(request, 'questions/question.html', {'question': found[0], 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
