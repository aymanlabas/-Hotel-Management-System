from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'client'  # Set default role as client
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            if user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'users/login.html')

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

def create_admin(request):
    # Check if there's already an admin user
    if User.objects.filter(role='admin').exists():
        messages.error(request, 'Admin user already exists.')
        return redirect('login')
    
    # Create admin user
    admin = User.objects.create_user(
        username='admin',
        password='admin123',
        email='admin@example.com',
        role='admin'
    )
    messages.success(request, 'Admin user created successfully!')
    return redirect('login')
