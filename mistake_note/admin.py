# mistake_note/admin.py

from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from django_summernote.widgets import SummernoteWidget  # 👈 1. SummernoteWidget import 추가
from django.db import models  # 👈 2. models import 추가
from .models import Question, UserAnswer, Exam, Category, Tag
from django.db.models import Count, Max, Q
from .forms import QuestionAdminForm

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam')
    list_filter = ('exam',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(SummernoteModelAdmin):
    list_display = (
        'id', 'type', 'exam', 'category', 'get_tags', 'correct_count_display', 'attempt_count_display',
        'last_attempt_date_display'
    )
    list_filter = ('type', 'exam', 'category', 'tags')
    search_fields = ('content', 'passage')
    inlines = [UserAnswerInline]

    # 👇 3. formfield_overrides를 사용하여 모든 TextField를 SummernoteWidget으로 강제 변경
    form = QuestionAdminForm  # 👈 Tell the admin to use this form

    change_form_template = 'admin/mistake_note/question/change_form.html'


    class Media:
        css = {
            'all': ('mistake_note/css/admin_custom.css',)
        }
    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    get_tags.short_description = '태그'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            correct_count_annotated=Count('useranswer', filter=Q(useranswer__is_correct=True)),
            attempt_count_annotated=Count('useranswer'),
            last_attempt_date_annotated=Max('useranswer__submitted_at')
        )
        return queryset

    def correct_count_display(self, obj):
        return obj.correct_count_annotated

    correct_count_display.short_description = '맞춘 횟수'

    def attempt_count_display(self, obj):
        return obj.attempt_count_annotated

    attempt_count_display.short_description = '시도 횟수'

    def last_attempt_date_display(self, obj):
        return obj.last_attempt_date_annotated if obj.last_attempt_date_annotated else '기록 없음'

    last_attempt_date_display.short_description = '최근 풀이일'


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'submitted_answer', 'is_correct', 'submitted_at')
    list_filter = ('is_correct',)