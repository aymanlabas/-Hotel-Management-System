from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Room, Reservation
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

def home(request):
    """Render the home page."""
    return render(request, 'rooms/home.html')

def room_list(request):
    rooms = Room.objects.filter(is_available=True)
    return render(request, 'rooms/room_list.html', {'rooms': rooms})

def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'rooms/room_detail.html', {'room': room})

@login_required
def reserve_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Calculate min and max dates for form
    today = timezone.now().date()
    min_date = today + timezone.timedelta(days=1)  # Tomorrow
    max_date = today + timezone.timedelta(days=365)  # One year from now
    
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        
        # Convert string dates to datetime objects
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # Validate dates
        if check_in_date < today:
            messages.error(request, 'Check-in date cannot be in the past.')
            return redirect('room_detail', room_id=room_id)
        
        if check_out_date <= check_in_date:
            messages.error(request, 'Check-out date must be after check-in date.')
            return redirect('room_detail', room_id=room_id)
        
        # Calculate total price
        days = (check_out_date - check_in_date).days
        total_price = room.price * days
        
        # Check for existing reservations
        conflicting_reservations = Reservation.objects.filter(
            room=room,
            status='confirmed',
            check_in_date__lte=check_out_date,
            check_out_date__gte=check_in_date
        ).exists()
        
        if conflicting_reservations:
            messages.error(request, 'Room is not available for these dates.')
            return redirect('room_detail', room_id=room_id)
        
        # Create reservation
        Reservation.objects.create(
            room=room,
            user=request.user,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            status='confirmed'
        )
        
        messages.success(request, 'Room reserved successfully!')
        return redirect('user_reservations')
    
    context = {
        'room': room,
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d')
    }
    return render(request, 'rooms/reserve.html', context)

@login_required
def user_reservations(request):
    reservations = Reservation.objects.filter(user=request.user)
    return render(request, 'rooms/user_reservations.html', {'reservations': reservations})

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if request.user == reservation.user:
        if reservation.status == 'confirmed':
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, 'Reservation cancelled successfully!')
        else:
            messages.error(request, 'This reservation cannot be cancelled.')
    else:
        messages.error(request, 'You are not authorized to cancel this reservation.')
    
    return redirect('user_reservations')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            send_mail(
                f'Contact Form - {subject}',
                f'Name: {name}\nEmail: {email}\nMessage: {message}',
                email,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again later.')
    
    return render(request, 'rooms/contact.html')
