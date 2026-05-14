from django.contrib import admin
from .models import TwoFactorProfile


@admin.register(TwoFactorProfile)
class TwoFactorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_enabled", "updated_at")
    search_fields = ("user__username", "user__email")
