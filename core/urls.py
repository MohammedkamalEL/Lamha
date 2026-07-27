from django.urls import path
from .views import (
    HomeView, DashboardView, UploadView, ProfileUpdateView, UserDeleteView,
    ProcessNotificationView, SaveTransactionView,
    admin_dashboard, admin_users_list, admin_user_toggle_active, admin_user_delete,
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('process-notification/', ProcessNotificationView.as_view(), name='process_notification'),
    path('save-transaction/', SaveTransactionView.as_view(), name='save_transaction'),

    # Admin
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', admin_users_list, name='admin_users_list'),
    path('admin-panel/users/<int:user_id>/toggle/', admin_user_toggle_active, name='admin_user_toggle'),
    path('admin-panel/users/<int:user_id>/delete/', admin_user_delete, name='admin_user_delete'),
]