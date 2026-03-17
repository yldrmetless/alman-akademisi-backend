from django.urls import path
from blog.cloudinary_upload import CloudinaryUploadAPIView
from blog.views import (
    BlogEditAPIView,
    BlogPostCreateAPIView,
    BlogPostDetailAPIView,
    BlogPostListAPIView,
    CategoryCreateAPIView,
    CategoryListAPIView,
    CategoryUpdateAPIView,
    CertificateCreate,
    CertificateListAPIView,
    CourseGalleryCreate,
    CourseGalleryListAPIView,
    WebPageContentCreate,
    WebPageContentDetailAPIView,
    WebPageContentListAPIView
)

urlpatterns = [
    path('cloudinary-upload/', CloudinaryUploadAPIView.as_view(), name='cloudinary_upload'),
    
    path('category-create/', CategoryCreateAPIView.as_view(), name='category_create'),
    
    path('category-list/', CategoryListAPIView.as_view(), name='category_list'),
    
    path('category-update/<int:id>/', CategoryUpdateAPIView.as_view(), name='category_update'),
    
    path('blog-post-create/', BlogPostCreateAPIView.as_view(), name='blog_post_create'),
    
    path('blog-post-list/', BlogPostListAPIView.as_view(), name='blog_post_list'),
    
    path('blog-post-detail/<int:id>/', BlogPostDetailAPIView.as_view(), name='blog_post_detail'),
    
    path('blog-edit/<int:id>/', BlogEditAPIView.as_view(), name='blog_edit'),
    
    path('webpage-content-create/', WebPageContentCreate.as_view(), name='webpage_content_create'),
    
    path('webpage-content-list/', WebPageContentListAPIView.as_view(), name='webpage_content_list'),
    
    path("webpage-content/<int:id>/", WebPageContentDetailAPIView.as_view(), name="webpage-content-detail"),
    
    path("course-gallery-create/", CourseGalleryCreate.as_view(), name="course-gallery"),
    
    path("course-gallery-list/", CourseGalleryListAPIView.as_view(), name="course-gallery-list"),
    
    path("certificate-create/", CertificateCreate.as_view(), name="certificate-create"),
    
    path("certificate-list/", CertificateListAPIView.as_view(), name="certificate-list"),
]