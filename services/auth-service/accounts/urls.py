from django.urls import path
from accounts import views

urlpatterns = [
    path('auth/register', views.RegisterUserAPIView.as_view(), name='register-view'),
    path('auth/login', views.LoginUserAPIView.as_view(), name='login-view'),
    path('auth/logout', views.LogoutAPIView.as_view(), name='logout-view'),
    path('auth/token/refresh', views.RefreshTokenAPIView.as_view(), name='refresh-view'),
    path('users/profile', views.UserProfileView.as_view(), name='profile-view'),
]
