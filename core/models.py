from django.db import models
from django.contrib.auth.models import User
<<<<<<< HEAD
=======
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.dispatch import receiver


>>>>>>> 9a7726ff3c79aedd394968656331281de038becf

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('in', 'وارد'),
        ('out', 'صادر'),
    ]
<<<<<<< HEAD
=======
    
>>>>>>> 9a7726ff3c79aedd394968656331281de038becf
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="المبلغ")
    ref_last_4 = models.CharField(max_length=4, verbose_name="آخر 4 أرقام")
    transaction_date = models.DateField(verbose_name="تاريخ الإشعار")
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, verbose_name="النوع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"

    class Meta:
        db_table = 'transactions'
        verbose_name = "عملية مالية"
<<<<<<< HEAD
        verbose_name_plural = "العمليات المالية"
=======
        verbose_name_plural = "العمليات المالية"


class UserSettings(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    alert_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    
    use_currency_symbols = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"إعدادات الحساب لـ {self.user.username}"

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
>>>>>>> 9a7726ff3c79aedd394968656331281de038becf
