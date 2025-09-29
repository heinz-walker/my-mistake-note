import csv
import io
import json
import random
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, F, FloatField
from django.db.models.functions import TruncDay
from django.db.models.expressions import ExpressionWrapper
from fuzzywuzzy import fuzz
from django.db import transaction

from .models import Question, UserAnswer, Exam, Category, Tag
from .forms import QuestionForm, AnswerForm, QuizSelectionForm


def dashboard(request):
    # 전체 정답률 계산
    total_answers = UserAnswer.objects.count()
    correct_answers = UserAnswer.objects.filter(is_correct=True).count()
    overall_accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0

    # 일별 정답률 추이 (그래프용 데이터)
    daily_stats = UserAnswer.objects.annotate(
        day=TruncDay('submitted_at')
    ).values('day').annotate(
        correct=Count('id', filter=Q(is_correct=True)),
        total=Count('id')
    ).order_by('day')

    # Chart.js가 사용할 수 있는 형태로 데이터 가공
    daily_accuracy_data = {
        "labels": [stat['day'].strftime('%m-%d') for stat in daily_stats],
        "data": [(stat['correct'] / stat['total'] * 100) for stat in daily_stats]
    }

    # 가장 많이 틀린 카테고리 TOP 5 (그래프용 데이터)
    weak_categories = UserAnswer.objects.filter(is_correct=False) \
                          .values('question__category__name') \
                          .annotate(wrong_count=Count('id')) \
                          .order_by('-wrong_count')[:5]

    weak_categories_data = {
        "labels": [cat['question__category__name'] for cat in weak_categories],
        "data": [cat['wrong_count'] for cat in weak_categories]
    }

    # 가장 많이 틀린 태그 TOP 5 (그래프용 데이터)
    weak_tags = UserAnswer.objects.filter(is_correct=False) \
                    .values('question__tags__name') \
                    .annotate(wrong_count=Count('id')) \
                    .order_by('-wrong_count')[:5]

    weak_tags_data = {
        "labels": [tag['question__tags__name'] for tag in weak_tags],
        "data": [tag['wrong_count'] for tag in weak_tags]
    }

    context = {
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'overall_accuracy': overall_accuracy,
        'daily_accuracy_data': daily_accuracy_data,
        'weak_categories_data': weak_categories_data,
        'weak_tags_data': weak_tags_data,
    }
    return render(request, 'mistake_note/dashboard.html', context)
# 홈 화면
def home(request):
    recent_questions = Question.objects.all().order_by('-created_at')[:5]
    context = {'recent_questions': recent_questions}
    return render(request, 'mistake_note/index.html', context)


# 시험별 카테고리 API
def category_by_exam(request, exam_id):
    categories = list(Category.objects.filter(exam_id=exam_id).values('id', 'name'))
    return JsonResponse(categories, safe=False)


# 답안 정규화 함수
def normalize_answer(answer_string):
    return sorted([part.strip() for part in answer_string.split(',')])


# 문제 추가 및 CSV 가져오기
def add_question_page(request):
    if request.method == 'POST':
        if 'import_csv' in request.POST:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, '파일을 업로드해주세요.')
                return redirect('mistake_note:add_question_page')

            # 인코딩 오류 방지를 위해 utf-8-sig로 디코딩
            data_set = csv_file.read().decode('utf-8-sig').splitlines()

            # 👇 CSV 대신 TSV를 사용하도록 delimiter='\t' 옵션 추가
            csv_reader = csv.DictReader(data_set, delimiter='\t')

            imported_count = 0
            errors = []

            try:
                with transaction.atomic():
                    for row in csv_reader:
                        exam_name = row.get('exam')
                        category_name = row.get('category')

                        if not exam_name or not category_name:
                            errors.append(f"오류: 'exam' 또는 'category' 필드가 비어있는 행이 있습니다.")
                            continue

                        exam, created_exam = Exam.objects.get_or_create(name=exam_name)
                        category, created_category = Category.objects.get_or_create(exam=exam, name=category_name)

                        question_data = {
                            'type': row.get('type'),
                            'exam': exam,
                            'category': category,
                            'content': row.get('content'),
                            'passage': row.get('passage'),
                            'correct_answer': row.get('correct_answer'),
                            'options': row.get('options'),
                            'explanation': row.get('explanation'),
                        }

                        form = QuestionForm(question_data)
                        if form.is_valid():
                            form.save()
                            imported_count += 1
                        else:
                            errors.append(f"문제: {row.get('content')} - 오류: {form.errors.as_text()}")

                if errors:
                    for error_msg in errors:
                        messages.error(request, error_msg)
                    messages.warning(request, f"{imported_count}개의 문제를 성공적으로 가져왔지만, {len(errors)}개의 문제가 실패했습니다.")
                else:
                    messages.success(request, f"{imported_count}개의 문제를 성공적으로 가져왔습니다.")

            except Exception as e:
                messages.error(request, f"파일 처리 중 오류가 발생했습니다: {e}")

            return redirect('mistake_note:add_question_page')
        else:
            form = QuestionForm(request.POST, request.FILES)
            if form.is_valid():
                question = form.save(commit=False)
                options_list = [v for k, v in request.POST.items() if k.startswith('option_') and v]
                question.options = ','.join(options_list)
                question.save()

                new_tags_str = form.cleaned_data.get('new_tags', '')
                if new_tags_str:
                    tag_names = [name.strip() for name in new_tags_str.split(',') if name.strip()]
                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        question.tags.add(tag)

                form.save_m2m()

                messages.success(request, '문제가 성공적으로 추가되었습니다.')
                return redirect('mistake_note:question_list')
            else:
                return render(request, 'mistake_note/add_question.html', {'form': form})
    else:
        form = QuestionForm()
    return render(request, 'mistake_note/add_question.html', {'form': form})


# 문제 목록
def question_list(request):
    questions = Question.objects.all().order_by('-created_at')
    return render(request, 'mistake_note/question_list.html', {'questions': questions})


# 문제 상세 (단일 문제 풀이)
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)

    # POST 요청 (답안 제출) 처리
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_answer = data.get('user_answer', "")
        except json.JSONDecodeError:
            user_answer = request.POST.get('submitted_answer', "")

        is_correct = False
        if question.type == 'MA':
            is_correct = (normalize_answer(user_answer) == normalize_answer(question.correct_answer))
        elif question.type == 'SA':
            similarity_score = fuzz.ratio(user_answer.strip(), question.correct_answer.strip())
            is_correct = similarity_score >= 85
        else:  # MCQ
            is_correct = (user_answer.strip() == question.correct_answer.strip())

        UserAnswer.objects.create(question=question, submitted_answer=user_answer, is_correct=is_correct)
        return JsonResponse({'status': 'success', 'is_correct': is_correct})

    # GET 요청 (페이지 표시) 처리
    options = [opt.strip() for opt in question.options.split(',') if opt]
    random.shuffle(options)

    alphabet = "abcdefghijklmnopqrstuvwxyz"
    options_with_labels = [{'label': alphabet[i], 'text': opt} for i, opt in enumerate(options)]

    next_question = Question.objects.filter(id__gt=pk).order_by('id').first()
    next_question_pk = next_question.id if next_question else None

    context = {
        'question': question,
        'options_with_labels': options_with_labels,
        'next_question_pk': next_question_pk,
    }
    return render(request, 'mistake_note/question_detail.html', context)


# 문제 결과
@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempt = get_object_or_404(QuizAttempt, user=request.user, quiz=quiz)
    questions = quiz.questions.all()

    results = []
    correct_answers_count = 0
    total_questions_count = questions.count()

    for question in questions:
        user_answers = attempt.answered.filter(question=question)
        correct_answers = question.answers.filter(is_correct=True)

        is_question_correct = set(user_answers) == set(correct_answers)

        if is_question_correct:
            correct_answers_count += 1

        results.append({
            'question': question,
            'user_answers': user_answers,
            'correct_answers': correct_answers,
            'is_correct': is_question_correct,
        })

    score = (correct_answers_count / total_questions_count) * 100 if total_questions_count > 0 else 0

    context = {
        'quiz': quiz,
        'results': results,
        'score': score,
        'correct_answers_count': correct_answers_count,
        'total_questions_count': total_questions_count,
    }

    return render(request, 'mistake_note/quiz_result.html', context)


# 퀴즈 선택
def quiz_select(request):
    total_questions_count = Question.objects.count()
    questions_queryset = Question.objects.all()

    if request.method == 'POST':
        form = QuizSelectionForm(request.POST)
        if form.is_valid():
            exam_name = form.cleaned_data.get('exam')
            mode = form.cleaned_data.get('mode')
            count = form.cleaned_data.get('count')

            # 모든 문제 선택
            if mode == 'all':
                questions_queryset = questions_queryset.order_by('?')
            # 많이 틀린 문제
            elif mode == 'wrong':
                questions_queryset = questions_queryset.order_by('-incorrect_count', '?')
            # 많이 안 풀어본 문제
            elif mode == 'unsolved':
                questions_queryset = questions_queryset.order_by('solved_count', '?')
            # 객관식, 주관식, 복수정답 필터링
            else:
                questions_queryset = questions_queryset.filter(type=mode).order_by('?')

            # 시험 종류 필터링
            if exam_name:
                questions_queryset = questions_queryset.filter(exam__name=exam_name)

            # 필요한 문제 개수만큼 슬라이싱
            questions_to_quiz = questions_queryset[:count]
            question_ids = [q.id for q in questions_to_quiz]

            # 세션에 퀴즈 정보 저장
            request.session['quiz_questions'] = question_ids
            request.session['quiz_score'] = 0
            request.session['current_question_index'] = 0
            request.session['quiz_answers'] = []
            return redirect('mistake_note:quiz_take')
    else:
        form = QuizSelectionForm()

    context = {
        'form': form,
        'total_questions': total_questions_count
    }
    return render(request, 'mistake_note/quiz_select.html', context)

# 퀴즈 풀기 (페이지 표시)
def quiz_take(request):
    question_ids = request.session.get('quiz_questions', [])
    current_index = request.session.get('current_question_index', 0)

    if current_index >= len(question_ids):
        return redirect('mistake_note:quiz_summary')

    question_id = question_ids[current_index]
    question = get_object_or_404(Question, pk=question_id)

    options = [opt.strip() for opt in question.options.split(',') if opt]
    random.shuffle(options)

    alphabet = "abcdefghijklmnopqrstuvwxyz"
    options_with_labels = [{'label': alphabet[i], 'text': opt} for i, opt in enumerate(options)]

    is_last_question = (current_index + 1) >= len(question_ids)

    context = {
        'question': question,
        'options_with_labels': options_with_labels,
        'is_last_question': is_last_question,
        'current_index': current_index + 1,
        'total_questions': len(question_ids),
    }

    return render(request, 'mistake_note/quiz_take.html', context)


# 퀴즈 답안 기록 API
@require_POST
def record_quiz_answer(request):
    try:
        data = json.loads(request.body)
        user_answer = data.get('user_answer', "")
        question_id = data.get('question_id')

        with transaction.atomic():
            question = get_object_or_404(Question.objects.select_for_update(), pk=question_id)
            is_correct = False

            if question.type == 'SA':  # 주관식
                correct_answer = question.correct_answer.strip().lower()
                user_answer_normalized = user_answer.strip().lower()

                # fuzzywuzzy를 사용해 85점 이상이면 정답으로 처리
                if fuzz.ratio(correct_answer, user_answer_normalized) >= 85:
                    is_correct = True

            else:  # 객관식(MCQ) 및 복수정답(MA)
                # 답안을 정규화하여 비교
                correct_answers_list = normalize_answer(question.correct_answer)
                user_answers_list = normalize_answer(user_answer)

                if correct_answers_list == user_answers_list:
                    is_correct = True

            # 풀이 횟수 및 정답 횟수 업데이트
            if is_correct:
                question.correct_count += 1
            question.solved_count += 1
            question.save()

            UserAnswer.objects.create(
                question=question,
                submitted_answer=user_answer,
                is_correct=is_correct,
                quiz_mode=True
            )

        # 👇 아래 코드를 추가하여 세션의 인덱스를 업데이트합니다.
        current_index = request.session.get('current_question_index', 0)
        request.session['current_question_index'] = current_index + 1

        # 세션에 답안 정보도 추가하여 결과 페이지에 사용
        if 'quiz_answers' not in request.session:
            request.session['quiz_answers'] = []
        request.session['quiz_answers'].append({
            'question_id': question.id,
            'is_correct': is_correct,
            'submitted_answer': user_answer
        })

        # 퀴즈 점수 업데이트
        if is_correct:
            request.session['quiz_score'] = request.session.get('quiz_score', 0) + 1

        return JsonResponse({'status': 'success', 'is_correct': is_correct})
    except Exception as e:
        print(f"record_quiz_answer 함수에서 오류 발생: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# 퀴즈 결과 요약
def quiz_summary(request):
    # 세션에서 퀴즈 정보 가져오기
    question_ids = request.session.get('quiz_questions', [])
    quiz_answers = request.session.get('quiz_answers', [])
    score = request.session.get('quiz_score', 0)

    total_questions = len(question_ids)

    # 틀린 문제 데이터 준비
    incorrect_questions_data = []
    for answer_data in quiz_answers:
        if not answer_data['is_correct']:
            question = get_object_or_404(Question, pk=answer_data['question_id'])
            incorrect_questions_data.append({
                'question': question,
                'submitted_answer': answer_data['submitted_answer']
            })

    # 퀴즈 세션 정보 삭제 (선택 사항)
    # del request.session['quiz_questions']
    # del request.session['current_question_index']
    # del request.session['quiz_answers']
    # del request.session['quiz_score']

    context = {
        'score': score,
        'total_questions': total_questions,
        'incorrect_questions_data': incorrect_questions_data,
    }

    return render(request, 'mistake_note/quiz_summary.html', context)


def get_question_count(request):
    exam_name = request.GET.get('exam')
    mode = request.GET.get('mode')

    questions_queryset = Question.objects.all()

    if exam_name:
        questions_queryset = questions_queryset.filter(exam__name=exam_name)

    if mode == 'all':
        pass
    elif mode == 'wrong':
        questions_queryset = questions_queryset.filter(incorrect_count__gt=0)
    elif mode == 'unsolved':
        questions_queryset = questions_queryset.filter(solved_count=0)
    else:
        questions_queryset = questions_queryset.filter(type=mode)

    count = questions_queryset.count()
    return JsonResponse({'count': count})

@require_POST
def validate_question_api(request):
    """
    기존 응답 포맷을 유지하면서 안정성만 보강:
    - JSON 본문 검증
    - 필수 필드 확인
    - 타임아웃 적용
    - 빈 응답/형식 불일치 방어
    - 내부 예외 메시지 노출 최소화
    응답 예:
      { "status": "success", "feedback": "..." }
      { "status": "error", "message": "..." }
    """
    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "잘못된 요청 본문(JSON 아님)"}, status=400)

        question_content = (data.get("content") or "").strip()
        question_options = (data.get("options") or "").strip()
        question_answer  = (data.get("answer")  or "").strip()

        if not question_content or not question_answer:
            return JsonResponse({"status": "error", "message": "content/answer는 필수입니다."}, status=400)

        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            return JsonResponse({"status": "error", "message": "서버에 GEMINI_API_KEY가 설정되지 않았습니다."}, status=500)

        model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        timeout = int(getattr(settings, "GEMINI_TIMEOUT_SEC", 12))

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        prompt = (
            "당신은 시험문항 검토자입니다. 아래 문항의 '명확성/정답 유일성/선택지 타당성'을 간결하게 검토하고 "
            "두 항목으로만 출력하세요: 1) 유효성, 2) 개선 제안.\n"
            f"---\n- 문제 내용: {question_content}\n- 선택지: {question_options}\n- 정답: {question_answer}\n---"
        )

        resp = model.generate_content(prompt, request_options={"timeout": timeout})

        # SDK 버전별 응답 추출 (안전)
        text = getattr(resp, "text", None)
        if not text and getattr(resp, "candidates", None):
            parts = getattr(resp.candidates[0], "content", {}).get("parts", [])
            text = "".join(getattr(p, "text", "") for p in parts)

        if not text or not str(text).strip():
            return JsonResponse({"status": "error", "message": "AI 응답이 비어 있습니다."}, status=502)

        return JsonResponse({"status": "success", "feedback": str(text).strip()})
    except Exception:
        # 내부 에러는 상세 노출하지 않음 (보안/안정성)
        return JsonResponse({"status": "error", "message": "AI 검증 중 오류가 발생했습니다."}, status=502)

#test
