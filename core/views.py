from django.views.generic import TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect
from .models import Notification, Transaction, UserSettings

import pytesseract
from PIL import Image, ImageOps, ImageEnhance
import re
from django.http import JsonResponse
from django.views import View
from datetime import datetime
from django.db.models import Sum, Max, Q
from django.utils import timezone
from django.contrib import messages
import openpyxl
from django.http import HttpResponse

class HomeView(TemplateView):
    template_name = 'core/home.html'

    
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Max
from django.utils import timezone

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['core/partials/transactions_table.html']
        return ['core/dashboard.html']


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

        query = self.request.GET.get('q')
        transactions_list = user_txs.order_by('-created_at')
        
        if query:
            transactions_list = transactions_list.filter(
                Q(ref_last_4__istartswith=query)
            )

        paginator = Paginator(transactions_list, 8) 
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['transactions'] = page_obj
        
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
                # حيطبع الداتا المتسخرجة في ال terminal للاختبار فقط 
                # print("--- النص المستخرج بعد التكبير ---\n", full_text)

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

        raw_amount = request.POST.get('amount', '0')
        clean_amount_str = raw_amount.replace(',', '').strip() 
        
        try:
            amount = float(clean_amount_str)
            raw_date = request.POST.get('date')
            ref = request.POST.get('ref_last_4')
            t_type = request.POST.get('type')

            try:
                clean_date = datetime.strptime(raw_date, '%d-%b-%Y').date()
            except:
                clean_date = timezone.now().date()


            is_duplicate = Transaction.objects.filter(
                user=request.user,
                ref_last_4=ref,
                amount=amount,
                transaction_date=clean_date
            ).exists()

            if is_duplicate:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'عذراً، هذا الإشعار تم حفظه ومسجل في النظام من قبل!'
                })
            

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_date=clean_date,
                ref_last_4=ref,
                type=t_type
            )

            user_settings, _ = UserSettings.objects.get_or_create(user=request.user)

            if user_settings.notifications_enabled:
                limit = float(user_settings.alert_threshold)
                if amount >= limit:
                    Notification.objects.create(
                        user=request.user,
                        title="!!تنبيه: مبلغ يتجاوز الحد",
                        message=f"تم رصد عملية بمبلغ {amount:,.0f} ج.س."
                    )

            return JsonResponse({'status': 'success', 'message': 'تم حفظ العملية بنجاح!'})
        except Exception as e:
            print(f"Error: {e}") # لل debuging في ال terminal ومتابعة ال errors
            return JsonResponse({'status': 'error', 'message': str(e)})


class SettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'core/settings.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('settings')
    success_message = "تم تحديث إعدادات حسابك بنجاح!"

    def get_object(self):
        return self.request.user
    

class FinancialSettingsUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        user_settings, created = UserSettings.objects.get_or_create(user=request.user)

        threshold = request.POST.get('alert_threshold')
        use_symbols = request.POST.get('use_currency_symbols') == 'on'
        notifications = request.POST.get('notifications_enabled') == 'on'

        if threshold:
            user_settings.alert_threshold = threshold
        
        user_settings.use_currency_symbols = use_symbols
        user_settings.notifications_enabled = notifications
        user_settings.save()

        messages.success(request, "تم تحديث التفضيلات المالية بنجاح!")
        return redirect('settings')
    

class MarkNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        
        updated_count = request.user.notifications.filter(is_read=False).update(is_read=True)
        
        return JsonResponse({
            'status': 'success', 
            'message': f'تم تحديث {updated_count} إشعار'
        })



class ExportFinancialLogExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Financial Report"
        ws.sheet_view.rightToLeft = True

        headers = ['التاريخ', 'النوع', 'المبلغ', 'آخر 4 أرقام للعملية']
        ws.append(headers)

        queryset = Transaction.objects.filter(user=request.user).order_by('-transaction_date')

        for obj in queryset:
            t_date = obj.transaction_date  
            amount = obj.amount
            t_type = "وارد" if obj.type == 'in' else "صادر"
            ref = obj.ref_last_4 

            formatted_date = t_date.strftime('%Y-%m-%d %H:%M') if t_date else "---"

            ws.append([
                formatted_date,
                t_type,
                float(amount) if amount else 0.0,
                ref
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="Financial_Report.xlsx"'
        
        wb.save(response)
        return response