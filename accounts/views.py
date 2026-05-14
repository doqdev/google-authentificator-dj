import base64
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LoginForm, RegisterForm, TOTPCodeForm
from .models import TwoFactorProfile


def home_redirect(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    return redirect("accounts:login")


def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("accounts:login")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            two_factor = getattr(user, "two_factor_profile", None)
            # If 2FA is enabled, require token verification before login().
            if two_factor and two_factor.is_enabled and two_factor.secret:
                request.session["pre_2fa_user_id"] = user.pk
                return redirect("accounts:two_factor_challenge")
            login(request, user)
            return redirect("accounts:profile")
    else:
        form = LoginForm(request)
    return render(request, "registration/login.html", {"form": form})


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    two_factor, _ = TwoFactorProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "generate_secret":
            # Secret is generated server-side and shown as QR otpauth URI.
            two_factor.secret = pyotp.random_base32()
            two_factor.is_enabled = False
            two_factor.save()
            messages.info(request, "New 2FA secret generated. Scan and verify the code.")
            return redirect("accounts:profile")
        if action == "enable_2fa":
            code_form = TOTPCodeForm(request.POST)
            if code_form.is_valid() and two_factor.secret:
                totp = pyotp.TOTP(two_factor.secret)
                if totp.verify(code_form.cleaned_data["code"], valid_window=1):
                    two_factor.is_enabled = True
                    two_factor.save()
                    messages.success(request, "2FA enabled successfully.")
                else:
                    messages.error(request, "Invalid TOTP code.")
            else:
                messages.error(request, "Invalid code format.")
            return redirect("accounts:profile")
        if action == "disable_2fa":
            two_factor.is_enabled = False
            two_factor.save()
            messages.warning(request, "2FA has been disabled.")
            return redirect("accounts:profile")

    qr_base64 = None
    provisioning_uri = None
    if two_factor.secret:
        provisioning_uri = pyotp.TOTP(two_factor.secret).provisioning_uri(
            name=request.user.username,
            issuer_name=settings.TOTP_ISSUER,
        )
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(
        request,
        "accounts/profile.html",
        {
            "two_factor": two_factor,
            "qr_base64": qr_base64,
            "provisioning_uri": provisioning_uri,
            "code_form": TOTPCodeForm(),
        },
    )


def two_factor_challenge_view(request: HttpRequest) -> HttpResponse:
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")

    user_model = get_user_model()
    user = get_object_or_404(user_model, pk=user_id)
    two_factor = getattr(user, "two_factor_profile", None)

    if not two_factor or not two_factor.is_enabled or not two_factor.secret:
        # If 2FA data was removed unexpectedly, continue normal login.
        login(request, user)
        request.session.pop("pre_2fa_user_id", None)
        return redirect("accounts:profile")

    if request.method == "POST":
        form = TOTPCodeForm(request.POST)
        if form.is_valid():
            if pyotp.TOTP(two_factor.secret).verify(form.cleaned_data["code"], valid_window=1):
                login(request, user)
                request.session.pop("pre_2fa_user_id", None)
                messages.success(request, "2FA verification successful.")
                return redirect("accounts:profile")
            messages.error(request, "Invalid TOTP code.")
    else:
        form = TOTPCodeForm()

    return render(request, "accounts/two_factor_challenge.html", {"form": form, "user": user})
