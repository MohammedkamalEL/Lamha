from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


TAILWIND_CLASSES = 'w-full px-5 py-4 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none transition-all text-right text-sm'

class TailwindUserCreationForm(UserCreationForm):

    email = forms.EmailField(label="البريد الإلكتروني", required=True)

    class Meta:
        model = User
        fields = ("username", "email")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

        self.fields['username'].label = "اسم المستخدم"
        self.fields['password1'].label = "كلمة المرور"
        self.fields['password2'].label = "تأكيد كلمة المرور"


        for field in self.fields.values():
            field.widget.attrs.update({'class': TAILWIND_CLASSES})

class TailwindAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = "اسم المستخدم"
        self.fields['password'].label = "كلمة المرور"
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': TAILWIND_CLASSES})