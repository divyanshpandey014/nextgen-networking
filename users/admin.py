from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Profile, Message

User = get_user_model()


@admin.action(description="Approve selected profiles (activate user + notify)")
def approve_profiles(modeladmin, request, queryset):
    """
    Admin action to mark profiles as approved:
    - set profile.is_approved = True
    - set linked user.is_active = True
    - send a notification email (silently fails in dev if email not configured)
    """
    for profile in queryset:
        profile.is_approved = True
        profile.save()

        # Activate the linked user
        user = profile.user
        user.is_active = True
        user.save()

        # Send notification email (safe for dev if console/email backend not configured)
        try:
            login_url = getattr(settings, 'LOGIN_URL', '/login/')
            # make login_url absolute if you have SITE_URL configured
            site_root = getattr(settings, 'SITE_ROOT', 'http://127.0.0.1:8000')
            full_login_url = site_root.rstrip('/') + login_url

            send_mail(
                subject="Your ConnectGen account has been approved",
                message=f"Hello {getattr(user, 'first_name', '')},\n\n"
                        "Your ConnectGen account has been approved by admin. "
                        f"You can now log in here: {full_login_url}\n\n"
                        "Regards,\nConnectGen Admin Team",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com'),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            # fail silently in case email backend is not configured in dev
            pass


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'department', 'is_approved', 'submitted_at')
    list_filter = ('is_approved', 'department')
    search_fields = ('student_id', 'user__username', 'user__email')
    actions = [approve_profiles]
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'short_body', 'created_at', 'read')
    search_fields = ('sender__username', 'sender__email', 'recipient__username', 'recipient__email', 'body')
    list_filter = ('read',)
    readonly_fields = ('created_at',)

    def short_body(self, obj):
        return (obj.body[:75] + '...') if len(obj.body) > 75 else obj.body
    short_body.short_description = 'Message'


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Message, MessageAdmin)
