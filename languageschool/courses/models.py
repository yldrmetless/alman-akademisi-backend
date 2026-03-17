from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

LEVEL_CHOICES = (
    ('A1', 'A1'),
    ('A2', 'A2'),
    ('B1', 'B1'),
    ('B2', 'B2'),
    ('C1', 'C1'),
    ('C2', 'C2'),
)

class LevelExam(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='A1')
    time_limit = models.PositiveIntegerField(default=15)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ExamQuestion(models.Model):
    QUESTION_TYPES = (
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('fill_in_the_blanks', 'Fill in the Blanks'),
    )

    level = models.ForeignKey(LevelExam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single_choice')
    
    audio_url = models.URLField(max_length=500, null=True, blank=True)
    audio_public_id = models.CharField(max_length=255, null=True, blank=True)
    
    options = models.JSONField() 
    
    order = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.level.name} - {self.question_text[:30]}"

class ExamResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    guest_full_name = models.CharField(max_length=255, null=True, blank=True)
    session_key = models.CharField(max_length=255, null=True, blank=True)
    
    exam = models.ForeignKey(LevelExam, on_delete=models.CASCADE)
    
    total_questions = models.PositiveIntegerField()
    correct_count = models.PositiveIntegerField()
    wrong_count = models.PositiveIntegerField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    user_responses = models.JSONField()
    is_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.user.username if self.user else (self.guest_full_name or "Guest")
        return f"{name} - {self.exam.name} - {self.score}"
    
    
    



class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



COURSE_TYPE_CHOICES = [
    ('online', 'Online'),
    ('offline', 'Offline'),
    ('private', 'Private'),
]

LEVEL_CHOICES = [
    ('A1', 'A1'),
    ('A2', 'A2'),
    ('B1', 'B1'),
    ('B2', 'B2'),
    ('C1', 'C1'),
    ('C2', 'C2'),
]

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image_public_id = models.CharField(max_length=255, blank=True, null=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    type = models.CharField(
        max_length=10, 
        choices=COURSE_TYPE_CHOICES, 
        default='online'
    )
    level = models.CharField(
        max_length=2, 
        choices=LEVEL_CHOICES, 
        default='A1'
    )
    
    category = models.ForeignKey(
        CourseCategory, 
        on_delete=models.SET_NULL, 
        related_name='courses', 
        null=True, 
        blank=True
    )
    
    quota = models.PositiveIntegerField(default=0)
    
    start_date = models.DateTimeField(null=True, blank=True)
    
    end_date = models.DateTimeField(null=True, blank=True)  
    
    start_time = models.TimeField(null=True, blank=True)
    
    end_time = models.TimeField(null=True, blank=True)
    
    education_link = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    is_deleted = models.BooleanField(default=False)
    
    first_day = models.CharField(max_length=20, null=True, blank=True)
    
    last_day = models.CharField(max_length=20, null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=(
            ('upcoming', 'Yakında Başlayacak'),
            ('ongoing', 'Devam Ediyor'),
            ('completed', 'Tamamlandı')
        ),
        default='upcoming'
    )
    
    is_private_lesson = models.BooleanField(default=False)
    
    is_link_send = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.level}"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['-created_at']
        
        

class CourseTag(models.Model):
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='tags'
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.course.name} - {self.name}"
    



class CourseOrder(models.Model):
    ORDER_STATUS = (
        ('pending', 'Ödeme Bekliyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Hatalı'),
        ('refund_requested', 'İade Talep Edildi'),
        ('refunded', 'İade Edildi'),
    )

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='course_orders'
    )
    course = models.ForeignKey(
        'Course', 
        on_delete=models.PROTECT, 
        related_name='orders'
    )

    merchant_oid = models.CharField(max_length=64, unique=True, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    error_msg = models.TextField(null=True, blank=True)
    refund_requested = models.BooleanField(default=False)
    refund_reason = models.TextField(null=True, blank=True)
    refund_status = models.CharField(
        max_length=20, 
        choices=(
            ('none', 'Talep Yok'),
            ('pending', 'Beklemede'),
            ('approved', 'Onaylandı'),
            ('rejected', 'Reddedildi')
        ),
        default='none'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_link_send = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.merchant_oid:
            self.merchant_oid = f"CRS{uuid.uuid4().hex[:17].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.merchant_oid} - {self.course.name} ({self.status})"

    class Meta:
        verbose_name = "Course Order"
        verbose_name_plural = "Course Orders"
        ordering = ['-created_at']