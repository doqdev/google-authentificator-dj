from django.conf import settings
from django.db import models


class TwoFactorProfile(models.Model):
    # One profile row per user stores TOTP state for Google Authenticator.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_profile",
    )
    secret = models.CharField(max_length=64, blank=True, default="")
    is_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} 2FA={self.is_enabled}"
