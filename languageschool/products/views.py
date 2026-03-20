import base64
import hashlib
import hmac
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminUserType
from products.serializers import (
    AdminOrderNotificationSerializer,
    DigitalProductCategoryListSerializer,
    DigitalProductCategorySerializer,
    DigitalProductCreateSerializer,
    DigitalProductDetailSerializer,
    DigitalProductDetailSerializerCustomer,
    DigitalProductEditSerializer,
    OrderAdminListSerializer,
    OrderCreateSerializer,
    ProductsOrderListSerializer
)
from products.models import DigitalProduct, DigitalProductCategory, DigitalProductOrder
from rest_framework.permissions import AllowAny
from blog.paginations import Pagination10
from products.serializers import DigitalProductListSerializer
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
import os
from django.utils import timezone
from datetime import timedelta
from courses.models import Course, CourseOrder
from users.models import Users
from django.db.models import Q,Count, Sum, Value
from django.db.models.functions import TruncMonth,Concat
from django.db import transaction
import json
import time
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import EmailMessage

class DigitalProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    def post(self, request):
        serializer = DigitalProductCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Digital product created successfully with external link.",
                    "status": 201,
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {
                "status": 400,
                "errors": serializer.errors
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )
        

class EditDigitalProduct(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id):
        try:
            product = DigitalProduct.objects.get(id=id)
        except DigitalProduct.DoesNotExist:
            return Response({"error": "Ürün bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DigitalProductEditSerializer(product, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Ürün ve görseller başarıyla güncellendi.",
                "status": 200,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class DigitalProductListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = Pagination10

    def get(self, request):
        search_query = request.query_params.get('search', None)
        
        products = DigitalProduct.objects.filter(is_deleted=False).order_by('-created_at')

        if search_query:
            products = products.filter(name__icontains=search_query)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(products, request)
        
        if page is not None:
            serializer = DigitalProductListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = DigitalProductListSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class DigitalProductDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def get(self, request, id):
        try:
            product = DigitalProduct.objects.get(id=id, is_deleted=False)
        except DigitalProduct.DoesNotExist:
            return Response(
                {"status": 404, "message": "Ürün bulunamadı."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DigitalProductDetailSerializer(product)
        
        return Response(
            {
                "status": 200,
                "data": serializer.data
            }, 
            status=status.HTTP_200_OK
        )
        
class DigitalProductDetailAPIViewCustomer(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            product = DigitalProduct.objects.get(id=id, is_deleted=False)
        except DigitalProduct.DoesNotExist:
            return Response(
                {"status": 404, "message": "Ürün bulunamadı."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DigitalProductDetailSerializerCustomer(product)
        
        return Response(
            {
                "status": 200,
                "data": serializer.data
            }, 
            status=status.HTTP_200_OK
        )
        



class CreateDigitalProductCategory(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request, *args, **kwargs):
        serializer = DigitalProductCategorySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Category created successfully",
                    "data": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class DigitalProdCategoryList(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = Pagination10

    def get(self, request, *args, **kwargs):
        queryset = DigitalProductCategory.objects.filter(is_deleted=False)

        name_filter = request.query_params.get('search', None)
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        ordering = request.query_params.get('ordering', '-created_at')
        if ordering in ['created_at', '-created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = DigitalProductCategoryListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = DigitalProductCategoryListSerializer(queryset, many=True)
        return Response(serializer.data)
        


class UpdateDigitalProductCategory(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, id, *args, **kwargs):
        category = DigitalProductCategory.objects.filter(id=id).first()
        if not category:
            return Response({"message": "Kategori bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DigitalProductCategorySerializer(category, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_instance = serializer.save()
            
            message = "Category updated successfully"
            if updated_instance.is_deleted:
                message = "Category has been marked as deleted (Soft Delete)"

            return Response(
                {
                    "message": message,
                    "data": serializer.data
                }, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class CreateOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = DigitalProduct.objects.get(id=serializer.validated_data['product_id'])
        user = request.user

        final_price = product.discounted_price if product.discounted_price else product.price
        
        order = DigitalProductOrder.objects.create(
            user=user,
            product=product,
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

        basket_content = [[product.name, str(final_price), 1]]
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
            'merchant_ok_url': "https://siteniz.com/payment-success",
            'merchant_fail_url': "https://siteniz.com/payment-failed",
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
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "Ödeme servis sağlayıcısına ulaşılamadı.", "detail": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if res_data.get('status') == 'success':
            return Response({
                "status": "success",
                "token": res_data['token'],
                "merchant_oid": merchant_oid
            }, status=status.HTTP_200_OK)
        else:
            order.status = 'failed'
            order.error_msg = res_data.get('reason', 'PayTR hatası')
            order.save()
            return Response(
                {"error": res_data.get('reason', 'Ödeme başlatılamadı.')}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse

@method_decorator(csrf_exempt, name='dispatch')
class PayTRCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        post_data = request.POST
        
        merchant_oid = post_data.get('merchant_oid')
        status_paytr = post_data.get('status')
        total_amount = post_data.get('total_amount')
        hash_paytr = post_data.get('hash')

        merchant_key = settings.PAYTR_MERCHANT_KEY.encode()
        merchant_salt = settings.PAYTR_MERCHANT_SALT
        
        hash_str = merchant_oid + merchant_salt + status_paytr + total_amount
        calculated_hash = base64.b64encode(
            hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()
        ).decode()

        if hash_paytr != calculated_hash:
            return HttpResponse("PAYTR HASH FAILED", status=400)

        try:
            order = DigitalProductOrder.objects.get(merchant_oid=merchant_oid)
            
            if status_paytr == 'success':
                # Ödeme Başarılı
                order.status = 'completed'
                order.save()
                
            else:
                order.status = 'failed'
                order.error_msg = post_data.get('failed_reason_msg', 'Ödeme başarısız.')
                order.save()

            return HttpResponse("OK")

        except DigitalProductOrder.DoesNotExist:
            return HttpResponse("ORDER NOT FOUND", status=404)

            

class CheckOrderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, merchant_oid):
        try:
            order = DigitalProductOrder.objects.get(
                merchant_oid=merchant_oid, 
                user=request.user
            )
            return Response({
                "status": order.status,
                "product_name": order.product.name,
                "total_amount": order.total_amount,
                "created_at": order.created_at
            })
        except DigitalProductOrder.DoesNotExist:
            return Response({"error": "Sipariş bulunamadı."}, status=404)
        



class AdminOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        orders = DigitalProductOrder.objects.all().order_by('-created_at')
        
        total_count = orders.count()
        successful_orders_revenue = sum(o.total_amount for o in orders if o.status == 'completed')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        serializer = OrderAdminListSerializer(page, many=True)
        
        response = paginator.get_paginated_response(serializer.data)
        response.data['total_orders'] = total_count
        response.data['total_revenue'] = successful_orders_revenue
        
        return response
    
    

class AdminOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        orders = DigitalProductOrder.objects.all().order_by('-created_at')
        
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
            
        total_sales = DigitalProductOrder.objects.filter(status='completed').count()
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        if page is not None:
            serializer = AdminOrderNotificationSerializer(page, many=True)
            response = paginator.get_paginated_response(serializer.data)
            response.data['total_completed_sales'] = total_sales
            return response

        serializer = AdminOrderNotificationSerializer(orders, many=True)
        return Response(serializer.data)


class AdminOrderUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def patch(self, request, merchant_oid):
        try:
            order = DigitalProductOrder.objects.get(merchant_oid=merchant_oid)
        except DigitalProductOrder.DoesNotExist:
            return Response({"message": "Sipariş bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in dict(DigitalProductOrder.ORDER_STATUS):
            return Response({"message": "Geçersiz durum değeri."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == 'completed' and new_status == 'completed':
            return Response({"message": "Sipariş zaten tamamlanmış."}, status=status.HTTP_200_OK)

        if new_status == 'completed':
            product = order.product
            if product.stock is not None:
                if product.stock > 0:
                    product.stock -= 1
                    product.save()
                elif product.stock == 0:
                    return Response({"error": "Ürün stoğu tükendiği için tamamlanamaz."}, status=status.HTTP_400_BAD_REQUEST)
            

        order.status = new_status
        order.save()

        serializer = AdminOrderNotificationSerializer(order)
        return Response({
            "message": f"Sipariş durumu {new_status} olarak güncellendi.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        


class MyDigitalProductsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = DigitalProductOrder.objects.filter(
            user=request.user, 
            status='completed'
        ).select_related('product')

        data = []
        for order in orders:
            product = order.product
            data.append({
                "order_id": order.merchant_oid,
                "product_id": product.id,
                "product_name": product.name,
                "product_type": product.product_type,
                "purchase_date": order.created_at,
                "access_url": product.external_link if product.product_type == 'link' else f"/api/products/download/{order.merchant_oid}/",
                "is_manual": product.product_type == 'manual'
            })
        
        return Response(data)
    


class DownloadDigitalProductAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, merchant_oid):
        order = get_object_or_404(DigitalProductOrder, merchant_oid=merchant_oid, user=request.user, status='completed')
        product = order.product

        if product.product_type != 'file' or not product.file_upload:
            return Response({"error": "Bu ürün indirilebilir bir dosya içermiyor."}, status=400)

        file_path = product.file_upload.path
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        
        raise Http404("Dosya sunucuda bulunamadı.")
    


class CustomerRefundRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, merchant_oid):
        order = get_object_or_404(DigitalProductOrder, merchant_oid=merchant_oid, user=request.user)
        
        if order.status != 'completed':
            return Response({"message": "Sadece tamamlanmış siparişler için iade talebi oluşturulamaz."}, status=400)
            
        time_diff = timezone.now() - order.created_at
        if time_diff > timedelta(days=7):
            return Response({
                "message": "İade süresi (7 gün) dolmuştur. Bu sipariş için iade talebi oluşturamazsınız."
            }, status=400)
            
        if order.refund_requested:
            return Response({"message": "Zaten aktif bir iade talebiniz bulunuyor."}, status=400)

        reason = request.data.get('reason')
        if not reason:
            return Response({"message": "Lütfen iade sebebi belirtiniz."}, status=400)

        order.refund_requested = True
        order.refund_reason = reason
        order.refund_status = 'pending'
        order.status = 'refund_requested'
        order.save()

        return Response({"message": "İade talebiniz alınmıştır, incelenip size bilgi verilecektir."}, status=200)
    


class AdminOrderRefundAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request, merchant_oid):
        order = get_object_or_404(DigitalProductOrder, merchant_oid=merchant_oid)
        
        if order.status != 'refund_requested':
            return Response({"message": "Sadece iade talebi oluşturulmuş siparişler için iade işlemi yapılabilir."}, status=400)
        
        if settings.DEBUG: 
            order.status = 'refunded'
            order.refund_status = 'approved'
            order.save()
            return Response({
                "message": "TEST MODU: İade talebi (PayTR atlanarak) başarıyla onaylandı. Tutar 1-7 iş günü içinde yansıyacaktır.",
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
            
            if res_data['status'] == 'success':
                order.status = 'refunded'
                order.refund_status = 'approved'
                order.save()
                
                
                return Response({
                    "message": "İade talebiniz onaylanmıştır. Tutarın hesabınıza yansıma süresi bankanıza bağlı olarak 1-7 iş günü sürebilir.",
                    "status": "success"
                }, status=200)
            else:
                return Response({"message": f"PayTR Hatası: {res_data.get('err_msg')}"}, status=400)

        except Exception as e:
            return Response({"message": f"Sistem hatası: {str(e)}"}, status=500)
        


class ProductsOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]
    pagination_class = Pagination10

    def get(self, request):
        status_filter = request.query_params.get('status', None)
        ordering = request.query_params.get('ordering', '-created_at')
        search_query = request.query_params.get('search', None)
        
        orders = DigitalProductOrder.objects.all().select_related('user', 'product').order_by('-created_at')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
            
        if ordering in ['created_at', '-created_at']:
            orders = orders.order_by(ordering)
        else:
            orders = orders.order_by('-created_at')
            
            
        if search_query:
            q = search_query.strip()
            orders = orders.annotate(
                full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(full_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(merchant_oid__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q)
            )
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(orders, request)
        
        if page is not None:
            serializer = ProductsOrderListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductsOrderListSerializer(orders, many=True)
        return Response(serializer.data)
    


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def get(self, request):
        now = timezone.now()
        current_date = now.date()
        current_time = now.time()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        student_count = Users.objects.filter(user_type='student', is_deleted=False).count()
        
        active_course_filter = Q(is_deleted=False) & (
            Q(end_date__gt=current_date) | 
            Q(end_date=current_date, end_time__gt=current_time) |
            Q(end_date__isnull=True)
        )
        course_count = Course.objects.filter(active_course_filter).count()
        digital_product_count = DigitalProduct.objects.filter(is_deleted=False, stock__gt=0).count()

        course_earnings = CourseOrder.objects.filter(
            status='completed',
            course__is_deleted=False,
            created_at__gte=start_of_month
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        digital_earnings = DigitalProductOrder.objects.filter(
            status='completed',
            product__is_deleted=False,
            created_at__gte=start_of_month
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        monthly_earnings = course_earnings + digital_earnings

        latest_courses_qs = Course.objects.filter(active_course_filter).order_by('-created_at')[:5]
        latest_courses = [{"id": c.id, "name": c.name} for c in latest_courses_qs]

        course_orders_qs = CourseOrder.objects.filter(
            status='completed', course__is_deleted=False
        ).select_related('user', 'course').order_by('-created_at')[:5]

        latest_order_students = []
        for o in course_orders_qs:
            adj_date = o.created_at + timedelta(hours=3)
            latest_order_students.append({
                "id": o.id,
                "first_name": o.user.first_name if o.user else None,
                "last_name": o.user.last_name if o.user else None,
                "course_name": o.course.name,
                "registration_date": adj_date.strftime("%Y-%m-%d %H:%M:%S")
            })

        digital_orders_qs = DigitalProductOrder.objects.filter(
            status='completed', product__is_deleted=False
        ).select_related('user', 'product').order_by('-created_at')[:5]

        latest_digital_orders = []
        for d_o in digital_orders_qs:
            adj_date = d_o.created_at + timedelta(hours=3)
            latest_digital_orders.append({
                "id": d_o.id,
                "first_name": d_o.user.first_name if d_o.user else None,
                "last_name": d_o.user.last_name if d_o.user else None,
                "product_name": d_o.product.name,
                "order_date": adj_date.strftime("%Y-%m-%d %H:%M:%S")
            })

        monthly_course_dict = {}
        monthly_digital_dict = {}
        for i in range(5, -1, -1):
            target_date = now - timedelta(days=i*30)
            month_name = target_date.strftime('%B').lower()
            monthly_course_dict[month_name] = 0
            monthly_digital_dict[month_name] = 0

        six_months_ago = now - timedelta(days=180)

        course_sales_qs = CourseOrder.objects.filter(
            status='completed',
            course__is_deleted=False,
            created_at__gte=six_months_ago
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id'))

        for entry in course_sales_qs:
            m_name = entry['month'].strftime('%B').lower()
            if m_name in monthly_course_dict:
                monthly_course_dict[m_name] = entry['count']

        digital_sales_qs = DigitalProductOrder.objects.filter(
            status='completed',
            product__is_deleted=False,
            created_at__gte=six_months_ago
        ).annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id'))

        for entry in digital_sales_qs:
            m_name = entry['month'].strftime('%B').lower()
            if m_name in monthly_digital_dict:
                monthly_digital_dict[m_name] = entry['count']

        monthly_course_sales = [{k: v} for k, v in monthly_course_dict.items()]
        monthly_digital_sales = [{k: v} for k, v in monthly_digital_dict.items()]

        return Response({
            "student_count": student_count,
            "course_count": course_count,
            "digital_product_count": digital_product_count,
            "monthly_earnings": monthly_earnings,
            "latest_courses": latest_courses,
            "latest_order_students": latest_order_students,
            "latest_digital_orders": latest_digital_orders,
            "monthly_course_sales": monthly_course_sales,
            "monthly_digital_sales": monthly_digital_sales
        })
        




class UnifiedOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            # Env var kontrolü
            if not all([settings.PAYTR_MERCHANT_ID, settings.PAYTR_MERCHANT_KEY, settings.PAYTR_MERCHANT_SALT]):
                return Response({
                    "error": "PAYTR ayarları eksik",
                    "detail": f"ID:{bool(settings.PAYTR_MERCHANT_ID)} KEY:{bool(settings.PAYTR_MERCHANT_KEY)} SALT:{bool(settings.PAYTR_MERCHANT_SALT)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            digital_products_data = request.data.get('digital_products', [])
            courses_data = request.data.get('courses', [])
            user = request.user

            initial_status = 'completed' if settings.DEBUG else 'pending'

            total_payment_amount = 0
            basket_items = []
            master_merchant_oid = f"ORD{user.id}X{int(time.time())}"

            for item in courses_data:
                course = get_object_or_404(Course, id=item['id'])
                amount = item['amount']
                price = course.discounted_price if course.discounted_price else course.price
                CourseOrder.objects.create(
                    user=user,
                    course=course,
                    total_amount=price * amount,
                    status=initial_status,
                    merchant_oid=master_merchant_oid
                )
                total_payment_amount += (price * amount)
                basket_items.append([course.name, str(price), str(amount)])

            for item in digital_products_data:
                product = get_object_or_404(DigitalProduct, id=item['id'])
                amount = item['amount']
                price = product.discounted_price if product.discounted_price else product.price
                DigitalProductOrder.objects.create(
                    user=user,
                    product=product,
                    total_amount=price * amount,
                    status=initial_status,
                    merchant_oid=master_merchant_oid
                )
                total_payment_amount += (price * amount)
                basket_items.append([product.name, str(price), str(amount)])

            merchant_id = str(settings.PAYTR_MERCHANT_ID)
            merchant_key = settings.PAYTR_MERCHANT_KEY.encode()
            merchant_salt = str(settings.PAYTR_MERCHANT_SALT)
            payment_amount_total = int(total_payment_amount * 100)
            user_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
            if ',' in user_ip:
                user_ip = user_ip.split(',')[0].strip()
            user_basket = base64.b64encode(json.dumps(basket_items).encode()).decode()
            test_mode = "1" if settings.DEBUG else "0"

            hash_str = (
                merchant_id + user_ip + master_merchant_oid + user.email +
                str(payment_amount_total) + user_basket + "0" + "0" + "TRY" + test_mode + merchant_salt
            )
            paytr_token = base64.b64encode(
                hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()
            ).decode()

            user_phone = user.phone if user.phone and str(user.phone).strip() else "0000000000"
            addr = getattr(user, 'address_data', {}) or {}

            if addr:
                formatted_address = f"{addr.get('address_title', 'Adres')}: {addr.get('neighborhood', '')} Mah. {addr.get('full_address', '')} {addr.get('district', '')}/{addr.get('city', '')}"
            else:
                formatted_address = "Adres Bilgisi Bulunamadi"

            payload = {
                'merchant_id': merchant_id,
                'user_ip': user_ip,
                'merchant_oid': master_merchant_oid,
                'email': user.email,
                'payment_amount': payment_amount_total,
                'paytr_token': paytr_token,
                'user_basket': user_basket,
                'user_name': f"{user.first_name} {user.last_name}",
                'user_address': formatted_address,
                'user_phone': str(user_phone),
                'merchant_ok_url': f"{settings.FRONTEND_URL}/payment-success",
                'merchant_fail_url': f"{settings.FRONTEND_URL}/payment-failed",
                'currency': 'TRY',
                'test_mode': int(test_mode),
                'debug_on': 1 if settings.DEBUG else 0,
                'timeout_limit': 30,
                'lang': 'tr',
                'no_installment': 0,
                'max_installment': 0,
            }

            response = requests.post(settings.PAYTR_BASE_URL, data=payload, timeout=10)

            if response.status_code != 200:
                return Response({
                    "error": f"PayTR Sunucu Hatası (Kod: {response.status_code})",
                    "detail": response.text
                }, status=status.HTTP_400_BAD_REQUEST)

            res_data = response.json()

            if res_data.get('status') == 'success':
                return Response({'token': res_data.get('token')}, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "PayTR Token Alınamadı",
                    "detail": res_data.get('reason', 'Bilinmeyen hata')
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            import traceback
            return Response({
                "error": "Sipariş oluşturma hatası",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def paytr_callback(request):
    post_data = request.POST 
    
    merchant_oid = post_data.get('merchant_oid')
    status = post_data.get('status')
    total_amount = post_data.get('total_amount')
    hash_from_paytr = post_data.get('hash')
    
    hash_str = merchant_oid + settings.PAYTR_MERCHANT_SALT + status + total_amount
    
    hash_hmac = hmac.new(
        settings.PAYTR_MERCHANT_KEY.encode(), 
        hash_str.encode(), 
        hashlib.sha256
    ).digest()
    
    expected_hash = base64.b64encode(hash_hmac).decode()
    
    if hash_from_paytr != expected_hash:
        return HttpResponse("PAYTR hash mismatch", status=400)

    if status == 'success':
        CourseOrder.objects.filter(merchant_oid=merchant_oid).update(status='completed')
        DigitalProductOrder.objects.filter(merchant_oid=merchant_oid).update(status='completed')
        
    else:
        CourseOrder.objects.filter(merchant_oid=merchant_oid).update(status='failed')
        DigitalProductOrder.objects.filter(merchant_oid=merchant_oid).update(status='failed')

    return HttpResponse("OK")



class SendProductMailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserType]

    def post(self, request):
        order_id = request.data.get('order_id')
        product_link = request.data.get('product_link')

        if not order_id or not product_link:
            return Response(
                {"error": "order_id and product_link are required fields."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        order_instance = get_object_or_404(DigitalProductOrder, id=order_id)

        if order_instance.status != 'completed':
            return Response(
                {"error": f"Mail cannot be sent. Order status is '{order_instance.status}'. Only completed orders are eligible."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = order_instance.user
        if not user or not user.email:
            return Response(
                {"error": "The user associated with this order has no email address."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            subject = f"Ürününüz Hazır: {order_instance.product.name}"
            
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            html_content = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; padding: 25px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Satın Alımınız İçin Teşekkürler!</h2>
                <p>Merhaba <strong>{full_name}</strong>,</p>
                <p>Satın aldığınız <strong>{order_instance.product.name}</strong> ürününe aşağıdaki bağlantıdan erişebilirsiniz:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{product_link}" style="background-color: #27ae60; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                        Ürünü İndir / Eriş
                    </a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 14px;">
                    Linke alternatif olarak buradan da ulaşabilirsiniz:<br>
                    <a href="{product_link}">{product_link}</a>
                </p>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #bdc3c7;">
                    Merchant OID: {order_instance.merchant_oid}<br>
                    Sipariş Tarihi: {order_instance.created_at.strftime('%d.%m.%Y %H:%M')}
                </p>
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
            
            order_instance.is_link_send = True
            order_instance.save()

            return Response(
                {"message": f"Product link successfully sent to {user.email}"}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Mail error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )