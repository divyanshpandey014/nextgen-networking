from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import DEPARTMENT_CHOICES

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    student_id = forms.CharField(max_length=40, required=True)
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, required=True)
    skills = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Your skills..."}),
        required=False
    )
    photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email', 'password1', 'password2',
            'first_name', 'last_name',
            'student_id', 'department', 'skills', 'photo'
        )
