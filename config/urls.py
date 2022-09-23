from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

from main.urls import router
from operation.urls import router as op_router
from django.conf.urls.static import static
from django.conf import settings
from main import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from main import views as ma_views
from operation import views as op_views
from operation.views import CronJob

schema_view = get_schema_view(
    openapi.Info(
        title="My project API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', include(router.urls)),
    path('certificate/<int:id>',ma_views.certificate),
    # path('down/',ma_views.generate),
    path('cron/', CronJob.as_view()),
    path('statistic/', op_views.statistic),
    path('filter_status/', op_views.filter_status),
    path('deadline_statistic/', op_views.deadline_statistic),
    path('migrate/', op_views.migrate),
    path('filter_statistic/', op_views.filter_statistic),
    path('operation/', include(op_router.urls)),
    path('main/exam/', ma_views.ExamApiViewset.as_view()),
    path('api/login/', op_views.login),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)