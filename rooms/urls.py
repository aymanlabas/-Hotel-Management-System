from django.urls import path
from rooms import views, admin_views

urlpatterns = [
    # Client URLs
    path('', views.home, name='home'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('reservations/', views.user_reservations, name='user_reservations'),
    path('reserve/<int:room_id>/', views.reserve_room, name='reserve_room'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('contact/', views.contact, name='contact'),
    
    # Admin URLs
    path('admin/login/', admin_views.admin_login, name='admin_login'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', admin_views.admin_user_management, name='admin_user_management'),
    path('admin/users/toggle/<int:user_id>/', admin_views.admin_toggle_user, name='admin_toggle_user'),
    path('admin/rooms/add/', admin_views.admin_add_room, name='admin_add_room'),
    path('admin/rooms/edit/<int:room_id>/', admin_views.admin_edit_room, name='admin_edit_room'),
    path('admin/rooms/delete/<int:room_id>/', admin_views.admin_delete_room, name='admin_delete_room'),
    path('admin/reservations/update/<int:reservation_id>/', admin_views.admin_update_reservation, name='admin_update_reservation'),
    path('admin/export/', admin_views.export_reports, name='admin_export_reports'),
]