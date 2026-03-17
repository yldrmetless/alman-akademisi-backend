from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

USER_TYPE_CHOICES = (
    ('student', 'Student'),
    ('admin', 'Admin'),
)

class Users(AbstractUser):
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    
    is_deleted = models.BooleanField(default=False)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    address_data = models.JSONField(null=True, blank=True)
    
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    
    avatar_url_id = models.CharField(max_length=255, null=True, blank=True)
    
    card_data = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.username



class GoogleReview(models.Model):
    author_name = models.CharField(max_length=255)
    author_avatar_url = models.URLField(max_length=500, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()
    review_text = models.TextField()
    review_date = models.CharField(max_length=100)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('author_name', 'review_text')

    def __str__(self):
        return f"{self.author_name} - {self.rating} Yıldız"
    


LINK_TYPE_CHOICES = (
    ('lesson', 'Lesson'),
    ('think', 'Think'),
)

class YouTubeLink(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    youtube_url = models.URLField(max_length=500)
    
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    type = models.CharField(max_length=50, null=True, blank=True, choices=LINK_TYPE_CHOICES)

    def __str__(self):
        return self.name

    @property
    def video_id(self):
        if "v=" in self.youtube_url:
            return self.youtube_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in self.youtube_url:
            return self.youtube_url.split("youtu.be/")[1]
        return None

    class Meta:
        verbose_name = "YouTube Link"
        verbose_name_plural = "YouTube Links"
        ordering = ['-created_at']
        


PRIORITY_CHOICES = (
    ('low', 'Low'),
    ('normal', 'Normal'),
    ('high', 'High'),
)        

STATUS_CHOICES = (
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('closed', 'Closed'),
)

class SupportModel(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image_url_id = models.CharField(max_length=255, null=True, blank=True)
    priority = models.CharField(max_length=20, default='normal')
    status = models.CharField(max_length=20, default='open', choices=STATUS_CHOICES)
    is_whatsapp = models.BooleanField(default=False)
    is_phone = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.email}"