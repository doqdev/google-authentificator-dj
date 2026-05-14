from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("2fa/challenge/", views.two_factor_challenge_view, name="two_factor_challenge"),
]
