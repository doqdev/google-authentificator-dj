import pyotp
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import TwoFactorProfile


class AuthenticationFlowTests(TestCase):
    def test_register_page_creates_user(self) -> None:
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_without_2fa_succeeds(self) -> None:
        User.objects.create_user(username="plain", password="TestPass123!")
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "plain", "password": "TestPass123!"},
            follow=False,
        )
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)

    def test_login_with_enabled_2fa_requires_challenge(self) -> None:
        user = User.objects.create_user(username="twofa", password="TestPass123!")
        TwoFactorProfile.objects.create(user=user, secret=pyotp.random_base32(), is_enabled=True)

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "twofa", "password": "TestPass123!"},
            follow=False,
        )
        self.assertRedirects(
            response,
            reverse("accounts:two_factor_challenge"),
            fetch_redirect_response=False,
        )

    def test_valid_2fa_code_completes_login(self) -> None:
        user = User.objects.create_user(username="codeuser", password="TestPass123!")
        secret = pyotp.random_base32()
        TwoFactorProfile.objects.create(user=user, secret=secret, is_enabled=True)

        self.client.post(
            reverse("accounts:login"),
            {"username": "codeuser", "password": "TestPass123!"},
        )
        code = pyotp.TOTP(secret).now()
        response = self.client.post(
            reverse("accounts:two_factor_challenge"),
            {"code": code},
            follow=False,
        )
        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)
