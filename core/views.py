from django.views.generic import TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect

import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import re
from django.http import JsonResponse
from django.views import View
from datetime import datetime
from .models import Transaction
from django.db.models import Sum, Max, Q
from django.utils import timezone


class HomeView(TemplateView):
    template_name = 'core/home.html'

    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_txs = Transaction.objects.filter(user=self.request.user)
        
        
        today = timezone.now().date()

        upload_today_txs = user_txs.filter(created_at__date=today)

        context['total_in_today'] = upload_today_txs.filter(type='in').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_out_today'] = upload_today_txs.filter(type='out').aggregate(Sum('amount'))['amount__sum'] or 0
        context['count_today'] = upload_today_txs.count()
        context['max_today'] = upload_today_txs.aggregate(Max('amount'))['amount__max'] or 0
        
        month_txs = user_txs.filter(created_at__month=today.month, created_at__year=today.year)
        context['total_in_month'] = month_txs.filter(type='in').aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_out_month'] = month_txs.filter(type='out').aggregate(Sum('amount'))['amount__sum'] or 0

        context['transactions'] = user_txs.order_by('-created_at')[:10]
        
        return context
    

    
class UploadView(LoginRequiredMixin, TemplateView):
    template_name = 'core/upload.html'

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'core/profile.html' 
    fields = ['username', 'email'] 
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        return self.request.user


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'core/user_confirm_delete.html' 
    success_url = reverse_lazy('home')

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        logout(request)
        return response
    

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\ahmed\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

class ProcessNotificationView(View):
    def post(self, request, *args, **kwargs):
        if request.FILES.get('notification_image'):
            try:
                image_file = request.FILES['notification_image']
                img = Image.open(image_file)

                width, height = img.size
                img = img.resize((width*2, height*2), resample=Image.Resampling.LANCZOS)
                
                img = img.convert('L') 
                img = ImageEnhance.Contrast(img).enhance(3.0)
                
                full_text = pytesseract.image_to_string(img, lang='ara+eng', config='--psm 6')
                print("--- النص المستخرج بعد التكبير ---\n", full_text)

                amount = "0.00"
                amount_match = re.findall(r'(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', full_text)

                if amount_match:
                    clean_amounts = [float(a.replace(',', '')) for a in amount_match]
                    amount = amount_match[clean_amounts.index(max(clean_amounts))]


                date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', full_text)
                
                if date_match:
                    extracted_date = date_match.group(1)
                else:
                    fallback = re.search(r'(\d{2}.{1,5}202[4-6])', full_text)

                    if fallback:
                        extracted_date = fallback.group(1)
                        extracted_date = re.sub(r'[^\d\-a-zA-Z]', '-', extracted_date)
                    else:
                        extracted_date = datetime.now().strftime('%d-%b-%Y')

                ref_match = re.search(r'(\d{10,})', full_text)
                if ref_match:
                    full_ref = ref_match.group(1)
                    ref_last_4 = full_ref[-4:] 
                else:
                    ref_fallback = re.findall(r'\d+', full_text)
                    longest_num = max(ref_fallback, key=len) if ref_fallback else "0000"
                    ref_last_4 = longest_num[-4:]

                return JsonResponse({
                    'status': 'success',
                    'amount': amount,
                    'date': extracted_date,
                    'ref_last_4': ref_last_4
                })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            

class SaveTransactionView(View):
    def post(self, request, *args, **kwargs):
        amount = request.POST.get('amount').replace(',', '')
        raw_date = request.POST.get('date')
        ref = request.POST.get('ref_last_4')
        t_type = request.POST.get('type')

        try:
            try:
                clean_date = datetime.strptime(raw_date, '%d-%b-%Y').date()
            except:
                clean_date = timezone.now().date()

            transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_date=clean_date,
                ref_last_4=ref,
                type=t_type
            )
            return JsonResponse({'status': 'success', 'message': 'تم حفظ العملية بنجاح!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})