from django.urls import path
from .views import (
    CreateInfoRequestAPIView,
    CreateSupportAPIView,
    ForgotPasswordAPIView,
    GoogleReviewListView,
    LoginAPIView,
    MyCourseOrderAPIView,
    MyDigitalProductsOrderAPIView,
    RegisterAPIView,
    EditProfileAPIView,
    MyProfileAPIView,
    ResetPasswordConfirmAPIView,
    StudentDashAPIView,
    StudentListAPIView,
    SupportListAPIView,
    SupportUpdateStatusAPIView,
    UserAddressDetailAPIView,
    UserAddressGetAPIView,
    UserAddressUpdateAPIView,
    UserSupportListAPIView,
    YouTubeLinkCreateAPIView,
    YouTubeLinkListAPIView,
    YouTubeLinkUpdateAPIView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='auth_register'),
    
    path('login/', LoginAPIView.as_view(), name='auth_login'),
    
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='auth_forgot_password'),
    
    path('reset-password/', ResetPasswordConfirmAPIView.as_view(), name='auth_reset_password'),
    
    path('edit-profile/', EditProfileAPIView.as_view(), name='edit_profile'),
    
    path('profile/', MyProfileAPIView.as_view(), name='user_profile'),
    
    path('reviews/', GoogleReviewListView.as_view(), name='google_reviews'),
    
    path('students/', StudentListAPIView.as_view(), name='student_list'),
    
    path('students-review-create/', YouTubeLinkCreateAPIView.as_view(), name='youtube_link_create'),
    
    path('students-review-list/', YouTubeLinkListAPIView.as_view(), name='youtube_link_list'),
    
    path('student-review-update/<int:id>/', YouTubeLinkUpdateAPIView.as_view(), name='youtube_link_update'),
    
    path('student-dashboard/', StudentDashAPIView.as_view(), name='student_dashboard'),
    
    path('my-course-order/', MyCourseOrderAPIView.as_view(), name='my_course_order'),
    
    path('my-digital-products-order/', MyDigitalProductsOrderAPIView.as_view(), name='my_digital_products_order'),
    
    path('address-create/', UserAddressUpdateAPIView.as_view(), name='address_create'),
    
    path('address-get/', UserAddressGetAPIView.as_view(), name='address_get'),
    
    path('address-detail/<int:id>/', UserAddressDetailAPIView.as_view(), name='address_detail'),
    
    path('support-create/', CreateSupportAPIView.as_view(), name='support_create'),
    
    path('info-request-create/', CreateInfoRequestAPIView.as_view(), name='info_request_create'),
    
    path('support-list/', SupportListAPIView.as_view(), name='support_list'),
    
    path('my-support-list/', UserSupportListAPIView.as_view(), name='my_support_list'),
    
    path('support-update/<int:id>/', SupportUpdateStatusAPIView.as_view(), name='support-update'),
]