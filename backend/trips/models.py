# trips/models.py
from django.db import models
# from django.contrib.auth.models import User
from django.conf import settings 
User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    current_location = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    profession = models.CharField(max_length=100, blank=True, null=True)
    photos = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='')
    
    def __str__(self):
        return self.name

class Trip(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_trips')
    group_name = models.CharField(max_length=100)
    destination = models.ForeignKey(City, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Budget per person in INR")
    min_age = models.IntegerField()
    max_age = models.IntegerField()
    required_members = models.IntegerField()
    members = models.ManyToManyField(User, related_name='joined_trips')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.group_name
    
    def current_members_count(self):
        return self.members.count() + 1  # +1 for the host

class TripItinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itinerary_items')
    day = models.IntegerField()
    description = models.TextField()
    
    def __str__(self):
        return f"{self.trip.group_name} - Day {self.day}"

class JoinRequest(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('trip', 'user')
    
    def __str__(self):
        return f"{self.user.username} -> {self.trip.group_name}"

class ChatMessage(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"