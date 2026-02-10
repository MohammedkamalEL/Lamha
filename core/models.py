from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('in', 'وارد'),
        ('out', 'صادر'),
    ]
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
        verbose_name_plural = "العمليات المالية"