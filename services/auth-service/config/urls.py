from django.contrib import admin
from django.urls import path, include
from accounts.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('health', HealthCheckView.as_view()),
]
