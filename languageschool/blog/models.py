from django.db import models
from django.utils.text import slugify
from users.models import Users



class Category(models.Model):
    name = models.CharField(max_length=100)
    
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100)
    
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class BlogPost(models.Model):
    author = models.ForeignKey(Users, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=255)
    
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    content = models.TextField()
    
    image_url = models.URLField(max_length=500, null=True, blank=True)
    
    image_public_id = models.CharField(max_length=255, null=True, blank=True)
    
    view_count = models.PositiveIntegerField(default=0)
    
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='category_posts'
    )
    
    tags = models.ManyToManyField(Tag, blank=True, related_name='tag_posts')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_deleted = models.BooleanField(default=False)
    
    deleted_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
        

class BlogViewCount(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, blank=True)
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'blog_post')
        


class WebPageModel(models.Model):
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    
    logo_public_id = models.CharField(max_length=255, null=True, blank=True)
    
    hero_title_first = models.CharField(max_length=255, null=True, blank=True)
    
    hero_title_second = models.CharField(max_length=255, null=True, blank=True)
    
    hero_title_third = models.CharField(max_length=255, null=True, blank=True)
    
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    type = models.CharField(max_length=50, null=True, blank=True)
    


class WebPageHeroImages(models.Model):
    webpage = models.ForeignKey(
        WebPageModel,
        on_delete=models.CASCADE,
        related_name="hero_images"
    )

    image_url = models.URLField(max_length=500)
    image_public_id = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=0)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    


    
    
class CourseGalleryImage(models.Model):
    image_url = models.URLField(max_length=500)
    image_public_id = models.CharField(max_length=255)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    

class CertificateImage(models.Model):
    image_url = models.URLField(max_length=500)
    image_public_id = models.CharField(max_length=255)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)