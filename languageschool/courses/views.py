import re
import base64, hmac, hashlib, requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminUserType
from courses.serializers import (
    AdminCourseOrderNotificationSerializer,
    CourseCategoryCreateSerializer,
    CourseCategoryEditSerializer,
    CourseCategoryListSerializer,
    CourseEditSerializer,
    CourseListSerializer,
    CourseOrdersListSerializer,
    LevelExamCreateSerializer,
    ExamQuestionListSerializer,
    LevelExamListSerializer,
    LevelExamEditSerializer,
    CourseCreateSerializer,
    CourseOrderCreateSerializer
)
from courses.models import (
    Course,
    CourseCategory,
    LevelExam,
    ExamQuestion,
    Course,
    CourseOrder
)
from rest_framework.permissions import AllowAny
from blog.paginations import Pagination10
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Count, Q
from django.core.mail import EmailMessage


class CreateExamAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = LevelExamCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Sınav ve sorular başarıyla oluşturuldu.",
                    "status": 201,
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LevelExamListAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        level_filter = request.query_params.get('level')
        
        exams = LevelExam.objects.filter(is_deleted=False)

        if level_filter:
            exams = exams.filter(level=level_filter.upper())

        exams = exams.order_by('-created_at')
        
        serializer = LevelExamListSerializer(exams, many=True)
        
        return Response(
            {
                "status": 200,
                "count": exams.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )



class ExamQuestionsListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            exam = LevelExam.objects.get(id=id, is_deleted=False)
        except LevelExam.DoesNotExist:
            return Response(
                {"status": 404, "message": "Sınav bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        questions_queryset = ExamQuestion.objects.filter(
            level=exam, 
            is_deleted=False
        ).order_by('order')

        serializer = ExamQuestionListSerializer(questions_queryset, many=True)
        
        return Response(
            {
                "exam_name": exam.name,
                "description": getattr(exam, 'description', None),
                "time_limit": exam.time_limit,
                "question_count": questions_queryset.count(),
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )
        

class EditExamAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            exam = LevelExam.objects.get(id=id)
        except LevelExam.DoesNotExist:
            return Response({"message": "Sınav bulunamadı."}, status=404)

        serializer = LevelExamEditSerializer(instance=exam, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Sınav başarıyla güncellendi.",
                    "status": 200,
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CreateCourseCategoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = CourseCategoryCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Category created successfully.",
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseCategoryListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination10

    def get(self, request):
        category_name = request.query_params.get('name', None)

        categories = CourseCategory.objects.filter(is_deleted=False).order_by('-created_at')

        if category_name:
            categories = categories.filter(name__icontains=category_name)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(categories, request)
        
        if page is not None:
            serializer = CourseCategoryListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CourseCategoryListSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class EditCourseCategoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            category = CourseCategory.objects.get(id=id)
        except CourseCategory.DoesNotExist:
            return Response(
                {"error": "Category not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        is_deleted_signal = request.data.get('is_deleted', None)
        if is_deleted_signal is True:
            category.is_deleted = True
            category.save()
            return Response(
                {"message": "Category marked as deleted."}, 
                status=status.HTTP_200_OK
            )

        serializer = CourseCategoryEditSerializer(category, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Category updated successfully.",
                    "data": serializer.data
                }, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CreateCourseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Course created successfully.",
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CourseListAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = Pagination10

    def get(self, request):
        search_name = request.query_params.get('name', None)
        filter_level = request.query_params.get('level', None)
        filter_type = request.query_params.get('type', None)
        filter_private = request.query_params.get('is_private_lesson', None)
        ordering = request.query_params.get('ordering', '-created_at')

        courses = Course.objects.filter(is_deleted=False).order_by('-created_at')

        if search_name:
            term = search_name.strip()
            
            def make_regex(text):
                char_map = {
                    'i': '[iİ]', 'İ': '[iİ]',
                    'ı': '[ıI]', 'I': '[ıI]',
                    'ü': '[üÜ]', 'Ü': '[üÜ]',
                    'ö': '[öÖ]', 'Ö': '[öÖ]',
                    'ç': '[çÇ]', 'Ç': '[çÇ]',
                    'ş': '[şŞ]', 'Ş': '[şŞ]',
                    'ğ': '[ğĞ]', 'Ğ': '[ğĞ]'
                }
                pattern = ""
                for char in text:
                    pattern += char_map.get(char, re.escape(char))
                return pattern

            regex_pattern = make_regex(term)
            courses = courses.filter(name__iregex=regex_pattern)
            
        filter_available = request.query_params.get('available', None)
        if filter_available == 'true':
            courses = courses.annotate(
                registered_count=Count('orders', filter=Q(orders__status='completed'))
            ).filter(quota__gt=F('registered_count'))

        if filter_level:
            courses = courses.filter(level=filter_level)

        if filter_type:
            courses = courses.filter(type=filter_type, is_private_lesson=False)

        if filter_private is not None:
            is_private = filter_private.lower() == 'true'
            courses = courses.filter(is_private_lesson=is_private)
            
        if ordering in ['created_at', '-created_at']:
            courses = courses.order_by(ordering)
        else:
            courses = courses.order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(courses, request)
        
        if page is not None:
            serializer = CourseListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class CourseDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, id):
        try:
            course = Course.objects.get(id=id, is_active=True)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseListSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class EditCourseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            course = Course.objects.get(id=id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        is_deleted_signal = request.data.get('is_deleted', None)
        if is_deleted_signal is True:
            course.is_deleted = True
            course.save()
            return Response({"message": "Course marked as deleted successfully."}, status=status.HTTP_200_OK)

        serializer = CourseEditSerializer(course, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Course updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CourseOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CourseOrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=serializer.validated_data['course_id'])
        user = request.user

        final_price = course.discounted_price if course.discounted_price else course.price
        
        order = CourseOrder.objects.create(
            user=user,
            course=course,
            total_amount=final_price,
            status='pending'
        )

        merchant_id = str(settings.PAYTR_MERCHANT_ID)
        merchant_key = settings.PAYTR_MERCHANT_KEY.encode()
        merchant_salt = settings.PAYTR_MERCHANT_SALT

        payment_amount = int(final_price * 100)
        merchant_oid = order.merchant_oid
        user_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        email = user.email
        user_name = f"{user.first_name} {user.last_name}"
        user_address = user.address if user.address else "Adres Belirtilmedi"
        user_phone = user.phone if user.phone else "0000000000"

        basket_content = [[course.name, str(final_price), 1]]
        user_basket = base64.b64encode(str(basket_content).encode()).decode()

        hash_str = (
            merchant_id + user_ip + merchant_oid + email + str(payment_amount) + 
            user_basket + "0" + "0" + "TRY" + "1" + merchant_salt
        )
        paytr_token = base64.b64encode(
            hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()
        ).decode()

        payload = {
            'merchant_id': merchant_id,
            'user_ip': user_ip,
            'merchant_oid': merchant_oid,
            'email': email,
            'payment_amount': payment_amount,
            'paytr_token': paytr_token,
            'user_basket': user_basket,
            'user_name': user_name,
            'user_address': user_address,
            'user_phone': user_phone,
            'merchant_ok_url': "http://localhost:3000/payment-success",
            'merchant_fail_url': "http://localhost:3000/payment-failed",
            'currency': 'TRY',
            'test_mode': 1,
            'no_installment': 0,
            'max_installment': 0,
            'debug_on': 1,
            'timeout_limit': 30,
            'lang': 'tr'
        }

        try:
            response = requests.post(settings.PAYTR_BASE_URL, data=payload, timeout=10)
            res_data = response.json()
            
            if res_data.get('status') == 'success':
                return Response({
                    "token": res_data['token'],
                    "merchant_oid": merchant_oid
                }, status=status.HTTP_200_OK)
            else:
                order.status = 'failed'
                order.error_msg = res_data.get('reason', 'PayTR hatası')
                order.save()
                return Response({"message": res_data.get('reason')}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": "Ödeme başlatılamadı."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

class CourseAdminOrderUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType] 

    def patch(self, request, merchant_oid):
        try:
            order = CourseOrder.objects.get(merchant_oid=merchant_oid)
        except CourseOrder.DoesNotExist:
            return Response({"message": "Kurs siparişi bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        
        if new_status not in dict(CourseOrder.ORDER_STATUS):
            return Response({"message": "Geçersiz durum değeri."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == 'completed' and new_status == 'completed':
            return Response({"message": "Bu sipariş zaten daha önce tamamlanmış."}, status=status.HTTP_200_OK)

        if new_status == 'completed':
            course = order.course
            completed_count = CourseOrder.objects.filter(course=course, status='completed').count()
            
            if course.quota > 0:
                if completed_count >= course.quota:
                    return Response(
                        {"error": "Kurs kontenjanı dolu olduğu için bu sipariş tamamlanamaz."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        order.status = new_status
        order.save()

        serializer = AdminCourseOrderNotificationSerializer(order)
        
        return Response({
            "message": f"Kurs siparişi durumu '{new_status}' olarak güncellendi.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        


class CustomerCourseRefundRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, merchant_oid):
        order = get_object_or_404(CourseOrder, merchant_oid=merchant_oid, user=request.user)
        
        if order.status != 'completed':
            return Response({"message": "Sadece tamamlanmış kurs ödemeleri için iade talebi oluşturulabilir."}, status=400)
            
        time_diff = timezone.now() - order.created_at
        if time_diff > timedelta(days=7):
            return Response({
                "message": "İade süresi (7 gün) dolmuştur. Bu kurs için iade talebi oluşturamazsınız."
            }, status=400)

        if order.course.start_date and order.course.start_date < timezone.now():
            return Response({
                "message": "Kurs başlangıç tarihi geçtiği için iade talebi oluşturulamaz."
            }, status=400)
            
        if order.refund_requested:
            return Response({"message": "Bu kurs için zaten aktif bir iade talebiniz bulunuyor."}, status=400)

        reason = request.data.get('reason')
        if not reason:
            return Response({"message": "Lütfen iade sebebi belirtiniz."}, status=400)

        order.refund_requested = True
        order.refund_reason = reason
        order.refund_status = 'pending'
        order.status = 'refund_requested'
        order.save()

        return Response({
            "message": "Kurs iade talebiniz alınmıştır. Yetkililer tarafından incelenip tarafınıza dönüş yapılacaktır."
        }, status=200)
        


class AdminCourseOrderRefundAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request, merchant_oid):
        order = get_object_or_404(CourseOrder, merchant_oid=merchant_oid)
        
        if order.status != 'refund_requested':
            return Response({"message": "Sadece iade talebi oluşturulmuş kurs siparişleri iade edilebilir."}, status=400)
        
        if settings.DEBUG: 
            order.status = 'refunded'
            order.refund_status = 'approved'
            order.save()

            
            return Response({
                "message": "TEST MODU: Kurs iadesi (PayTR atlanarak) onaylandı. Kontenjan serbest bırakıldı.",
                "status": "success"
            }, status=200)

        merchant_id = settings.PAYTR_MERCHANT_ID
        merchant_key = settings.PAYTR_MERCHANT_KEY.encode()
        merchant_salt = settings.PAYTR_MERCHANT_SALT
        refund_amount = str(int(order.total_amount * 100))
        
        hash_str = merchant_id + merchant_oid + refund_amount + merchant_salt
        paytr_token = base64.b64encode(
            hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()
        ).decode()

        payload = {
            'merchant_id': merchant_id,
            'merchant_oid': merchant_oid,
            'return_amount': refund_amount,
            'paytr_token': paytr_token,
        }

        try:
            res = requests.post("https://www.paytr.com/odeme/iade", data=payload, timeout=10)
            res_data = res.json()
            
            if res_data.get('status') == 'success':
                order.status = 'refunded'
                order.refund_status = 'approved'
                order.save()
                
                return Response({
                    "message": "Kurs iadesi başarıyla onaylandı. Ücret iadesi banka tarafından 1-7 gün içinde yapılacaktır.",
                    "status": "success"
                }, status=200)
            else:
                return Response({
                    "message": f"PayTR İade Hatası: {res_data.get('err_msg', 'Bilinmeyen hata')}"
                }, status=400)

        except Exception as e:
            return Response({"message": f"İade işlemi sırasında sistem hatası oluştu: {str(e)}"}, status=500)
        

class CourseOrdersListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        orders = CourseOrder.objects.all().select_related('user', 'course').order_by('-created_at')
        
        is_private = request.query_params.get('is_private_lesson')
        
        if is_private is not None:
            if is_private.lower() == 'true':
                orders = orders.filter(course__is_private_lesson=True)
            elif is_private.lower() == 'false':
                orders = orders.filter(course__is_private_lesson=False)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        if page is not None:
            serializer = CourseOrdersListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CourseOrdersListSerializer(orders, many=True)
        return Response(serializer.data)
    
    


class SendCourseLinkAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        order_id = request.data.get('order_id')
        course_link = request.data.get('course_link')

        if not order_id or not course_link:
            return Response(
                {"error": "order_id ve course_link alanları zorunludur."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        order_instance = get_object_or_404(CourseOrder, id=order_id)

        if order_instance.status != 'completed':
            return Response(
                {"error": f"Link gönderilemedi. Sipariş durumu: {order_instance.status}."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = order_instance.user
        if not user or not user.email:
            return Response(
                {"error": "Siparişe bağlı kullanıcı veya e-posta adresi bulunamadı."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            subject = "Eğitim Erişim Linkiniz"
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #eee;">
                <h2 style="color: #28a745;">Tebrikler!</h2>
                <p>Merhaba <strong>{full_name}</strong>,</p>
                <p><strong>{order_instance.course.name}</strong> kursuna erişim linkiniz hazır.</p>
                <div style="margin: 20px 0; text-align: center;">
                    <a href="{course_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Eğitime Git
                    </a>
                </div>
                <p>Alternatif link: <br>{course_link}</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <small>Sipariş No: {order_instance.merchant_oid}</small>
            </div>
            """

            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.content_subtype = "html"
            email.send()

            # --- GÜNCELLEME: Sipariş modelindeki alanı true yap ---
            order_instance.is_link_send = True
            order_instance.save()
            # -----------------------------------------------------

            return Response(
                {"message": f"Link {user.email} adresine gönderildi ve sipariş güncellendi."}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Mail hatası: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )