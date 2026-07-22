from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import TailwindUserCreationForm


class RegisterView(CreateView):
    form_class = TailwindUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
    
