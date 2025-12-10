from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Firebase", {"fields": ("firebase_uid", "display_name")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    list_display = ("username", "firebase_uid", "email", "is_staff", "is_active")
    search_fields = ("username", "firebase_uid", "email", "display_name")
