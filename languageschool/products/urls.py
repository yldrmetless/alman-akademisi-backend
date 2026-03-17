from django.urls import path
from products.views import (
    AdminOrderListAPIView, 
    AdminOrderRefundAPIView, 
    AdminOrderUpdateAPIView, 
    CheckOrderStatusAPIView, 
    CreateDigitalProductCategory, 
    CreateOrder, 
    CustomerRefundRequestAPIView,
    DashboardAPIView,
    DigitalProdCategoryList, 
    DigitalProductCreateAPIView, 
    DigitalProductDetailAPIView,
    DigitalProductDetailAPIViewCustomer, 
    DigitalProductListAPIView, 
    DownloadDigitalProductAPIView, 
    EditDigitalProduct, 
    MyDigitalProductsAPIView,
    PayTRCallbackView,
    ProductsOrderListAPIView,
    SendProductMailAPIView,
    UnifiedOrderCreateAPIView,
    UpdateDigitalProductCategory
)

urlpatterns = [
    path('create-digital-product/', DigitalProductCreateAPIView.as_view(), name='create_digital_product'),
    
    path('edit-digital-product/<int:id>/', EditDigitalProduct.as_view(), name='edit_digital_product'),
    
    path('list-digital-products/', DigitalProductListAPIView.as_view(), name='list_digital_products'),
    
    path('digital-product-detail/<int:id>/', DigitalProductDetailAPIView.as_view(), name='digital_product_detail'),
    
    path('digital-product-detail-customer/<int:id>/', DigitalProductDetailAPIViewCustomer.as_view(), name='digital_product_detail_customer'),
    
    path('create-digital-product-category/', CreateDigitalProductCategory.as_view(), name='create_digital_product_category'),
    
    path('digital-product-categories/', DigitalProdCategoryList.as_view(), name='digital_product_categories'),
    
    path('digital-product-categories/<int:id>/', UpdateDigitalProductCategory.as_view(), name='digital_product_categories'),
    
    path('create-order/', CreateOrder.as_view(), name='create_order'),
    
    path('paytr-callback/', PayTRCallbackView.as_view(), name='paytr_callback'),
    
    path('check-order-status/<str:merchant_oid>/', CheckOrderStatusAPIView.as_view(), name='check_order_status'),
    
    path('admin-orders/', AdminOrderListAPIView.as_view(), name='admin_orders'),
    
    path('notifications/', AdminOrderListAPIView.as_view(), name='admin_notifications'),
    
    path('order-status-update/<str:merchant_oid>/', AdminOrderUpdateAPIView.as_view(), name='order_status_update'),
    
    path('my-products/', MyDigitalProductsAPIView.as_view(), name='my_digital_products'),
    
    path('download/<str:merchant_oid>/', DownloadDigitalProductAPIView.as_view(), name='download_digital_product'), 
    
    path('request-refund/<str:merchant_oid>/', CustomerRefundRequestAPIView.as_view(), name='customer_request_refund'),
    
    path('admin/refund-requests/<str:merchant_oid>/', AdminOrderRefundAPIView.as_view(), name='admin_refund_requests'), 
    
    path('admin/products-orders/', ProductsOrderListAPIView.as_view(), name='admin_products_orders'),
    
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard_statistics'),
    
    path('create-orders/', UnifiedOrderCreateAPIView.as_view(), name='create_unified_order'),
    
    path('send-product-mail/', SendProductMailAPIView.as_view(), name='send_product_mail'),
]