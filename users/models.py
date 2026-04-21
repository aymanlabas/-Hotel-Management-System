from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    total_loyalty_points = models.IntegerField(default=0)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    def add_loyalty_points(self, points):
        self.total_loyalty_points += points
        self.save()
    
    def get_loyalty_tier(self):
        if self.total_loyalty_points >= 1000:
            return 'Platinum'
        elif self.total_loyalty_points >= 500:
            return 'Gold'
        elif self.total_loyalty_points >= 100:
            return 'Silver'
        return 'Bronze'
    
    def get_discount_percentage(self):
        tier = self.get_loyalty_tier()
        discounts = {
            'Platinum': 15,
            'Gold': 10,
            'Silver': 5,
            'Bronze': 0
        }
        return discounts[tier]
