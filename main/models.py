import qrcode
from PIL import Image, ImageDraw
from io import BytesIO
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.files import File


# Create your models here.


class User(AbstractUser):
    pass_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    organization = models.CharField(max_length=750)
    position = models.CharField(max_length=500)
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name_plural = 'Foydalanuvchilar'


class Module(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nomi')
    AT = models.CharField(max_length=20, verbose_name="Qisqa nomi")
    no_1 = models.IntegerField(verbose_name="1-Raqami", null=True, blank=True)
    no_2 = models.IntegerField(verbose_name="2-Raqami", null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = 'Kategoriyalar'


class Variant(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    name = models.CharField(max_length=70)
    description = models.TextField(max_length=70, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, verbose_name='variant')
    name = models.TextField(verbose_name='Nomi')
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = 'Savollar'


class Answers(models.Model):
    STATUS = (
        ('Correct', 'Correct'),
        ('Mistake', 'Mistake'),
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Savol')
    answer = models.TextField(verbose_name='variant')
    status = models.CharField(max_length=50, choices=STATUS, default="Mistake", verbose_name='Holati')
    ball = models.CharField(max_length=150, default=0, verbose_name='Ball')
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.answer

    class Meta:
        verbose_name_plural = 'Variantlar'


class Group(models.Model):
    name = models.CharField(max_length=200)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True)
    users = models.ManyToManyField(User)
    start_date = models.DateField()
    finish_date = models.DateField()
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Exam(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Guruh', null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, verbose_name='Variant')
    user = models.ManyToManyField(User, verbose_name='Ishtirokchi')
    start_date = models.DateTimeField(verbose_name='Ochilish sanasi')
    finish_date = models.DateTimeField(verbose_name='Yopilish sanasi')
    duration = models.IntegerField(verbose_name='Davomiyligi', help_text="Imtihon davomiyligi minutda kiritilsin!")
    is_retry = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Imtihonlar'

    # def __str__(self):
    #     return self.group.name

    @property
    def total_passed_students(self):
        result = Operations.objects.filter(exam_id=self.id, status="Passed").count()
        return result

    @property
    def total_users(self):
        result = Exam.objects.get(id=self.id).user.all().count()

        return result

    @property
    def total_failed_students(self):
        result = Operations.objects.filter(exam_id=self.id, status='Fail').count()
        return result

    @property
    def total_missed_students(self):
        result = Operations.objects.filter(exam_id=self.id, status='not_submit').count()
        return result


class Operations(models.Model):
    STATUS = (
        ('Passed', 'Passed'),
        ('Fail', 'Fail'),
        ('not_submit', 'Did not submit'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)
    correct_answer = models.IntegerField(null=True, blank=True)
    percent = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    total_ball = models.IntegerField(null=True, blank=True)
    number_1 = models.IntegerField(null=True, blank=True)
    number_2 = models.IntegerField(null=True, blank=True)
    qr_image = models.ImageField(upload_to='qr_code/', null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS, default='not_submit', verbose_name='Holati')
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    @property
    def total_balls(self):
        total_balls = 0
        questions = Question.objects.filter(variant=self.variant.id)
        for question in questions:
            answers = Answers.objects.filter(question=question.id)
            for answer in answers:
                total_balls += int(answer.ball)

        return total_balls

    @property
    def operationitem(self):
        return self.operationitem_set.all()


class OperationItem(models.Model):
    operation = models.ForeignKey(Operations, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answers, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)


class UserPayment(models.Model):
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.BooleanField()
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
