from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from blog.serializers import (
    BlogPostCreateSerializer,
    BlogPostListSerializer,
    BlogEditSerializer,
    CategoryCreateSerializer,
    CategoryListSerializer,
    CategoryUpdateSerializer,
    CourseGalleryCreateSerializer,
    CourseGalleryListSerializer,
    WebPageContentCreateSerializer,
    WebPageContentListSerializer,
    CertificateCreateSerializer,
    CertificateListSerializer
)
from blog.models import BlogPost, Category, CertificateImage, CourseGalleryImage, WebPageModel
from users.permissions import IsAdminUserType
from rest_framework.generics import ListAPIView, RetrieveAPIView
from blog.models import BlogPost, BlogViewCount
from blog.paginations import Pagination10
from django.db.models import F
from rest_framework.permissions import AllowAny


class CategoryCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Kategori başarıyla oluşturuldu.",
                    "status": 201,
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CategoryListAPIView(ListAPIView):
    """
    Tüm aktif kategorileri en yeniden en eskiye doğru listeler.
    'name' query parametresi ile arama yapabilir.
    """
    permission_classes = [AllowAny]
    serializer_class = CategoryListSerializer
    pagination_class = Pagination10

    def get_queryset(self):
        queryset = Category.objects.filter(is_deleted=False).order_by('-created_at')
        
        category_name = self.request.query_params.get('name')
        
        if category_name:
            queryset = queryset.filter(name__icontains=category_name)
            
        return queryset
    

class CategoryUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response({"message": "Kategori bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategoryUpdateSerializer(instance=category, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Kategori başarıyla güncellendi.",
                    "status": 200,
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BlogPostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = BlogPostCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Blog yazısı başarıyla oluşturuldu.", "status": 201},
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class BlogPostListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BlogPostListSerializer
    pagination_class = Pagination10

    def get_queryset(self):
        queryset = BlogPost.objects.filter(is_deleted=False).order_by('-created_at')
        
        category_name = self.request.query_params.get('category')
        
        if category_name:
            queryset = queryset.filter(categories__name__iexact=category_name)
            
        tag_name = self.request.query_params.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name__iexact=tag_name)
            
        search_title = self.request.query_params.get('title')
        if search_title:
            queryset = queryset.filter(title__icontains=search_title)
            
        ordering = self.request.query_params.get('ordering', '-created_at')
        
        if ordering in ['created_at', '-created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset
    

class BlogPostDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            post = BlogPost.objects.get(id=id, is_deleted=False)
            
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            user = request.user if request.user.is_authenticated else None

            is_admin = user and hasattr(user, 'user_type') and user.user_type == 'admin'

            if not is_admin:
                if user:
                    view_exists = BlogViewCount.objects.filter(user=user, blog_post=post).exists()
                else:
                    view_exists = BlogViewCount.objects.filter(ip_address=ip, blog_post=post, user=None).exists()

                if not view_exists:
                    BlogViewCount.objects.create(user=user, blog_post=post, ip_address=ip)
                    post.view_count = F('view_count') + 1
                    post.save()
                    post.refresh_from_db()

            serializer = BlogPostListSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except BlogPost.DoesNotExist:
            return Response({"message": "Yazı bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        

class BlogEditAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            post = BlogPost.objects.get(id=id, is_deleted=False)
        except BlogPost.DoesNotExist:
            return Response(
                {"message": "Yazı bulunamadı veya zaten silinmiş."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BlogEditSerializer(instance=post, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Blog başarıyla güncellendi.", "status": 200},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class WebPageContentCreate(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = WebPageContentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        webpage = serializer.save()

        return Response({
            "status": 201,
            "message": "Web page content created successfully.",
            "id": webpage.id
        }, status=201)
        

class WebPageContentListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = WebPageContentListSerializer
    pagination_class = Pagination10

    def get_queryset(self):
        queryset = WebPageModel.objects.filter(is_deleted=False)

        type_filter = self.request.query_params.get("type")
        ordering = self.request.query_params.get("ordering", "-created_at")

        if type_filter:
            queryset = queryset.filter(type=type_filter)

        if ordering not in ["created_at", "-created_at"]:
            ordering = "-created_at"

        return queryset.order_by(ordering)
    

class WebPageContentDetailAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = WebPageContentListSerializer
    lookup_field = "id"

    def get_queryset(self):
        return WebPageModel.objects.filter(is_deleted=False)
    

class CourseGalleryCreate(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        gallery_data = request.data.get("images", [])

        if not isinstance(gallery_data, list):
            return Response(
                {"status": 400, "message": "images must be a list"},
                status=400
            )

        CourseGalleryImage.objects.filter(is_deleted=False).update(is_deleted=True)

        serializer = CourseGalleryCreateSerializer(data=gallery_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "status": 201,
                "message": "Gallery images updated successfully"
            },
            status=201
        )
        

class CourseGalleryListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination10

    def get(self, request):
        queryset = CourseGalleryImage.objects.filter(is_deleted=False).order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = CourseGalleryListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CourseGalleryListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



class CertificateCreate(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        gallery_data = request.data.get("images", [])

        if not isinstance(gallery_data, list):
            return Response(
                {"status": 400, "message": "images must be a list"},
                status=400
            )

        CertificateImage.objects.filter(is_deleted=False).update(is_deleted=True)

        serializer = CertificateCreateSerializer(data=gallery_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "status": 201,
                "message": "Gallery images updated successfully"
            },
            status=201
        )
        

class CertificateListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination10

    def get(self, request):
        queryset = CertificateImage.objects.filter(is_deleted=False).order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = CertificateListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CertificateListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)