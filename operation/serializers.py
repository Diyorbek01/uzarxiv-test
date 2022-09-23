from rest_framework import serializers

from main.models import Operations, OperationItem, UserPayment, Answers, Module
from main.serializers import VairantSerializer, UserSerializer, ExamsSerializer


class OperationItemsSerializer(serializers.ModelSerializer):
    operation = serializers.StringRelatedField(many=False)

    class Meta:
        model = OperationItem
        # fields = '__all__'
        fields = ['operation', 'question', 'answer']
        # read_only_fields = ('operation',)


class OperationSerializer(serializers.ModelSerializer):
    operationitem = OperationItemsSerializer(many=True, read_only=True)

    class Meta:
        model = Operations
        # fields = '__all__'
        fields = ['id', 'user', 'exam','group', 'variant','description', 'correct_answer', 'percent', 'total_ball', 'status', 'total_balls'
            , 'operationitem','description']

    def create(self, validated_data):
        operationitem = self.context.pop('operationitem')
        operation = Operations.objects.create(**validated_data)
        # exam = Exam.objects.
        module = Module.objects.get(id=operation.variant.module_id)
        module.no_1 += 1
        module.no_2 += 1
        module.save()
        total_ball = operation.total_balls
        answer_list = []
        correct_ball = 0
        correct_answers = 0

        for item in operationitem:
            OperationItem.objects.create(question_id=item['question'], answer_id=item['answer'], operation=operation)

            if item.get('answer'):

                answer = Answers.objects.filter(status='Correct')
                for i in answer:
                    answer_list.append(i.id)

                if item.get('answer') in answer_list:
                    correct_answers += 1
                    correct_ball += int(Answers.objects.get(id=item.get('answer')).ball)
        percent = 0
        if correct_ball>0:
            percent = correct_ball * 100 / total_ball
        operation.percent = round(percent, 2)
        operation.correct_answer = correct_answers
        operation.total_ball = correct_ball
        operation.number_1 = module.no_1
        operation.number_2 = module.no_2

        if percent >= 56:
            operation.status = "Passed"
        elif percent < 56:
            operation.status = "Fail"
        operation.save()

        return operation


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPayment
        fields = '__all__'


class OperationsItemsSerializer(serializers.ModelSerializer):
    operation = serializers.StringRelatedField(many=False)

    class Meta:
        model = OperationItem
        # fields = '__all__'
        fields = ['operation', 'question', 'answer']
        # read_only_fields = ('operation',)


class OperationsSerializer(serializers.ModelSerializer):
    operationitem = OperationsItemsSerializer(many=True)

    class Meta:
        model = Operations
        # fields = '__all__'
        fields = ['user', 'exam','group', 'variant', 'correct_answer', 'percent', 'total_ball', 'status', 'total_balls',
                  'qr_image', 'operationitem',"description"]


class OperaSerializer(serializers.ModelSerializer):
    operationitem = OperationsItemsSerializer(many=True)
    variant = VairantSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    exam = ExamsSerializer(read_only=True)

    class Meta:
        model = Operations
        # fields = '__all__'
        fields = ["id",'user', 'exam','group', 'variant', 'correct_answer', 'percent', 'total_ball', 'status', 'total_balls',
                  'qr_image', 'operationitem',"description"]