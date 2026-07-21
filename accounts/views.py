from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import TailwindUserCreationForm


class RegisterView(CreateView):
    form_class = TailwindUserCreationForm
    template_name = 'accounts/register.html'
<<<<<<< HEAD
    success_url = reverse_lazy('login')
    
=======
    success_url = reverse_lazy('login')
>>>>>>> 9a7726ff3c79aedd394968656331281de038becf
