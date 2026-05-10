from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .forms import SignUpForm
from .models import Profile, Message

User = get_user_model()


def signup_view(request):
    """
    Signup creates a User and a Profile. New accounts remain inactive/is_approved False
    until admin reviews them.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            student_id = form.cleaned_data.get('student_id')
            department = form.cleaned_data.get('department')
            photo = form.cleaned_data.get('photo')
            first_name = form.cleaned_data.get('first_name', '')
            last_name = form.cleaned_data.get('last_name', '')
            skills = form.cleaned_data.get('skills', '')

            # Prevent duplicate student_id
            if student_id and Profile.objects.filter(student_id=student_id).exists():
                messages.error(request, "A user with this student ID already exists.")
                return render(request, 'users/signup.html', {'form': form})

            # Save the User using the form (commit=False to set fields reliably)
            user = form.save(commit=False)

            # If username is empty, use email as username (keeps compatibility)
            if not getattr(user, 'username', None):
                user.username = email or form.cleaned_data.get('username', '')

            if email:
                user.email = email

            # New users are inactive until admin approves — adjust if you want auto-activate
            user.is_active = False

            # Optional first/last names on User model
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name

            user.save()

            # Create Profile entry (if signal already creates one, update instead)
            profile, created = Profile.objects.get_or_create(user=user)
            profile.student_id = student_id or profile.student_id
            profile.department = department or profile.department
            if hasattr(profile, 'photo') and photo:
                profile.photo = photo
            if hasattr(profile, 'first_name'):
                profile.first_name = first_name
            if hasattr(profile, 'last_name'):
                profile.last_name = last_name
            if hasattr(profile, 'skills'):
                profile.skills = skills
            # ensure not approved by default
            profile.is_approved = False
            profile.save()

            messages.success(request, "Application submitted. You will be notified after admin approval.")
            return redirect('users:signup')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    """
    Login using email OR username:
    - if email provided, find user by email and authenticate using its username
    - otherwise use username input
    """
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        username_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        username_to_auth = None

        # If email provided, try to find user by email first
        if email:
            try:
                user_obj = User.objects.get(email__iexact=email)
                username_to_auth = user_obj.username
            except User.DoesNotExist:
                username_to_auth = None

        # If no email match, fall back to username field
        if not username_to_auth and username_input:
            username_to_auth = username_input

        user = None
        if username_to_auth:
            user = authenticate(request, username=username_to_auth, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('users:dashboard')
            else:
                messages.error(request, "Your account is not active yet. Please wait for admin approval.")
                return render(request, 'users/login.html', {})
        else:
            messages.error(request, "Invalid email/username or password.")
            return render(request, 'users/login.html', {})
    return render(request, 'users/login.html', {})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('users:login')


@login_required
def home(request):
    return render(request, 'users/home.html')


@login_required
def dashboard(request):
    # show a few recent messages for quick access
    recent_msgs = Message.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    return render(request, 'users/dashboard.html', {'recent_msgs': recent_msgs})


@login_required
def directory(request):
    q = request.GET.get('q', '').strip()
    users_qs = Profile.objects.filter(is_approved=True, user__is_active=True).select_related('user')
    if q:
        users_qs = users_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(student_id__icontains=q) |
            Q(department__icontains=q)
        )
    users_qs = users_qs.order_by('first_name', 'last_name')
    return render(request, 'users/directory.html', {'users': users_qs, 'query': q})


@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user_obj)
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def inbox(request):
    received = Message.objects.filter(recipient=request.user).select_related('sender').order_by('-created_at')
    # optionally mark unread count
    unread_count = received.filter(read=False).count()
    return render(request, 'users/inbox.html', {'messages': received, 'unread_count': unread_count})


@login_required
def send_message(request, username):
    receiver_user = get_object_or_404(User, username=username)
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            # create message with new field names
            Message.objects.create(sender=request.user, recipient=receiver_user, body=body)
            messages.success(request, "Message sent successfully!")
            return redirect('users:inbox')
        else:
            messages.error(request, "Message cannot be empty.")
    return render(request, 'users/send_message.html', {'receiver': receiver_user})
# users/views.py (add imports at top if not present)
from django.core.mail import send_mail
from django.conf import settings

# Add this view
def contact(request):
    """
    Simple contact page. On POST, sends a notification email to DEFAULT_FROM_EMAIL (console backend in dev).
    """
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()

        # Optional: very simple validation
        if not message_text:
            messages.error(request, "Please write a message before sending.")
            return render(request, 'users/contact.html', {'name': name, 'email': email, 'message': message_text})

        # Send a notification to the admin (prints to console in dev)
        try:
            send_mail(
                subject=f"Contact form: {name or 'Anonymous'}",
                message=f"From: {name} <{email}>\n\n{message_text}",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@connectgen.local'),
                recipient_list=[getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@connectgen.local')],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, "Thanks — your message has been sent. We'll get back to you soon.")
        return redirect('users:home')

    # GET: render form
    return render(request, 'users/contact.html', {})
from django.shortcuts import redirect, get_object_or_404
from .models import Message

def mark_read(request, message_id):
    msg = get_object_or_404(Message, id=message_id, recipient=request.user)
    msg.read = True
    msg.save()
    return redirect('users:inbox')
