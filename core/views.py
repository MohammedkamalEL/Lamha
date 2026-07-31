from django.views.generic import TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect

import requests
from django.conf import settings
import re
from django.http import JsonResponse
from django.views import View
from datetime import datetime
from .models import Transaction
from django.db.models import Sum, Max, Q
from django.utils import timezone


from functools import wraps
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required


def admin_required(view_func):

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


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


def ocr_space_extract(image_file):
    """
    يبعت الصورة لـ OCR.space API ويرجع النص المستخرج.
    """
    url = 'https://api.ocr.space/parse/image'

    response = requests.post(
        url,
        files={'notification_image': image_file},
        data={
            'apikey': settings.OCR_SPACE_API_KEY,
            'language': 'auto',
            'OCREngine': 3,
            'scale': True,
        },
    )

    result = response.json()

    if result.get('IsErroredOnProcessing'):
        raise Exception(result.get('ErrorMessage', 'OCR failed'))

    parsed_text = result['ParsedResults'][0]['ParsedText']
    return parsed_text


# class ProcessNotificationView(View):
#     def post(self, request, *args, **kwargs):
#         if request.FILES.get('notification_image'):
#             try:
#                 image_file = request.FILES['notification_image']

#                 image_file.seek(0)
#                 try:
#                     full_text = ocr_space_extract(image_file)
#                 except Exception as e:
#                     return JsonResponse({'status': 'error', 'message': f'فشل استخراج النص: {str(e)}'})

#                 print("--- النص المستخرج (OCR.space) ---\n", full_text)

#                 amount = "0.00"
#                 amount_match = re.findall(r'(\d{1,3}(?:,\d{3})+(?:\.\d{2})?)', full_text)

#                 if amount_match:
#                     clean_amounts = [float(a.replace(',', '')) for a in amount_match]
#                     amount = amount_match[clean_amounts.index(max(clean_amounts))]


#                 date_match = re.search(r'(\d{2}-[A-Za-z]{3}-\d{4})', full_text)
                
#                 if date_match:
#                     extracted_date = date_match.group(1)
#                 else:
#                     fallback = re.search(r'(\d{2}.{1,5}202[4-6])', full_text)

#                     if fallback:
#                         extracted_date = fallback.group(1)
#                         extracted_date = re.sub(r'[^\d\-a-zA-Z]', '-', extracted_date)
#                     else:
#                         extracted_date = datetime.now().strftime('%d-%b-%Y')

#                 ref_match = re.search(r'(\d{10,})', full_text)
#                 if ref_match:
#                     full_ref = ref_match.group(1)
#                     ref_last_4 = full_ref[-4:] 
#                 else:
#                     ref_fallback = re.findall(r'\d+', full_text)
#                     longest_num = max(ref_fallback, key=len) if ref_fallback else "0000"
#                     ref_last_4 = longest_num[-4:]

#                 return JsonResponse({
#                     'status': 'success',
#                     'amount': amount,
#                     'date': extracted_date,
#                     'ref_last_4': ref_last_4
#                 })

#             except Exception as e:
#                 return JsonResponse({'status': 'error', 'message': str(e)})

class ProcessNotificationView(View):
    def post(self, request, *args, **kwargs):
        if request.FILES.get('notification_image'):
            try:
                image_file = request.FILES['notification_image']
                t_type = request.POST.get('transaction_type', 'in')  # نوع العملية من الفورم

                image_file.seek(0)
                try:
                    full_text = ocr_space_extract(image_file)
                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': f'فشل استخراج النص: {str(e)}'})

                print("--- النص المستخرج (OCR.space) ---\n", full_text)

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

                # --- فحص التكرار قبل عرض المودال ---
                try:
                    clean_amount_val = amount.replace(',', '')
                    clean_date_val = datetime.strptime(extracted_date, '%d-%b-%Y').date()
                except:
                    clean_date_val = None

                is_duplicate = False
                if clean_date_val:
                    is_duplicate = Transaction.objects.filter(
                        user=request.user,
                        amount=clean_amount_val,
                        transaction_date=clean_date_val,
                        ref_last_4=ref_last_4,
                        type=t_type
                    ).exists()

                if is_duplicate:
                    return JsonResponse({
                        'status': 'duplicate',
                        'message': 'هذا الإشعار مكرر وتم رفعه من قبل.'
                    })

                return JsonResponse({
                    'status': 'success',
                    'amount': amount,
                    'date': extracted_date,
                    'ref_last_4': ref_last_4
                })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
          

# class SaveTransactionView(View):
#     def post(self, request, *args, **kwargs):
#         amount = request.POST.get('amount').replace(',', '')
#         raw_date = request.POST.get('date')
#         ref = request.POST.get('ref_last_4')
#         t_type = request.POST.get('type')

#         try:
#             try:
#                 clean_date = datetime.strptime(raw_date, '%d-%b-%Y').date()
#             except:
#                 clean_date = timezone.now().date()

#             transaction = Transaction.objects.create(
#                 user=request.user,
#                 amount=amount,
#                 transaction_date=clean_date,
#                 ref_last_4=ref,
#                 type=t_type
#             )
#             return JsonResponse({'status': 'success', 'message': 'تم حفظ العملية بنجاح!'})
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)})

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

            # التحقق من التكرار: نفس المستخدم + المبلغ + التاريخ + آخر 4 أرقام + النوع
            is_duplicate = Transaction.objects.filter(
                user=request.user,
                amount=amount,
                transaction_date=clean_date,
                ref_last_4=ref,
                type=t_type
            ).exists()

            if is_duplicate:
                return JsonResponse({
                    'status': 'error',
                    'message': 'هذا الإشعار مكرر بالفعل وتم تسجيله من قبل.'
                })

            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_date=clean_date,
                ref_last_4=ref,
                type=t_type
            )
            return JsonResponse({'status': 'success', 'message': 'تم حفظ العملية بنجاح!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


#  admin views 

@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_in = Transaction.objects.filter(type='in').aggregate(Sum('amount'))['amount__sum'] or 0
    total_out = Transaction.objects.filter(type='out').aggregate(Sum('amount'))['amount__sum'] or 0
    total_volume = total_in + total_out

    context = {
        'total_users': total_users,
        'total_in': total_in,
        'total_out': total_out,
        'total_volume': total_volume,
        'total_transactions': Transaction.objects.count(),
    }
    return render(request, 'core/admin_dashboard.html', context)


@admin_required
def admin_users_list(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )

    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'core/admin_users.html', context)


@admin_required
def admin_user_toggle_active(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('admin_users_list')

    if request.method == 'POST':
        target_user.is_active = not target_user.is_active
        target_user.save()

    return redirect('admin_users_list')


@admin_required
def admin_user_delete(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return redirect('admin_users_list')

    if request.method == 'POST':
        target_user.delete()

    return redirect('admin_users_list')