from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import (
    MyCourseOrderSerializer,
    MyDigitalProductsOrderSerializer,
    RegisterSerializer,
    LoginSerializer,
    EditProfileSerializer,
    StudentListSerializer,
    SupportListSerializer,
    SupportSerializer,
    SupportStatusUpdateSerializer,
    UserProfileSerializer,
    GoogleReviewSerializer,
    YouTubeLinkSerializer
)
from users.models import GoogleReview, SupportModel, YouTubeLink
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Avg
from users.models import Users
from users.permissions import IsAdminUserType
from blog.paginations import Pagination10
from courses.models import CourseOrder
from products.models import DigitalProductOrder
from django.utils import timezone
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.hashers import make_password

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Kullanıcı başarıyla kayıt oldu.", "status": 201},
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            minutes = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds() // 60)

            return Response(
                {
                    "access": str(access),
                    "refresh": str(refresh),
                    "expires_time": minutes,
                },
                status=status.HTTP_200_OK,
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('username_or_email')

        if not identifier:
            return Response(
                {"error": "Lütfen kullanıcı adı veya e-posta giriniz."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Users.objects.get(Q(username=identifier) | Q(email=identifier))
            
            if not user.email:
                return Response(
                    {"error": "Bu kullanıcıya tanımlı bir e-posta adresi bulunamadı."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            subject = "Şifre Yenileme Talebi"
            
            reset_link = f"{settings.FRONTEND_URL}/reset-password?email={user.email}"
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username

            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
                <h2 style="color: #007bff;">Şifre Yenileme</h2>
                <p>Merhaba <strong>{full_name}</strong>,</p>
                <p>Hesabınız için şifre yenileme talebinde bulunuldu. Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Şifremi Sıfırla
                    </a>
                </div>
                <p>Eğer bu talebi siz yapmadıysanız, lütfen bu e-postayı dikkate almayınız.</p>
                <p style="font-size: 12px; color: #777;">Bağlantı linki: <br>{reset_link}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <small>Alman Akademisi Güvenlik Ekibi</small>
            </div>
            """

            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )

            email_obj = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                connection=connection
            )
            email_obj.content_subtype = "html"
            email_obj.send()

            return Response(
                {"message": "Şifre yenileme bağlantısı e-posta adresinize gönderildi."}, 
                status=status.HTTP_200_OK
            )

        except Users.DoesNotExist:
            return Response(
                {"error": "Girdiğiniz bilgilere ait bir kullanıcı bulunamadı."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Mail gönderimi sırasında hata oluştu: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

class ResetPasswordConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # 1. Temel boş alan kontrolleri
        if not email or not new_password or not confirm_password:
            return Response(
                {"error": "E-posta ve şifre alanları zorunludur."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Şifre eşleşme kontrolü
        if new_password != confirm_password:
            return Response(
                {"error": "Şifreler birbiriyle eşleşmiyor."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Şifre uzunluk kontrolü (isteğe bağlı)
        if len(new_password) < 6:
            return Response(
                {"error": "Şifre en az 6 karakter olmalıdır."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Users.objects.get(email=email)
            
            # 4. Şifreyi hashleyerek güncelle
            user.password = make_password(new_password)
            user.save()

            return Response(
                {"message": "Şifreniz başarıyla güncellendi. Yeni şifrenizle giriş yapabilirsiniz."}, 
                status=status.HTTP_200_OK
            )

        except Users.DoesNotExist:
            return Response(
                {"error": "Geçersiz e-posta adresi."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Bir hata oluştu: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    

class EditProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = EditProfileSerializer(instance=request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profil başarıyla güncellendi.", "status": 200},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class MyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        
        return Response(serializer.data)
    


class GoogleReviewListView(APIView):
    def get(self, request):
        queryset = GoogleReview.objects.filter(is_visible=True).order_by('id')
        serializer = GoogleReviewSerializer(queryset, many=True)
        
        avg_rating = queryset.aggregate(Avg('rating'))['rating__avg'] or 0
        formatted_avg = round(float(avg_rating), 1)
        
        return Response({
            "average_rating": formatted_avg,
            "count": queryset.count(),
            "results": serializer.data
        })
        
        

class StudentListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        students = Users.objects.filter(
            user_type='student', 
            is_deleted=False
        ).order_by('-date_joined')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(students, request)
        
        if page is not None:
            serializer = StudentListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)
    


class YouTubeLinkCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = YouTubeLinkSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Video link created successfully.",
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class YouTubeLinkListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination10

    def get(self, request):
        links = YouTubeLink.objects.filter(
            is_deleted=False, 
            is_active=True
        ).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(links, request)
        
        if page is not None:
            serializer = YouTubeLinkSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = YouTubeLinkSerializer(links, many=True)
        return Response(serializer.data)
    

class YouTubeLinkUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            link_instance = YouTubeLink.objects.get(id=id, is_deleted=False)
        except YouTubeLink.DoesNotExist:
            return Response(
                {"message": "Link not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_deleted_payload = request.data.get('is_deleted')

        if is_deleted_payload is True:
            link_instance.is_deleted = True
            link_instance.save()
            return Response(
                {"message": "Link marked as deleted successfully."}, 
                status=status.HTTP_200_OK
            )

        serializer = YouTubeLinkSerializer(link_instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Link updated successfully.",
                    "data": serializer.data
                }, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class StudentDashAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        total_products_count = DigitalProductOrder.objects.filter(
            user=user,
            status='completed',
            product__is_deleted=False
        ).count()

        completed_course_count = CourseOrder.objects.filter(
            user=user,
            status='completed',
            course__is_deleted=False,
            course__end_date__lt=now.date()
        ).count()

        course_orders_total = CourseOrder.objects.filter(
            user=user,
            status='completed',
            course__is_deleted=False
        ).count()
        
        total_orders_count = total_products_count + course_orders_total

        return Response({
            "total_orders_count": total_orders_count,
            "total_products_count": total_products_count,
            "completed_course_count": completed_course_count
        })
        
        

class MyCourseOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination10

    def get(self, request):
        user = request.user
        
        orders = CourseOrder.objects.filter(
            user=user,
            course__is_deleted=False
        ).select_related('course').order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        if page is not None:
            serializer = MyCourseOrderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = MyCourseOrderSerializer(orders, many=True)
        return Response(serializer.data)
    


class MyDigitalProductsOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination10

    def get(self, request):
        user = request.user
        
        orders = DigitalProductOrder.objects.filter(
            user=user,
            product__is_deleted=False
        ).select_related('product').order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        if page is not None:
            serializer = MyDigitalProductsOrderSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = MyDigitalProductsOrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    

class UserAddressUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        address_payload = request.data.get('address_data')

        if not address_payload:
            return Response(
                {"message": "Address data is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(address_payload, dict):
            return Response(
                {"message": "Address data must be a valid JSON object."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user.address_data = address_payload
        user.save()

        return Response(
            {
                "message": "Address updated successfully.",
                "address_data": user.address_data
            }, 
            status=status.HTTP_200_OK
        )
        

class UserAddressGetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        return Response(
            {
                "id": user.id,
                "address_data": user.address_data if user.address_data else {}
            }, 
            status=status.HTTP_200_OK
        )
        

class UserAddressDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            return Users.objects.get(id=id, is_deleted=False)
        except Users.DoesNotExist:
            return None

    def get(self, request, id):
        target_user = self.get_object(id)
        if not target_user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": target_user.id,
            "address_data": target_user.address_data if target_user.address_data else {}
        })

    def patch(self, request, id):
        target_user = self.get_object(id)
        if not target_user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if "address_data" in request.data and (request.data.get("address_data") is None or request.data.get("address_data") == {}):
            target_user.address_data = None
            target_user.save()
            return Response({"message": "Address deleted successfully."}, status=status.HTTP_200_OK)

        new_address_data = request.data.get("address_data")
        if new_address_data:
            if not isinstance(new_address_data, dict):
                return Response({"message": "Invalid format."}, status=status.HTTP_400_BAD_REQUEST)

            target_user.address_data = new_address_data
            target_user.save()
            
            return Response({
                "message": "Address updated successfully.",
                "address_data": target_user.address_data
            })

        return Response({"message": "No data provided."}, status=status.HTTP_400_BAD_REQUEST)
    
class CreateSupportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SupportSerializer(data=request.data)
        
        if serializer.is_valid():
            full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            user_phone = getattr(request.user, 'phone', None)
            
            instance = serializer.save(
                email=request.user.email,
                name=full_name,
                phone=user_phone
            )

            try:
                subject = f"Destek Talebi Alındı: {instance.priority.upper()}"
                
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd;">
                    <h2 style="color: #007bff;">Alman Akademisi</h2>
                    <p>Merhaba <strong>{full_name}</strong>,</p>
                    <p>Mesajınız bize ulaştı. En kısa sürede dönüş yapacağız.</p>
                    <div style="background: #f4f4f4; padding: 15px; border-left: 5px solid #007bff;">
                        <strong>Mesajınız:</strong><br>
                        {instance.message}
                    </div>
                    <br>
                    <p>Öncelik: {instance.priority.capitalize()}</p>
                    <p>Telefon: {user_phone or 'Belirtilmemiş'}</p>
                    <small>Talep ID: #{instance.id}</small>
                </div>
                """
                
                connection = get_connection(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                )

                email = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[request.user.email],
                    connection=connection
                )
                email.content_subtype = "html"
                email.send()
                    
            except Exception as e:
                print(f"MAİL HATASI: {str(e)}")

            return Response(
                {"message": "Destek talebiniz alındı, mail kutunuzu kontrol edin.", "id": instance.id}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



class CreateInfoRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SupportSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            is_auth = user.is_authenticated
            
            email = request.data.get('email') or (user.email if is_auth else None)
            first_name = request.data.get('first_name') or (user.first_name if is_auth else None)
            last_name = request.data.get('last_name') or (user.last_name if is_auth else None)
            phone = request.data.get('phone') or (getattr(user, 'phone', None) if is_auth else None)
            
            full_name = request.data.get('name')
            if not full_name:
                if is_auth:
                    full_name = f"{first_name} {last_name}".strip() or user.username
                else:
                    full_name = "Ziyaretçi"

            instance = serializer.save(
                email=email,
                name=full_name,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            recipient_list = [email] if email else [settings.DEFAULT_FROM_EMAIL]

            try:
                subject = f"Yeni Bilgi Talebi: {instance.priority.upper()} - {full_name}"
                
                whatsapp_status = "Evet" if instance.is_whatsapp else "Hayır"
                phone_status = "Evet" if instance.is_phone else "Hayır"

                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd;">
                    <h2 style="color: #007bff;">Alman Akademisi - Bilgi Talebi Bilgilendirmesi</h2>
                    <p>Sistemde yeni bir talep oluşturuldu.</p>
                    <div style="background: #f4f4f4; padding: 15px; border-left: 5px solid #007bff;">
                        <strong>Talep Sahibi:</strong> {full_name}<br>
                        <strong>E-posta:</strong> {email or 'Belirtilmemiş'}<br>
                        <strong>Telefon:</strong> {phone or 'Belirtilmemiş'}<br>
                        <hr style="border: 0; border-top: 1px solid #ccc; margin: 10px 0;">
                        <strong>İletişim Tercihleri:</strong><br>
                        - WhatsApp: {whatsapp_status}<br>
                        - Telefon: {phone_status}<br>
                        <hr style="border: 0; border-top: 1px solid #ccc; margin: 10px 0;">
                        <strong>Mesaj:</strong><br>
                        {instance.message}
                    </div>
                    <br>
                    <p>Öncelik: {instance.priority.capitalize()}</p>
                    <small>Talep ID: #{instance.id}</small>
                </div>
                """
                
                connection = get_connection(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                )

                email_obj = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=recipient_list,
                    connection=connection
                )
                email_obj.content_subtype = "html"
                email_obj.send()
            except Exception as e:
                print(f"MAİL HATASI: {str(e)}")

            return Response(
                {"message": "Talebiniz başarıyla alındı.", "id": instance.id}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SupportListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        status_filter = request.query_params.get('status')
        ordering = request.query_params.get('ordering', '-created_at')
        
        if ordering not in ['created_at', '-created_at']:
            ordering = '-created_at'
            
        support_requests = SupportModel.objects.all()

        if status_filter in ['open', 'in_progress', 'closed']:
            support_requests = support_requests.filter(status=status_filter)

        support_requests = support_requests.order_by(ordering)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(support_requests, request)
        
        if page is not None:
            serializer = SupportListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SupportListSerializer(support_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class UserSupportListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination10

    def get(self, request):
        status_filter = request.query_params.get('status')
        ordering = request.query_params.get('ordering', '-created_at')
        
        if ordering not in ['created_at', '-created_at']:
            ordering = '-created_at'
        
        support_requests = SupportModel.objects.filter(email=request.user.email)

        if status_filter in ['open', 'in_progress', 'closed']:
            support_requests = support_requests.filter(status=status_filter)

        support_requests = support_requests.order_by(ordering)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(support_requests, request)
        
        if page is not None:
            serializer = SupportListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SupportListSerializer(support_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupportUpdateStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            support_request = SupportModel.objects.get(id=id)
        except SupportModel.DoesNotExist:
            return Response(
                {"message": "Kayıt bulunamadı."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SupportStatusUpdateSerializer(
            support_request, 
            data=request.data, 
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Talep durumu başarıyla güncellendi.",
                    "id": support_request.id,
                    "new_status": support_request.status
                },
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)