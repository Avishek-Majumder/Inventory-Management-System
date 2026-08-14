from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Profile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'address']
    search_fields = ['user__username', 'phone_number']
