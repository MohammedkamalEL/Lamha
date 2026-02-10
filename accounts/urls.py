from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import TailwindAuthenticationForm
from .views import RegisterView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html', 
        authentication_form=TailwindAuthenticationForm
    ), name='login'),
    
    path('register/', RegisterView.as_view(), name='register'),
]