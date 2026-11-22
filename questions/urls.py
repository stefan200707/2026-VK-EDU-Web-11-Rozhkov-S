from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    # AJAX
    path('question/vote/', views.question_vote, name='question_vote'),
    path('answer/vote/', views.answer_vote, name='answer_vote'),
    path('answer/correct/', views.answer_correct, name='answer_correct'),
]
