from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ['nickname', 'avatar']


class UserWithProfileAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'nickname', 'date_joined', 'is_staff']
    list_select_related = ['profile']

    @admin.display(description='Никнейм', ordering='profile__nickname')
    def nickname(self, user):
        # у пользователя, созданного через createsuperuser, профиля может не быть
        return getattr(user, 'profile', None) and user.profile.nickname


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'nickname', 'avatar']
    list_select_related = ['user']
    search_fields = ['nickname', 'user__username', 'user__email']
    list_filter = ['user__date_joined', 'user__is_staff']
    raw_id_fields = ['user']


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)
