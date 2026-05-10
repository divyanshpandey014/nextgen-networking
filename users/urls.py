# users/urls.py
from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Root → home
    path('', views.home, name='home'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Home + Dashboard
    path('home/', views.home, name='home_alt'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Directory
    path('directory/', views.directory, name='directory'),

    # Profile
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # Messaging
    path('inbox/', views.inbox, name='inbox'),
    path('message/<str:username>/', views.send_message, name='send_message'),

    # <-- Add contact route here:
    path('contact/', views.contact, name='contact'),
    path('mark-read/<int:message_id>/', views.mark_read, name='mark_read'),

]
