from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()
DEPARTMENT_CHOICES = [
    ('SoL', 'School of Languages'),
    ('SoM', 'School of Management'),
    ('SoSS', 'School of Social Sciences'),
    ('SoENR', 'School of Environment & Natural Resources'),
    ('SoD', 'School of Design'),
    ('SoPS', 'School of Physical Sciences'),
    ('SoT', 'School of Technology'),
    ('SoMC', 'School of Media & Communication Studies'),
    ('NHRC', 'Nityanand Himalayan Research and Study Centre'),
    ('SoBS', 'School of Biological Sciences'),
    ('GSCUS', 'Global South Centre for Urban Studies'),
    ('CHS', 'Centre for Hindu Studies'),
]



class Profile(models.Model):
    # You can keep first_name/last_name here, or use User.first_name/last_name.
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    skills = models.TextField(blank=True, null=True)
    student_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True)
    photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)   # admin approval flag
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        # prefer email if available; fallback to username or student_id
        user_ident = getattr(self.user, 'email', None) or getattr(self.user, 'username', '')
        return f"{user_ident} — {self.student_id}"

    def get_full_name(self):
        name = f"{self.first_name or self.user.first_name} {self.last_name or self.user.last_name}".strip()
        return name or (getattr(self.user, 'email', '') or self.student_id)


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='inbox_messages', on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)  # useful for unread count

    class Meta:
        ordering = ['-created_at']  # newest first
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        sender_ident = getattr(self.sender, 'email', getattr(self.sender, 'username', str(self.sender)))
        recipient_ident = getattr(self.recipient, 'email', getattr(self.recipient, 'username', str(self.recipient)))
        return f"Msg from {sender_ident} to {recipient_ident} at {self.created_at}"


# Automatically create/update Profile when a User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # create profile with default placeholders (you can customize)
        Profile.objects.create(user=instance, student_id=f"uid-{instance.pk}")
    else:
        # Ensure profile exists and save it so signals propagate
        Profile.objects.get_or_create(user=instance)
