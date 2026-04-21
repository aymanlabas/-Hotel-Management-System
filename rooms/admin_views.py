from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth import get_user_model
from .models import Room, Reservation
import json
import csv
from django.http import HttpResponse

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    today = timezone.now()
    
    # Basic stats
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(is_available=True).count()
    total_users = User.objects.count()
    total_clients = User.objects.filter(role='client').count()
    
    # Reservation stats
    active_reservations = Reservation.objects.filter(
        status='confirmed',
        check_out_date__gte=today
    ).count()
    
    total_revenue = Reservation.objects.filter(
        status='confirmed'
    ).aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    pending_checkins = Reservation.objects.filter(
        status='confirmed',
        check_in_date=today.date()
    ).count()
    
    today_checkins = Reservation.objects.filter(
        status='confirmed',
        check_in_date=today.date()
    ).count()
    
    # Monthly revenue data for the chart (last 6 months)
    months = 6
    monthly_revenue = []
    for i in range(months):
        date = today - timedelta(days=30 * i)
        revenue = Reservation.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month,
            status='confirmed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        monthly_revenue.append({
            'month': date.strftime('%B'),
            'revenue': float(revenue)  # Convert Decimal to float for JSON serialization
        })
    
    # Get rooms for management
    rooms = Room.objects.all().order_by('room_number')
    
    # Get recent reservations
    recent_reservations = Reservation.objects.all().order_by('-created_at')[:10]
    
    # Add status colors for badges
    status_colors = {
        'pending': 'warning',
        'confirmed': 'success',
        'cancelled': 'danger',
        'completed': 'info'
    }
    for reservation in recent_reservations:
        reservation.status_color = status_colors.get(reservation.status, 'secondary')
    
    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'total_users': total_users,
        'total_clients': total_clients,
        'active_reservations': active_reservations,
        'total_revenue': total_revenue,
        'pending_checkins': pending_checkins,
        'today_checkins': today_checkins,
        'monthly_revenue': json.dumps(monthly_revenue),  # Convert to JSON string
        'rooms': rooms,
        'recent_reservations': recent_reservations,
    }
    
    return render(request, 'admin/dashboard.html', context)

def admin_login(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'admin':
            login(request, user)
            messages.success(request, 'Welcome back, Admin!')
            return redirect('admin_dashboard')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'admin/login.html')

@user_passes_test(is_admin, login_url='admin_login')
def admin_user_management(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/users.html', {'users': users})

@user_passes_test(is_admin, login_url='admin_login')
def admin_toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.role != 'admin':  # Prevent deactivating admins
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} has been {status}.')
    else:
        messages.error(request, 'Admin users cannot be deactivated.')
    return redirect('admin_user_management')

@user_passes_test(is_admin, login_url='admin_login')
def admin_add_room(request):
    if request.method == 'POST':
        try:
            number = request.POST.get('number')
            room_type = request.POST.get('room_type')
            price = request.POST.get('price')
            capacity = request.POST.get('capacity')
            description = request.POST.get('description')
            image = request.FILES.get('image')
            amenities_list = request.POST.getlist('amenities[]')
            
            if Room.objects.filter(room_number=number).exists():
                messages.error(request, f'Room {number} already exists.')
                return render(request, 'admin/add_room.html')
            
            # Create amenities dictionary
            amenities = {
                'wifi': 'wifi' in amenities_list,
                'tv': 'tv' in amenities_list,
                'ac': 'ac' in amenities_list,
                'minibar': 'minibar' in amenities_list
            }
            
            # Create room
            room = Room.objects.create(
                room_number=number,
                room_type=room_type,
                price=price,
                capacity=capacity,
                description=description,
                amenities=amenities,
                is_available=True
            )
            
            if image:
                room.image = image
                room.save()
            
            messages.success(request, f'Room {number} has been added successfully.')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error adding room: {str(e)}')
            return render(request, 'admin/add_room.html')
    
    return render(request, 'admin/add_room.html')

@user_passes_test(is_admin, login_url='admin_login')
def admin_edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        try:
            number = request.POST.get('number')
            if Room.objects.filter(room_number=number).exclude(id=room_id).exists():
                messages.error(request, f'Room {number} already exists.')
            else:
                try:
                    amenities = request.POST.get('amenities', '{}')
                    amenities_dict = json.loads(amenities)
                    
                    room.room_number = number
                    room.room_type = request.POST.get('room_type')
                    room.price = request.POST.get('price')
                    room.capacity = request.POST.get('capacity')
                    room.description = request.POST.get('description')
                    room.amenities = amenities_dict
                    
                    # Handle image upload
                    if 'image' in request.FILES:
                        room.image = request.FILES['image']
                    
                    room.save()
                    
                    messages.success(request, f'Room {number} has been updated successfully.')
                    return redirect('admin_dashboard')
                except (ValueError, json.JSONDecodeError):
                    messages.error(request, 'Invalid amenities format. Please provide valid JSON.')
        except Exception as e:
            messages.error(request, f'Error updating room: {str(e)}')
    
    # Pass the current room data to the template
    context = {
        'room': room,
        'amenities': room.amenities
    }
    return render(request, 'admin/edit_room.html', context)

@user_passes_test(is_admin, login_url='admin_login')
def admin_delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if Reservation.objects.filter(room=room, status='confirmed').exists():
        messages.error(request, f'Room {room.room_number} has active reservations and cannot be deleted.')
    else:
        room_number = room.room_number
        room.delete()
        messages.success(request, f'Room {room_number} has been deleted successfully.')
    return redirect('admin_dashboard')

@user_passes_test(is_admin, login_url='admin_login')
def admin_update_reservation(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        action = request.POST.get('action')
        
        if action == 'confirm' and reservation.status == 'pending':
            reservation.status = 'confirmed'
            messages.success(request, f'Reservation #{reservation_id} has been confirmed.')
        
        elif action == 'cancel' and reservation.status not in ['cancelled', 'completed']:
            reservation.status = 'cancelled'
            messages.success(request, f'Reservation #{reservation_id} has been cancelled.')
        
        elif action == 'complete' and reservation.status == 'confirmed':
            reservation.status = 'completed'
            messages.success(request, f'Reservation #{reservation_id} has been marked as completed.')
        
        reservation.save()
    
    return redirect('admin_dashboard')

@user_passes_test(is_admin, login_url='admin_login')
def export_reports(request):
    report_type = request.GET.get('type', 'reservations')
    
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'reservations':
        # Export reservations report
        writer.writerow(['Reservation ID', 'Room', 'Guest', 'Check-in', 'Check-out', 'Status', 'Total Price', 'Created At'])
        reservations = Reservation.objects.all().order_by('-created_at')
        
        for reservation in reservations:
            writer.writerow([
                reservation.id,
                reservation.room.room_number,
                reservation.user.username,
                reservation.check_in_date,
                reservation.check_out_date,
                reservation.status,
                reservation.total_price,
                reservation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif report_type == 'rooms':
        # Export rooms report
        writer.writerow(['Room Number', 'Type', 'Capacity', 'Price', 'Status', 'Total Reservations'])
        rooms = Room.objects.annotate(
            total_reservations=Count('reservation')
        ).order_by('room_number')
        
        for room in rooms:
            writer.writerow([
                room.room_number,
                room.room_type,
                room.capacity,
                room.price,
                'Available' if room.is_available else 'Not Available',
                room.total_reservations
            ])
    
    elif report_type == 'revenue':
        # Export revenue report
        writer.writerow(['Month', 'Total Revenue', 'Number of Reservations'])
        today = timezone.now()
        
        for i in range(12):  # Last 12 months
            date = today - timedelta(days=30 * i)
            month_reservations = Reservation.objects.filter(
                created_at__year=date.year,
                created_at__month=date.month,
                status='confirmed'
            )
            
            revenue = month_reservations.aggregate(total=Sum('total_price'))['total'] or 0
            count = month_reservations.count()
            
            writer.writerow([
                date.strftime('%B %Y'),
                revenue,
                count
            ])
    
    return response
