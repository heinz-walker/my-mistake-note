from django import forms
from django_summernote.widgets import SummernoteWidget # Summernote 위젯 import
from .models import Question, UserAnswer, Exam, Category, Tag

class QuestionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="태그"
    )

    new_tags = forms.CharField(
        label='새 태그 (쉼표로 구분)',
        required=False,
        help_text='기존 목록에 없는 태그는 여기에 쉼표로 구분하여 입력하세요.'
    )

    class Meta:
        model = Question
        fields = ['exam', 'category', 'type', 'content', 'passage', 'image',
                  'tags', 'new_tags',
                  'correct_answer', 'options', 'explanation']
        labels = {
            'content': '문제',
            'explanation': '해설',
            'passage': '지문',
        }
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'content': SummernoteWidget(),
            'passage': SummernoteWidget(),
            'explanation': SummernoteWidget(),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '정답을 입력하세요'}),
            'options': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': '객관식/복수 정답 보기를 콤마(,)로 구분하여 입력하세요'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'exam' in self.data:
            try:
                exam_id = int(self.data.get('exam'))
                self.fields['category'].queryset = Category.objects.filter(exam_id=exam_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            if self.instance.exam:
                self.fields['category'].queryset = Category.objects.filter(exam=self.instance.exam).order_by('name')

class AnswerForm(forms.Form):
    submitted_answer = forms.CharField(label='내 답안', widget=forms.TextInput(attrs={'class': 'form-control'}))

class QuizSelectionForm(forms.Form):
    EXAM_CHOICES = [('', '모든 시험')] + [(exam.name, exam.name) for exam in Exam.objects.all()]
    MODE_CHOICES = [
        ('all', '모든 문제'),
        ('wrong', '많이 틀린 문제'),
        ('unsolved', '많이 안 풀어본 문제'),
        ('MCQ', '객관식만'),
        ('SA', '주관식만'),
        ('MA', '복수 정답만'),
    ]

    exam = forms.ChoiceField(choices=EXAM_CHOICES, required=False, label='시험 범위',
                             widget=forms.Select(attrs={'class': 'form-select'}))
    mode = forms.ChoiceField(choices=MODE_CHOICES, required=False, label='퀴즈 모드',
                             widget=forms.Select(attrs={'class': 'form-select'}))
    count = forms.IntegerField(min_value=1, initial=10, label='문제 개수',
                               widget=forms.NumberInput(attrs={'class': 'form-control'}))

    from django_summernote.widgets import SummernoteWidget

class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        widgets = {
            'content': SummernoteWidget(),
            'passage': SummernoteWidget(),
            'explanation': SummernoteWidget(),
        }
        fields = '__all__'


