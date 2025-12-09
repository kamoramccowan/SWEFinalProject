from django.urls import path

from .views import LoginVerifyView, LogoutView

urlpatterns = [
    path('auth/login/verify/', LoginVerifyView.as_view(), name='auth_login_verify'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
]
