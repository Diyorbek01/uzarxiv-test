# Create your views here.
import os
import random
from datetime import timedelta

from django.http.response import FileResponse
from django.template.loader import get_template
from django.shortcuts import render
from django.utils.timezone import now
from rest_framework import viewsets, authentication, permissions
from rest_framework.authtoken import views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from main.serializers import *

from django.http import HttpResponse

from django.template.loader import get_template
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, legal, elevenSeventeen


def index(request):
    return render(request, "index.html")


def certificate(request, id):
    operation = Operations.objects.get(id=id)
    en_month_create = operation.create_at.strftime("%B")
    en_month_start = operation.exam.group.start_date.strftime("%B")
    en_month_finish = operation.exam.group.finish_date.strftime("%B")
    date_months = {
        'January': "Yanvar",
        'February': "Fevral",
        'March': "Mart",
        'April': "Aprel",
        'May': "May",
        'June': "Iyun",
        'July': "Iyul",
        'August': "Avgust",
        'September': "Sentabr",
        'October': "Oktabr",
        'November': "Noyabr",
        'December': "Dekabr",
    }
    uz_month_create = date_months[en_month_create]
    uz_month_start = date_months[en_month_start]
    uz_month_finish = date_months[en_month_finish]

    start_date = operation.exam.group.start_date.strftime("%d %B, %Y").replace(en_month_start, uz_month_start)
    finish_date = operation.exam.group.finish_date.strftime("%d %B, %Y").replace(en_month_finish, uz_month_finish)
    create_at = operation.create_at.strftime("%d %B, %Y").replace(en_month_create, uz_month_create)

    if operation:
        url = request.build_absolute_uri('/')[:-1]
        img = qrcode.make(f"{url}/certificate/{operation.id}")
        type(img)  # qrcode.image.pil.PilImage
        img.save(os.path.abspath("static/qr_code.png"))

        image = os.path.abspath("static/qr_code.png")
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=elevenSeventeen)

        can.drawCentredString(400, 350, f"{operation.variant.module.AT} Nº{operation.number_1}", mode=0)
        can.drawString(320, 290,
                       f'{start_date} yil dan      {finish_date} yil gacha')
        if 6 > len(operation.variant.module.name.split()) >= 3:
            can.drawString(250, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus ')
            can.drawString(350, 250, "o’quv kursini muvaffaqiyatli tamomladi")

        elif 9 > len(operation.variant.module.name.split()) >= 6:
            can.drawString(230, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus o’quv kursining')
            can.drawString(350, 250, "muvaffaqiyatli tamomladi")

        elif 11 > len(operation.variant.module.name.split()) >= 8:
            can.drawString(150, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus')
            can.drawString(350, 250, "o’quv kursini muvaffaqiyatli tamomladi")
        elif 14 > len(operation.variant.module.name.split()) >= 8:
            can.drawString(130, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik')
            can.drawString(350, 250, "maxsus o’quv kursini muvaffaqiyatli tamomladi")
        elif 16 > len(operation.variant.module.name.split()) >= 11:
            can.drawString(150, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik')
            can.drawString(350, 250, "maxsus o’quv kursini muvaffaqiyatli tamomladi")

        else:
            can.drawString(280, 270,
                           f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus o’quv kursini')
            can.drawString(350, 250, "muvaffaqiyatli tamomladi")
        can.drawString(300, 120, f'{create_at} yil')
        can.drawString(480, 120, f"Qayd raqami: {operation.number_2}")
        can.drawInlineImage(image, 640, 130, width=70, height=80)
        can.setFontSize(18)
        # can.setFillColor('red')
        name_length = len(operation.user.last_name)+ len(operation.user.first_name)
        if name_length in range(0,27):
            can.drawCentredString(400, 320, f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                mode=2,
                                charSpace=6)
        elif name_length in range(27,30):
            can.drawCentredString(418, 320, f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                mode=2,
                                charSpace=6)
        elif name_length in range(30,33):
            can.drawCentredString(435, 320, f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                mode=2,
                                charSpace=6)
        else:
            can.drawCentredString(430, 320,
                                  f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                  mode=2,
                                  charSpace=4)
        # rgb(31, 48, 108)
        can.save()

        # move to the beginning of the StringIO buffer
        packet.seek(0)

        # create a new PDF with Reportlab
        new_pdf = PdfFileReader(packet)
        # read your existing PDF
        existing_pdf = PdfFileReader(open(os.path.abspath("static/sertifikat.pdf"), "rb"))
        output = PdfFileWriter()
        # add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        # finally, write "output" to a real file
        outputStream = open(os.path.abspath("static/certification.pdf"), "wb")
        output.write(outputStream)
        outputStream.close()

        pdf_file = os.path.abspath("static/certification.pdf")
        with open(pdf_file, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline;filename=certification.pdf'
            return response
        pdf.closed


class UserViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['post'], detail=False)
    def post(self, request):
        data = request.data
        serializer_class = UserSerializer(data=data)
        if serializer_class.is_valid():
            serializer_class.is_valid(raise_exception=True)
            serializer_class.save()
            return Response(serializer_class.data, 201)
        return Response(serializer_class.errors)

    @action(methods=['get'], detail=False)
    def get(self, request):
        users = User.objects.filter(is_superuser=False).order_by("-id")
        serializer_class = UserSerializer(users, many=True)
        return Response(serializer_class.data, status=200)

    @action(methods=['post'], detail=False)
    def add_admin(self, request):
        user_id = request.data['user_id']
        user = User.objects.get(id=user_id)
        user.is_superuser = True
        user.save()
        serializer_class = UserSerializer(user)
        return Response(serializer_class.data, 201)

    @action(methods=['get'], detail=False)
    def filter_pass(self, request):
        data = request.GET
        pass_number = data['pass_number']
        user = User.objects.get(pass_number=pass_number)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def filter_name(self, request):
        data = request.GET
        first_name = data.get('first_name', None)
        last_name = data.get('last_name', None)
        user = User.objects.filter(Q(first_name=first_name) | Q(last_name=last_name))
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data)


class ModuleViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer


class VariantViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Variant.objects.all()
    serializer_class = VairantSerializer


class GroupViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(methods=['post'], detail=False)
    def post(self, request):
        data = request.data
        name = data['name']
        start_date = data['start_date']
        finish_date = data['finish_date']
        module = data['module']
        users = data['users']
        group = Group.objects.create(
            name=name,
            start_date=start_date,
            finish_date=finish_date,
            module_id=module,
        )
        for i in users:
            group.users.add(i)

        for i in group.users.all():
            payment = UserPayment.objects.create(group_id=group.id, user_id=i.id, status=False)
        return Response("Create", 201)

    @action(methods=['get'], detail=False)
    def get(self, request):
        groups = Group.objects.all()
        result = []
        gr_users = []
        for i in groups:
            gr_users.append([s.id for s in i.users.all()])
            result.append({
                "id": i.id,
                "name": i.name,
                "start_date": i.start_date,
                "finish_date": i.finish_date,
                "module_id": i.module_id,
            })
            exam_users = []
            passed_users = []
            result[0]['exam_users']: len(exam_users)
            for i in Exam.objects.filter(group_id=i.id):
                for o in Operations.objects.filter(exam_id=i.id):
                    if o.user_id in gr_users[0] and o.user_id not in passed_users:
                        operation = Operations.objects.filter(user_id=o.user_id, status="Passed")
                        if operation:
                            passed_users.append(operation.last().user_id)
                    if o.user_id in gr_users[0] and o.user_id not in exam_users:
                        exam_users.append(o.user_id)
        return Response(result, 200)

    @action(methods=['post'], detail=False)
    def add(self, request):
        data = request.data
        result = Group.objects.get(id=int(data['group_id']))

        for i in data['user_id']:
            result.users.add(i)
            result.save()
            payment = UserPayment.objects.create(
                user_id=i,
                group_id=data['group_id'],
                status=False
            )
        return Response("Added", status=201)

    @action(methods=['post'], detail=False)
    def remove_user(self, request):
        data = request.data
        group_id = data['group_id']
        users = data['user_id']
        group = Group.objects.get(id=group_id)
        for i in group.users.all():
            if i.id in users:
                group.users.remove(i)
        ser = GroupSerializer(group)
        return Response(ser.data, 200)

    @action(methods=['get'], detail=False)
    def filter(self, request):
        data = request.GET
        group = Group.objects.get(id=data['group_id'])
        result = group.users.all()
        res = []
        for i in result:
            res.append({
                'id': i.id,
                'username': i.username,
                'firs_name': i.first_name,
                'last_name': i.last_name,
                'organization': i.organization,
                'position': i.position,
            })

        return Response(res, status=200)

    @action(methods=['get'], detail=False)
    def get_details(self, request):
        group_id = request.GET['group_id']
        group = User.objects.raw('''SELECT user.id, payment.status
    FROM main_group_users as gr_rel 
    LEFT JOIN main_user as user on gr_rel.user_id=user.id
    LEFT JOIN main_userpayment as payment on payment.user_id = gr_rel.user_id AND payment.group_id=gr_rel.group_id
    WHERE gr_rel.group_id = %s
    ''', [group_id])
        check = []
        payment = []
        for i in group:
            if i.status != None and i.id not in check:
                check.append(i.id)
                payment.append({
                    "user": {
                        "id": i.id,
                        "first_name": i.first_name,
                        "last_name": i.last_name,
                        "organization": i.organization,
                        "position": i.position,
                        "pass_number": i.pass_number,
                        "username": i.username,
                    },

                    "payment_status": i.status
                })
            elif i.status == None:
                payment.append({
                    "user": {
                        "id": i.id,
                        "first_name": i.first_name,
                        "last_name": i.last_name,
                        "organization": i.organization,
                        "position": i.position,
                        "pass_number": i.pass_number,
                        "username": i.username,
                    },
                    "payment_status": False
                })

        exam = Exam.objects.filter(group_id=group_id).last()
        for i in Group.objects.get(id=group_id).users.all():
            for a in payment:
                if exam:
                    operation = Operations.objects.filter(group_id=group_id, user_id=i.id).last()
                    if operation and a['user']['id'] == operation.user.id:
                        a['exam_status'] = operation.status
                        a['operation_id'] = operation.id

        groups = Group.objects.get(id=group_id)
        if exam:
            payment.insert(0, {
                "group": {
                    "name": groups.name,
                    "module": groups.module.name,
                    "module_id": groups.module.id,
                    "start_date": groups.start_date,
                    "finish_date": groups.finish_date,
                    "total_passed_students": 0,
                    "total_users": exam.total_users,
                    "total_failed_students": exam.total_failed_students,
                    "total_missed_students": exam.total_missed_students,
                    'exams': []
                }})
        else:
            payment.insert(0, {
                "group": {
                    "name": groups.name,
                    "module": groups.module.name,
                    "module_id": groups.module.id,
                    "start_date": groups.start_date,
                    "finish_date": groups.finish_date,
                    'exams': []
                }})
        exams = Exam.objects.filter(group_id=group_id)
        passed_user = 0
        for i in exams:
            passed_user += i.total_passed_students
            payment[0]['group']['exams'].append(
                {
                    'id': i.id,
                    'user': [x.id for x in i.user.all()],
                    'start_date': i.start_date,
                    'finish_date': i.finish_date,
                    'duration': i.duration,
                    'is_retry': i.is_retry,
                    "total_passed_students": i.total_passed_students,
                    "total_users": i.total_users,
                    "total_failed_students": i.total_failed_students,
                    "total_missed_students": i.total_missed_students,
                }
            )
        if passed_user > 0:
            payment[0]['group']['total_passed_students'] += passed_user
        return Response(payment, 200)


class AnsversViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Answers.objects.all()
    serializer_class = AnswerSerializer


class QuestionViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @action(methods=['get'], detail=False)
    def delete(self, request):
        id = request.GET['id']
        answer = Answers.objects.get(id=id).delete()
        return Response("Success", 200)

    @action(methods=['get'], detail=False)
    def delete_question(self, request):
        id = request.GET['id']
        answer = Question.objects.get(id=id).delete()
        return Response("Success", 200)

    @action(methods=['get'], detail=False)
    def get(self, request):
        id = request.GET.get("id", None)
        if id:
            question = Question.objects.filter(id=id)
        else:
            question = Question.objects.all()
        data_list = []
        for i in question:
            if i.variant:
                data = {
                    "id": i.id,
                    "name": i.name,
                    "variant_id": i.variant.id,
                    "variant_name": i.variant.name,
                    "module_id": i.variant.module.id,
                    "module_name": i.variant.module.name,
                    "variants": []

                }
            else:
                data = {
                    "id": i.id,
                    "name": i.name,
                    "variant_id": None,
                    "variant_name": None,
                    "module_id": None,
                    "module_name": None,
                    "variants": []

                }
            data_list.append(data)
            answer = Answers.objects.filter(question=i.id)
            if answer:
                answer_list = []
                for a in answer:
                    result = {
                        "id": a.id,
                        "name": a.answer,
                        "status": a.status,
                        "ball": a.ball,
                    }
                    answer_list.append(result)
                data['variants'] += answer_list

        return Response(data_list, 200)

    @action(methods=['get'], detail=False)
    def get_list(self, request):
        variant_id = request.GET.get('variant_id')
        list_question = list(Question.objects.filter(variant=variant_id))
        number_question = Question.objects.filter(variant=variant_id).count()
        question = random.sample(list_question, number_question)

        data_list = []
        for i in question:
            data = {
                "id": i.id,
                "name": i.name,
                "variant_id": i.variant.id,
                "variant_name": i.variant.name,
                "module_id": i.variant.module.id,
                "module_name": i.variant.module.name,
                "variants": []

            }
            data_list.append(data)
            list_answer = list(Answers.objects.filter(question=i.id))
            number_answer = Answers.objects.filter(question=i.id).count()
            answer = random.sample(list_answer, number_answer)
            if answer:
                answer_list = []
                for a in answer:
                    result = {
                        "id": a.id,
                        "name": a.answer,
                        "status": a.status,
                        "ball": a.ball,
                    }
                    answer_list.append(result)
                data['variants'] += answer_list

        return Response(data_list, 200)

    @action(methods=['get'], detail=False)
    def get_correct_list(self, request):
        variant_id = request.GET.get('variant_id')
        questions = Question.objects.filter(variant=variant_id)
        result = []
        for i in questions:
            answers = Answers.objects.filter(question=i.id, status="Correct")
            if answers:
                serializer = AnswerSerializer(answers, many=True)
                result.append(serializer.data)
        return Response(result, 200)

    @action(methods=['post'], detail=False)
    def update_question(self, request):
        data = request.data
        total_ball = 0
        id = data.get('id')
        name = data.get('name')
        variant = data.get('variant')
        question = Question.objects.get(id=id)
        question.name = name
        question.variant_id = variant
        question.save()
        for v in data.get('variants'):
            answer_id = v.get('id', None)
            name = v.get('name')
            status = v.get('status')
            ball = v.get('ball')
            total_ball += int(ball)
            if type(answer_id) == int:
                answer = Answers.objects.get(id=answer_id)
                answer.answer = name
                answer.status = status
                answer.ball = ball
                answer.question = question
                answer.save()
            elif type(answer_id) == str:
                Answers.objects.create(answer=name, status=status, ball=ball, question=question)
        if total_ball == 0:
            return Response("The amount of points is not enough", 400)
        return Response("Created", 201)

    @action(methods=['post'], detail=False)
    def post(self, request):
        data = request.data
        for i in data:
            total_ball = 0
            name = i.get('name')
            variant = i.get('variant')
            question = Question.objects.create(name=name, variant_id=variant)
            for v in i.get('variants'):
                answer = v.get('name')
                status = v.get('status')
                ball = v.get('ball')
                total_ball += int(ball)
                answer = Answers.objects.create(answer=answer, status=status, ball=ball, question=question)
            if total_ball == 0:
                return Response("The amount of points is not enough", 400)
        return Response("Created", 201)

    @action(methods=['get'], detail=False)
    def filter(self, request):
        data = request.GET
        question = Question.objects.filter(variant=data['variant_id'])
        result = []
        for i in question:
            answers = Answers.objects.filter(question=i.id)

            for a in answers:
                dict = {
                    'id': a.id,
                    "answer": a.answer,
                    "status": a.status,
                    "question": {
                        "id": a.question_id,
                        "name": a.question.name,

                    },
                    "ball": a.ball,
                }
                result.append(dict)
        return Response(result, status=200)

    @action(methods=['get'], detail=False)
    def filter_questions(self, request):
        variant_id = request.GET['variant_id']
        questions = Question.objects.filter(variant=variant_id)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, 200)


class ExamViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Exam.objects.all()
    serializer_class = ExamsSerializer

    @action(methods=['get'], detail=False)
    def get(self, request):
        user_id = request.GET.get("user_id", None)
        exams = Exam.objects.raw('''SELECT id,exam_id from main_exam_user
WHERE user_id = %s''', [user_id])

        operations = Operations.objects.filter(user_id=user_id)
        new_date = now() + timedelta(hours=5)
        exam_ids = []
        for i in operations:
            exam_ids.append(i.exam_id)
        result = []
        for i in exams:
            exam = Exam.objects.filter(id=i.exam_id, start_date__lte=new_date, finish_date__gte=new_date).last()
            if exam and i.exam_id not in exam_ids:
                result.append(exam)
        data = []
        for i in result:
            data.append({
                "id": i.id,
                "group_id": i.group.id,
                "group_name": i.group.name,
                "variant_id": i.variant.id,
                "variant_name": i.variant.name,
                'start_date': i.start_date,
                'finish_date': i.finish_date,
                "duration": i.duration,
                "is_retry": i.is_retry,
            })
        return Response(data, 200)

    @action(methods=['post'], detail=False)
    def edit(self, request):
        id = request.data['id']
        start_date = request.data['start_date']
        finish_date = request.data['finish_date']
        duration = request.data['duration']
        variant = request.data['variant']
        group = request.data['group']
        users = request.data['user']

        exam = Exam.objects.get(id=id)

        exam.start_date = start_date
        exam.finish_date = finish_date
        exam.duration = duration
        exam.variant_id = variant
        exam.group_id = group
        exam.save()

        exam.user.clear()
        for i in users:
            exam.user.add(i)
        exam.save()

        return Response("Updated")


class ExamApiViewset(views.APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Exam.objects.all()
        serializer_class = ExamSerializer(queryset)
        return Response(serializer_class.data)

    def post(self, request):
        group_id = request.data.get('group', None)
        user_id = request.data.get('user', None)
        context = {
            'group': group_id,
            'user': user_id,
        }
        serializer = ExamSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
