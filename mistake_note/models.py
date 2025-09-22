from django.db import models

class Exam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Category(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    class Meta:
        verbose_name_plural = 'Categories'
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Question(models.Model):
    TYPE_CHOICES = [
        ('MCQ', '객관식'),
        ('SA', '주관식'),
        ('MA', '복수정답'),
    ]

    type = models.CharField(max_length=3, choices=TYPE_CHOICES, default='MCQ')
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    tags = models.ManyToManyField(Tag, blank=True)

    content = models.TextField(verbose_name='문제 내용')  # TextField로 변경
    passage = models.TextField(verbose_name='지문', blank=True, null=True)  # TextField로 변경

    solved_count = models.IntegerField(default=0, verbose_name="풀이 횟수")
    incorrect_count = models.IntegerField(default=0, verbose_name="오답 횟수")
    correct_count = models.IntegerField(default=0, verbose_name="맞춘 횟수")

    correct_answer = models.CharField(max_length=200)
    options = models.TextField(blank=True, help_text="객관식/복수 정답 보기를 콤마(,)로 구분하여 입력하세요.")
    explanation = models.TextField(verbose_name='해설', blank=True, null=True)  # TextField로 변경
    image = models.ImageField(upload_to='questions/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        exam_name = self.exam.name if self.exam else "미분류 시험"
        category_name = self.category.name if self.category else "미분류 카테고리"
        return f'{exam_name} - {category_name} - 문제#{self.id}'

class UserAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    submitted_answer = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    quiz_mode = models.BooleanField(default=True)

    def __str__(self):
        return f"문제 #{self.question.id}에 대한 답변"