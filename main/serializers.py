from rest_framework import serializers, validators
from rest_framework.authtoken.models import Token

from main.models import *


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'


class VairantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Variant
        fields = '__all__'




class GroupSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    class Meta:
        model = Group
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", 'password', 'username', 'first_name', 'last_name', 'organization', 'position', 'pass_number']
        # fields = '__all__'

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        token, created = Token.objects.get_or_create(user=user)
        return user


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.StringRelatedField(many=False)

    class Meta:
        model = Answers
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer(many=True, read_only=True)
    variant =VairantSerializer(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'name', 'variant', 'answer']

        # def create(self, validated_data):
        #     variants = validated_data.pop('answer')
        #     question = Question.objects.create(**validated_data)
        #     for item in variants:
        #         Answers.objects.create(**item, question=question)
        #
        #     return question


class ExamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Exam
        fields = ['id', 'group', 'user', 'start_date', 'finish_date', 'duration','variant', 'is_retry', 'total_passed_students',
                  'total_users', 'total_failed_students', 'total_missed_students']

    def create(self, validated_data):
        data = validated_data
        group = self.context.get('group', None)
        user = self.context.get('user', None)
        is_retry = self.context.get('is_retry', None)
        start_date = data['start_date']
        finish_date = data['finish_date']
        duration = data['duration']
        variant = data['variant']
        print(user)
        try:
            group = Group.objects.get(id=group).id
        except Group.DoesNotExist:
            raise validators.ValidationError('group id does not exists')

        for i in user:
            try:
                user_id = User.objects.get(id=i).id
            except User.DoesNotExist:
                raise validators.ValidationError(f'user id - {i} does not exists')
        exam = Exam.objects.create(group_id=group,
                                   start_date=start_date,
                                   finish_date=finish_date,
                                   duration=duration,
                                   variant_id=variant.id
                                   )
        for i in user:
            exam.user.add(i)
            exam.save()
        return exam


class ExamsSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    user = UserSerializer(read_only=True, many=True)
    variant = VairantSerializer(read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'group', 'user', 'start_date', 'finish_date', 'duration','variant', 'is_retry', 'total_passed_students',
                  'total_users', 'total_failed_students', 'total_missed_students']