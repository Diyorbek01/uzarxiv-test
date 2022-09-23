from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()

router.register('payment', PaymentViewset)
router.register('result', OperationViewset)
router.register('sertificate', SertificateViewset)
