from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal

class Room(models.Model):
    ROOM_TYPES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    )
    
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField()
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='room_images/', null=True, blank=True)
    amenities = models.JSONField(default=dict)  # Store amenities as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.get_room_type_display()}"

    def get_average_rating(self):
        reviews = self.review_set.all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    loyalty_points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"Reservation for Room {self.room.room_number} "
                f"by {self.user.username}")

    def save(self, *args, **kwargs):
        if not self.pk:  # New reservation
            # Calculate loyalty points (1 point per $10 spent)
            self.loyalty_points_earned = int(self.total_price / 10)
        super().save(*args, **kwargs)

class Review(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['reservation', 'user']  # One review per reservation
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for Room {self.room.room_number}"
