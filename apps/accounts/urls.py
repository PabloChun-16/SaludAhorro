from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings

urlpatterns = [
    path("login/",  LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/logout/",
         LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL),
         name="logout"),
]
