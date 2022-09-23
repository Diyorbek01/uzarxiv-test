from django.urls import path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from operation.views import OperationViewset
from .views import *

router = DefaultRouter()

router.register('group', GroupViewset)
router.register('user', UserViewset)
router.register('module', ModuleViewset)
router.register('variant', VariantViewset)
router.register('answer', AnsversViewset)
router.register('question', QuestionViewset)
router.register('exams', ExamViewset)
