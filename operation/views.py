import os.path
import subprocess
from datetime import timedelta, datetime
from itertools import groupby

import qrcode
import requests
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.utils.timezone import now
from rest_framework import viewsets, authentication, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings import BASE_DIR
from main.models import UserPayment, Group, User, Operations, Module, Exam, Variant, Question, Answers, OperationItem
from main.serializers import QuestionSerializer
from operation.serializers import PaymentStatusSerializer, OperationSerializer, OperationsSerializer, OperaSerializer

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, legal, elevenSeventeen


@api_view(['POST'])
def login(request):
    username = request.data['username']
    password = request.data['password']
    if User.objects.filter(username=username, password=password).exists():
        user_new = User.objects.get(username=username)
        token, created = Token.objects.get_or_create(user=user_new)

        data = {
            "id": user_new.id,
            'token': token.key,
            "is_superuser": user_new.is_superuser,
            "full_name": f"{user_new.first_name} {user_new.last_name}"
        }
        return Response(data, status=200)
    else:
        return Response('User does not exist', status=400)


class PaymentViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserPayment.objects.all()
    serializer_class = PaymentStatusSerializer

    @action(methods=['post'], detail=False)
    def post(self, request):
        data = request.data
        for i in data:
            result = UserPayment.objects.create(
                status=i['status'],
                group_id=i['group'],
                user_id=i['user']
            )
        return Response("Created", status=201)

    @action(methods=['post'], detail=False)
    def update_status(self, request):
        data = request.data
        for i in data:
            result = UserPayment.objects.filter(
                group_id=i['group'],
                user_id=i['user']
            ).last()
            if result != None:
                result.status = i['status']
                result.save()
            else:
                return Response("User or group doesn't exist", 400)
        return Response("Changed", status=201)

    @action(methods=['get'], detail=False)
    def paid(self, request):
        data = request.GET
        result = UserPayment.objects.filter(group=data['group_id'])
        group = Group.objects.get(id=data['group_id'])
        group_user = Group.objects.get(id=data['group_id']).users.all()
        pay_users = []
        group_users = []
        for i in result:
            pay_users.append(i.user.id)
        for i in group_user:
            group_users.append(i.id)
        paid_list = []
        for i in pay_users:
            if i in group_users:
                paid_list.append(i)

        result_list = []
        for i in User.objects.all():
            if i.id in paid_list:
                result_list.append({
                    'id': i.id,
                    'username': i.username,
                    'firs_name': i.first_name,
                    'last_name': i.last_name,
                    'organization': i.organization,
                    'position': i.position,
                    'pass_number': i.pass_number,
                })
        result_list.insert(0, {
            "group": {
                "id": data['group_id'],
                "name": group.name,
                "users": [x.id for x in group.users.all()],
                "start_date": group.start_date,
                "finish_date": group.finish_date,
                "module": group.module.name,
            }
        })
        # serializer = PaymentStatusSerializer(result, many=True)
        return Response(result_list, status=200)

    @action(methods=['get'], detail=False)
    def unpaid(self, request):
        data = request.GET
        pay_user = UserPayment.objects.filter(group=data['group_id'])
        group_user = Group.objects.get(id=data['group_id'])
        pay_user_list = []
        group_user_list = []
        for i in pay_user:
            pay_user_list.append(i.user.id)
        for i in group_user.users.all():
            group_user_list.append(i.id)
        unpaid_user = []
        for i in group_user_list:
            if i not in pay_user_list:
                unpaid_user.append(i)
        result_list = []
        for i in User.objects.all():
            if i.id in unpaid_user:
                result_list.append({
                    'id': i.id,
                    'username': i.username,
                    'firs_name': i.first_name,
                    'last_name': i.last_name,
                    'organization': i.organization,
                    'position': i.position,
                    "pass_number": i.pass_number
                })
        result_list.insert(0, {
            "group": {
                "id": data['group_id'],
                "name": group_user.name,
                "users": [x.id for x in group_user.users.all()],
                "start_date": group_user.start_date,
                "finish_date": group_user.finish_date,
                "module": group_user.module.name,
            }
        })

        return Response(result_list, status=200)


class OperationViewset(viewsets.ModelViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Operations.objects.all()
    serializer_class = OperaSerializer

    @action(methods=['post'], detail=False)
    def add_description(self, request):
        data = request.data['description']
        id = request.data['id']
        operation = Operations.objects.get(id=id)
        operation.description = data
        operation.save()
        return Response("Success", 201)

    @action(methods=['get'], detail=False)
    def get_filter(self, request):
        id = request.GET.get('id', None)
        operation = Operations.objects.filter(id=id)
        data = self.get_serializer_class()(operation, many=True)
        return Response(data.data)

    @action(methods=['get'], detail=False)
    def show_answers(self, request):
        operation_id = request.GET.get('id', None)
        operation = Operations.objects.get(id=operation_id).variant_id
        question = Question.objects.filter(variant_id=operation)

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
    def get(self, request):
        operation = Operations.objects.all()
        result = []
        for i in operation:
            if i.status != "not_submitted" and i.variant:
                result.append({
                    "id": i.id,
                    "user_first_name": i.user.first_name,
                    "description": i.description,
                    "user_last_name": i.user.last_name,
                    "module_name": i.exam.group.module.name,
                    "group_name": i.exam.group.name,
                    "variant_name": i.variant.name,
                    "collect_ball": i.total_ball,
                    "percent": i.percent,
                    "status": i.status,
                    "date": i.create_at,
                })
            else:
                result.append({
                    "id": i.id,
                    "user_first_name": i.user.first_name,
                    "user_last_name": i.user.last_name,
                    "module_name": i.exam.group.module.name,
                    "group_name": i.exam.group.name,
                    "variant_name": None,
                    "collect_ball": i.total_ball,
                    "percent": i.percent,
                    "status": i.status,
                    "date": i.create_at,
                })
        return Response(result, 200)

    @action(methods=['get'], detail=False)
    def filter(self, request):
        user_id = request.GET.get('user_id', None)
        exam_id = request.GET.get('exam_id', None)
        operation = None
        if user_id:
            operation = Operations.objects.filter(user_id=user_id).order_by("-create_at")
        elif exam_id:
            operation = Operations.objects.filter(exam_id=exam_id).order_by("-create_at")
        result = []
        for i in operation:
            if i.status != "not_submitted" and i.variant:
                try:
                    paid_status = UserPayment.objects.filter(user_id=i.user_id, group_id=i.exam.group.id).last().status
                except:
                    paid_status = False
                result.append({
                    "id": i.id,
                    "user_first_name": i.user.first_name,
                    "description": i.description,
                    "user_last_name": i.user.last_name,
                    "module_name": i.exam.group.module.name,
                    "group_name": i.exam.group.name,
                    "variant_name": i.variant.name,
                    "collect_ball": i.total_ball,
                    "percent": i.percent,
                    "status": i.status,
                    "date": i.create_at + timedelta(hours=5),
                    "payment_status": paid_status,
                })
            else:
                result.append({
                    "id": i.id,
                    "user_first_name": i.user.first_name,
                    "user_last_name": i.user.last_name,
                    "module_name": i.exam.group.module.name,
                    "group_name": i.exam.group.name,
                    "variant_name": None,
                    "collect_ball": i.total_ball,
                    "percent": i.percent,
                    "status": i.status,
                    "date": i.create_at,
                })
        return Response(result, 200)

    @action(methods=['post'], detail=False)
    def post(self, request):
        data = request.data
        context = {"operationitem": data[0].get('operationitem')}
        serializer = OperationSerializer(data=data[0], context=context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(methods=['get'], detail=False)
    def filter_status(self, request):
        status_id = request.GET.get('status', None)
        operations = False
        if status_id == '1':
            operations = Operations.objects.filter(status="Passed")
        elif status_id == '2':
            operations = Operations.objects.filter(status="Fail")
        elif status_id == '3':
            operations = Operations.objects.filter(status="not_submit")

        data = []
        if operations:
            for i in operations:
                if i.group:
                    data.append({
                        "first_name": i.user.first_name,
                        "last_name": i.user.last_name,
                        "username": i.user.username,
                        "organization": i.user.organization,
                        "pass_number": i.user.pass_number,
                        "position": i.user.position,
                        "group_name": i.group.name,
                        "variant_name": i.variant.name,
                        "module_name": i.variant.module.name,
                        "status": i.status,
                        "total_ball": i.total_ball,
                    })
        return Response(data)


class SertificateViewset(viewsets.ModelViewSet):
    queryset = Operations.objects.all()
    serializer_class = OperationsSerializer

    @action(methods=['get'], detail=False)
    def get(self, request):
        id = request.GET.get('id')
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
                               f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus o’quv kursini')
                can.drawString(350, 250, "muvaffaqiyatli tamomladi")

            elif 11 > len(operation.variant.module.name.split()) >= 8:
                can.drawString(150, 270,
                               f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik maxsus')
                can.drawString(350, 250, "o’quv kursini muvaffaqiyatli tamomladi")
            elif 14 > len(operation.variant.module.name.split()) >= 11:
                can.drawString(130, 270,
                               f'"{operation.variant.module.name}" mavzusi bo’yicha 40 soatlik')
                can.drawString(350, 250, "maxsus o’quv kursini muvaffaqiyatli tamomladi")
            elif 16 > len(operation.variant.module.name.split()) >= 14:
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
            name_length = len(operation.user.last_name) + len(operation.user.first_name)
            if name_length in range(0, 27):
                can.drawCentredString(400, 320,
                                      f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                      mode=2,
                                      charSpace=6)
            elif name_length in range(27, 30):
                can.drawCentredString(418, 320,
                                      f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
                                      mode=2,
                                      charSpace=6)
            elif name_length in range(30, 33):
                can.drawCentredString(435, 320,
                                      f"{operation.user.last_name.upper()} {operation.user.first_name.upper()}",
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

            data = {
                "url": f"{url}/static/certification.pdf"
            }

            return Response(data)
        else:
            return Response('Sertificate does not exist', 400)

    @action(methods=['get'], detail=False)
    def filter(self, request):
        no_1 = request.GET.get('module_number_1', None)
        no_2 = request.GET.get('module_number_2', None)
        operation = None
        if no_1:
            operation = Operations.objects.get(number_1=no_1)
        elif no_2:
            operation = Operations.objects.get(number_2=no_2)
        if operation:
            serializer_class = OperationsSerializer(operation)
            return Response(serializer_class.data)
        else:
            return Response('Sertificate does not exist', 400)
        # except:
        #     return Response('Sertificate does not exist', 400)


class CronJob(APIView):
    def get(self, request):
        new_date = now() + timedelta(hours=5)
        exam = Exam.objects.filter(finish_date__lt=new_date)
        if exam:
            for i in exam:
                users = []
                operation = Operations.objects.filter(exam_id=i.id)
                for e in operation:
                    users.append(e.user_id)
                for user in i.user.all():
                    if user.id not in users:
                        oper = Operations.objects.create(
                            exam_id=i.id,
                            user_id=user.id,
                            status="not_submit",
                            group_id=i.group_id,
                            variant_id=i.variant_id,
                        )

        return Response("Success")


@api_view(['GET'])
def statistic(request):
    users = User.objects.all().count()
    groups = Group.objects.all().count()
    payment = UserPayment.objects.filter(status=True).count()
    passed = Operations.objects.filter(status="Passed").count()
    failed = Operations.objects.filter(status="Fail").count()
    missed = Operations.objects.filter(status="not_submit").count()
    paid_users = []
    payments = UserPayment.objects.filter(status=True)
    user = Operations.objects.filter(status="Passed")
    for i in payments:
        if i.user:
            paid_users.append(i.user.id)

    certificated_users = []
    for u in user:
        if u.user.id in paid_users:
            certificated_users.append(u.user.id)

    exams = Exam.objects.all().count()
    exam = Exam.objects.all()
    month = now().month - 1
    current_month = now().month

    # ----Last month data-------

    month_users = User.objects.filter(create_at__month=month).count()
    month_groups = Group.objects.filter(create_at__month=month).count()
    month_payment = UserPayment.objects.filter(status=True, create_at__month=month).count()
    month_passed = Operations.objects.filter(status="Passed", create_at__month=month).count()
    month_failed = Operations.objects.filter(status="Fail", create_at__month=month).count()
    month_missed = Operations.objects.filter(status="not_submit", create_at__month=month).count()
    month_exams = Exam.objects.filter(create_at__month=month).count()
    month_exam = Exam.objects.filter(create_at__month=month)

    month_paid_users = []
    month_payments = UserPayment.objects.filter(status=True)
    current_user = Operations.objects.filter(create_at__month=month, status="Passed")
    for i in month_payments:
        if i.user:
            month_paid_users.append(i.user.id)

    month_certificated_users = []
    for u in current_user:
        if u.user.id in month_paid_users:
            month_certificated_users.append(u.id)

    result = []
    month_result = []
    for e in exam:
        operation = Operations.objects.filter(exam_id=e.id)
        for i in operation:
            if i.exam_id not in result:
                result.append(i.exam_id)
    for e in month_exam:
        month_operation = Operations.objects.filter(exam_id=e.id)
        for i in month_operation:
            if i.exam_id not in month_result:
                month_result.append(i.exam_id)

    # ----Last month data-------

    current_users = User.objects.filter(create_at__month=current_month).count()
    current_groups = Group.objects.filter(create_at__month=current_month).count()
    current_payment = UserPayment.objects.filter(status=True, create_at__month=current_month).count()
    current_passed = Operations.objects.filter(status="Passed", create_at__month=current_month).count()
    current_failed = Operations.objects.filter(status="Fail", create_at__month=current_month).count()
    current_missed = Operations.objects.filter(status="not_submit", create_at__month=current_month).count()
    current_exams = Exam.objects.filter(create_at__month=current_month).count()
    current_exam = Exam.objects.filter(create_at__month=current_month)

    current_paid_users = []
    current_payments = UserPayment.objects.filter(status=True)
    month_user = Operations.objects.filter(create_at__month=current_month, status="Passed")
    for i in current_payments:
        if i.user:
            current_paid_users.append(i.user.id)

    current_certificated_users = []
    for u in month_user:
        if u.user.id in current_paid_users:
            current_certificated_users.append(u.id)

    currentresult = []
    current_result = []
    for e in exam:
        operation = Operations.objects.filter(exam_id=e.id)
        for i in operation:
            if i.exam_id not in currentresult:
                currentresult.append(i.exam_id)
    for e in current_exam:
        current_operation = Operations.objects.filter(exam_id=e.id)
        for i in current_operation:
            if i.exam_id not in current_result:
                current_result.append(i.exam_id)

    data = {
        "number_users": users,
        "number_groups": groups,
        "number_paid_users": payment,
        "passed_users": passed,
        "failed_users": failed,
        "missed_users": missed,
        "all_exams": exams,
        "taken_exams": len(result),
        "number_certificate": len(certificated_users),
        "last_month_number_certificate": len(month_certificated_users),
        "current_month_number_certificate": len(current_certificated_users),
        "last_month_number_users": month_users,
        "last_month_number_groups": month_groups,
        "last_month_number_paid_users": month_payment,
        "last_month_passed_users": month_passed,
        "last_month_failed_users": month_failed,
        "last_month_missed_users": month_missed,
        "last_month_all_exams": month_exams,
        "last_month_taken_exams": len(month_result),
        "current_month_number_users": current_users,
        "current_month_number_groups": current_groups,
        "current_month_number_paid_users": current_payment,
        "current_month_passed_users": current_passed,
        "current_month_failed_users": current_failed,
        "current_month_missed_users": current_missed,
        "current_month_all_exams": current_exams,
        "current_month_taken_exams": len(current_result),
    }
    return Response(data, 200)


@api_view(['GET'])
def filter_statistic(request):
    group_id = request.GET.get('group_id', None)
    start_dat = request.GET.get('start_date', None)
    finish_dat = request.GET.get('finish_date', None)
    number_group = 0
    if group_id != "null" and start_dat == "null" and finish_dat == "null":
        users = Group.objects.get(id=group_id).users.all().count()

        payment = UserPayment.objects.filter(group_id=group_id, status=True).count()
        exams = Exam.objects.filter(group_id=group_id)

        operations_ = []
        operations = 0

        for i in exams:
            operations += Operations.objects.filter(exam_id=i.id).count()
            operation = Operations.objects.filter(exam_id=i.id)
            for i in operation:
                if i.exam_id not in operations_:
                    operations_.append(i.exam_id)
        passed = Operations.objects.filter(status="Passed", group_id=group_id).count()
        failed = Operations.objects.filter(status="Fail", group_id=group_id).count()
        missed = Operations.objects.filter(status="not_submit", group_id=group_id).count()
        exams_number = Exam.objects.filter(group_id=group_id).count()
        operation = Operations.objects.all()
    elif start_dat != "null" and finish_dat != "null" and group_id != "null":
        start_date = datetime.strptime(start_dat, '%Y-%m-%d').date()
        finish_date = datetime.strptime(finish_dat, '%Y-%m-%d').date()
        number_group = Group.objects.filter(create_at__lte=finish_date,
                                            create_at__gte=start_date).count()
        users = Group.objects.get(id=group_id, create_at__lte=finish_date,
                                  create_at__gte=start_date).users.all().count()
        payment = UserPayment.objects.filter(group_id=group_id, status=True, create_at__lte=finish_date,
                                             create_at__gte=start_date).count()
        exams = Exam.objects.filter(group_id=group_id, create_at__lte=finish_date, create_at__gte=start_date)
        month = now().month - 1
        new_month = now().month
        operations_ = []
        operations = 0
        passed = 0
        missed = 0
        failed = 0
        for i in exams:
            operations += Operations.objects.filter(exam_id=i.id, create_at__lte=finish_date,
                                                    create_at__gte=start_date).count()
            operation = Operations.objects.filter(exam_id=i.id, create_at__lte=finish_date, create_at__gte=start_date)
            for i in operation:
                if i.exam_id not in operations_:
                    operations_.append(i.exam_id)
        passed += Operations.objects.filter(status="Passed", group_id=group_id, create_at__lte=finish_date,
                                            create_at__gte=start_date).count()
        failed += Operations.objects.filter(status="Fail", group_id=group_id, create_at__lte=finish_date,
                                            create_at__gte=start_date).count()
        missed += Operations.objects.filter(status="not_submit", group_id=group_id, create_at__lte=finish_date,
                                            create_at__gte=start_date).count()
        exams_number = Exam.objects.filter(group_id=group_id, create_at__lte=finish_date,
                                           create_at__gte=start_date).count()
        operation = Operations.objects.all()

    elif group_id == "null" and start_dat != "null" and finish_dat != "null":
        start_dat = request.GET.get('start_date', None)
        finish_dat = request.GET.get('finish_date', None)
        start_date = datetime.strptime(start_dat, '%Y-%m-%d').date()
        finish_date = datetime.strptime(finish_dat, '%Y-%m-%d').date()
        number_group = Group.objects.filter(create_at__lte=finish_date,
                                            create_at__gte=start_date).count()
        users = User.objects.filter(create_at__lte=finish_date, create_at__gte=start_date).count()
        payment = UserPayment.objects.filter(create_at__lte=finish_date, create_at__gte=start_date, status=True).count()

        month_new = start_date.month - 1
        operations_ = []

        operations = Operations.objects.filter(create_at__lte=finish_date,
                                               create_at__gte=start_date).count()
        operation = Operations.objects.filter(create_at__lte=finish_date, create_at__gte=start_date)
        for i in operation:
            if i.exam_id not in operations_:
                operations_.append(i.exam_id)
        passed = Operations.objects.filter(status="Passed", create_at__lte=finish_date,
                                           create_at__gte=start_date).count()
        failed = Operations.objects.filter(status="Fail", create_at__lte=finish_date,
                                           create_at__gte=start_date).count()
        missed = Operations.objects.filter(status="not_submit", create_at__lte=finish_date,
                                           create_at__gte=start_date).count()
        exams_number = Exam.objects.filter(create_at__lte=finish_date, create_at__gte=start_date).count()
    # -------Get last month data---------

    data = {
        "number_users": users,
        "number_exams": operations,
        "number_paid_users": payment,
        "passed_users": passed,
        "failed_users": failed,
        "missed_users": missed,
        "all_exams": exams_number,
        "taken_exams": len(operations_),
        "number_groups": number_group

    }
    return Response(data, 200)


@api_view(['GET'])
def filter_status(request):
    status_id = request.GET.get('status', None)
    start_dat = request.GET.get('start_date', None)
    finish_dat = request.GET.get('finish_date', None)
    group_id = request.GET.get('group_id', None)
    if start_dat == 'null' and finish_dat == 'null' and group_id == 'null':
        operations = False
        if status_id == '1':
            operations = Operations.objects.filter(status="Passed")
        elif status_id == '2':
            operations = Operations.objects.filter(status="Fail")
        elif status_id == '3':
            operations = Operations.objects.filter(status="not_submit")
    elif start_dat != 'null' and finish_dat != 'null' and group_id == 'null':
        start_date = datetime.strptime(start_dat, '%Y-%m-%d').date()
        finish_date = datetime.strptime(finish_dat, '%Y-%m-%d').date()
        operations = False
        if status_id == '1':
            operations = Operations.objects.filter(status="Passed", create_at__lte=finish_date,
                                                   create_at__gte=start_date)
        elif status_id == '2':
            operations = Operations.objects.filter(status="Fail", create_at__lte=finish_date,
                                                   create_at__gte=start_date)
        elif status_id == '3':
            operations = Operations.objects.filter(status="not_submit", create_at__lte=finish_date,
                                                   create_at__gte=start_date)

    elif start_dat == 'null' and finish_dat == 'null' and group_id != 'null':
        operations = False
        if status_id == '1':
            operations = Operations.objects.filter(status="Passed", group_id=group_id)
        elif status_id == '2':
            operations = Operations.objects.filter(status="Fail", group_id=group_id)
        elif status_id == '3':
            operations = Operations.objects.filter(status="not_submit", group_id=group_id)
    elif start_dat != 'null' and finish_dat != 'null' and group_id != 'null':
        start_date = datetime.strptime(start_dat, '%Y-%m-%d').date()
        finish_date = datetime.strptime(finish_dat, '%Y-%m-%d').date()
        operations = False
        if status_id == '1':
            operations = Operations.objects.filter(status="Passed", group_id=group_id, create_at__lte=finish_date,
                                                   create_at__gte=start_date)
        elif status_id == '2':
            operations = Operations.objects.filter(status="Fail", group_id=group_id, create_at__lte=finish_date,
                                                   create_at__gte=start_date)
        elif status_id == '3':
            operations = Operations.objects.filter(status="not_submit", group_id=group_id, create_at__lte=finish_date,
                                                   create_at__gte=start_date)

    data = []
    if operations:
        for i in operations:
            if i.group:
                data.append({
                    "first_name": i.user.first_name,
                    "last_name": i.user.last_name,
                    "username": i.user.username,
                    "organization": i.user.organization,
                    "pass_number": i.user.pass_number,
                    "position": i.user.position,
                    "group_name": i.group.name,
                    "variant_name": i.variant.name,
                    "module_name": i.variant.module.name,
                    "status": i.status
                })
    return Response(data)


@api_view(['GET'])
def migrate(request):
    url = "http://127.0.0.1:8000/main/migrate/"

    files = [

    ]
    headers = {}

    response = requests.request("GET", url, headers=headers, files=files)

    data = response.json()
    for i in data:
        id = i['id']
        operation = i['operation']
        question = i['question']
        answer = i['answer']

        OperationItem.objects.create(
            id=id,
            operation_id=operation,
            question_id=question,
            answer_id=answer,
        )

    return Response("success")


@api_view(['GET'])
def deadline_statistic(request):
    operations = Operations.objects.filter(status="Passed").order_by('create_at')
    data = []
    for i in operations:
        data.append({
            "id": i.id,
            "status": i.status,
            "first_name": i.user.first_name,
            "last_name": i.user.last_name,
            "pass_num": i.user.pass_number,
            "username": i.user.username,
            "position": i.user.position,
            "organization": i.user.organization,
            "total_ball": i.total_ball,
            "correct_answer": i.correct_answer,
            "variant_name": i.variant.name,
            "group_name": i.group.name,
            "module_name": i.group.module.name,
            "date": i.create_at + timedelta(days=1095),

        })

    return Response(data)
