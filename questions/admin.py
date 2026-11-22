from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class FirstLetterFilter(admin.SimpleListFilter):
    title = 'Первая буква'
    parameter_name = 'letter'

    def lookups(self, request, model_admin):
        return [(letter, letter.upper()) for letter in 'abcdefghijklmnopqrstuvwxyz']

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__istartswith=self.value())
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    list_filter = [FirstLetterFilter]


class AuthorIdWidget(ForeignKeyRawIdWidget):
    # поле id с кнопкой поиска, но без подписи с именем:
    # обычный raw_id-виджет делает отдельный запрос за пользователем для каждого ответа в инлайне (N+1)
    def label_and_url_for_value(self, value):
        return '', ''


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ['author', 'text', 'is_correct', 'rating', 'created_at']
    raw_id_fields = ['author']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            kwargs['widget'] = AuthorIdWidget(db_field.remote_field, self.admin_site)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'rating', 'answers_count', 'created_at']
    list_select_related = ['author']
    search_fields = ['title']
    list_filter = ['created_at']
    raw_id_fields = ['author', 'tags']
    inlines = [AnswerInline]
    show_full_result_count = False   # не считать COUNT(*) по всей таблице лишний раз


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'author', 'is_correct', 'rating', 'created_at']
    list_select_related = ['question', 'author']
    search_fields = ['question__title']
    list_filter = ['is_correct', 'created_at']
    raw_id_fields = ['question', 'author']
    show_full_result_count = False


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'question', 'value', 'created_at']
    list_select_related = ['user', 'question']
    search_fields = ['user__username']
    list_filter = ['value', 'created_at']
    raw_id_fields = ['user', 'question']
    show_full_result_count = False


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'answer', 'value', 'created_at']
    list_select_related = ['user', 'answer']
    search_fields = ['user__username']
    list_filter = ['value', 'created_at']
    raw_id_fields = ['user', 'answer']
    show_full_result_count = False
