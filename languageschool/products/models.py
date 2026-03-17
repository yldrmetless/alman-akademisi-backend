from django.db import models
from django.utils.text import slugify
import uuid
from users.models import Users


class DigitalProductCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
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
    

class DigitalProduct(models.Model):
    PRODUCT_TYPES = (
        ('file', 'Dosya (PDF/Kitap)'),
        ('link', 'Dış Bağlantı (Drive/Zoom)'),
        ('manual', 'Manuel Kayıt (Classroom)'),
    )
    
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default='file')
    file_upload = models.FileField(upload_to='digital_products/', null=True, blank=True)
    external_link = models.URLField(max_length=500, null=True, blank=True)
    download_limit = models.PositiveIntegerField(default=5)
    
    stock = models.IntegerField(default=-1)
    
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    category = models.ForeignKey(
        DigitalProductCategory, 
        on_delete=models.SET_NULL, 
        related_name='products', 
        null=True, 
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class DigitalProductImage(models.Model):
    product = models.ForeignKey(
        DigitalProduct, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    digital_product_image_url = models.URLField(max_length=500)
    digital_product_public_id = models.CharField(max_length=255)
    
    order = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"
    


class DigitalProductOrder(models.Model):
    ORDER_STATUS = (
        ('pending', 'Ödeme Bekliyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Hatalı'),
        ('refund_requested', 'İade Talep Edildi'),
        ('refunded', 'İade Edildi'),
    )

    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey('DigitalProduct', on_delete=models.PROTECT)

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
    
    is_link_send = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.merchant_oid:
            self.merchant_oid = str(uuid.uuid4().hex)[:20]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.merchant_oid} - {self.status}"