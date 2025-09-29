# mistake_note/urls.py

from django.urls import path
from . import views

app_name = 'mistake_note'

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_question_page, name="add_question_page"),
    path("list/", views.question_list, name="question_list"),

    # ✅ 파라미터 누락/오타 수정
    path("question/<int:pk>/", views.question_detail, name="question_detail"),
    path("question/<int:pk>/result/", views.question_result, name="question_result"),

    path("quiz/", views.quiz_select, name="quiz_select"),
    path("quiz/take/", views.quiz_take, name="quiz_take"),
    path("quiz/summary/", views.quiz_summary, name="quiz_summary"),

    # ✅ 파라미터 누락/오타 수정
    path("api/categories/<int:exam_id>/", views.category_by_exam, name="category_by_exam"),

    path("quiz/record_answer/", views.record_quiz_answer, name="record_quiz_answer"),
    path("api/quiz/count/", views.get_question_count, name="get_question_count"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/validate-question/", views.validate_question_api, name="validate_question_api"),
]