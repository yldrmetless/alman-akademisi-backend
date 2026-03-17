from django.urls import path
from courses.views import (
    AdminCourseOrderRefundAPIView,
    CourseAdminOrderUpdateAPIView,
    CourseCategoryListAPIView,
    CourseDetailAPIView,
    CourseListAPIView,
    CourseOrderCreateAPIView,
    CourseOrdersListAPIView,
    CreateCourseAPIView,
    CreateCourseCategoryAPIView,
    CreateExamAPIView,
    CustomerCourseRefundRequestAPIView,
    EditCourseAPIView,
    EditCourseCategoryAPIView,
    EditExamAPIView,
    ExamQuestionsListAPIView,
    LevelExamListAPIView,
    SendCourseLinkAPIView
)

urlpatterns = [
    path('create-exam/', CreateExamAPIView.as_view(), name='create_exam'),
    
    path('exam-list/', LevelExamListAPIView.as_view(), name='level_exam_list'),
    
    path('exam-questions/<int:id>/', ExamQuestionsListAPIView.as_view(), name='exam_questions_list'),
    
    path('edit-exam/<int:id>/', EditExamAPIView.as_view(), name='edit_exam'),
    
    path('create-course-category/', CreateCourseCategoryAPIView.as_view(), name='create-category'),
    
    path('course-category-list/', CourseCategoryListAPIView.as_view(), name='category-list'),
    
    path('edit-course-category/<int:id>/', EditCourseCategoryAPIView.as_view(), name='edit-course-category'),
    
    path('create-course/', CreateCourseAPIView.as_view(), name='create_course'),
    
    path('course-list/', CourseListAPIView.as_view(), name='course_list'),
    
    path('course-detail/<int:id>/', CourseDetailAPIView.as_view(), name='course_detail'),
    
    path('edit-course/<int:id>/', EditCourseAPIView.as_view(), name='edit-course'),
    
    path('create-course-order/', CourseOrderCreateAPIView.as_view(), name='create-course-order'),
    
    path('admin-update-course-order/<str:merchant_oid>/', CourseAdminOrderUpdateAPIView.as_view(), name='admin-update-course-order'),
    
    path('refund-request/<str:merchant_oid>/', CustomerCourseRefundRequestAPIView.as_view(), name='customer_course_refund_request'),
    
    path('admin-refund/<str:merchant_oid>/', AdminCourseOrderRefundAPIView.as_view(), name='admin_course_order_refund'),
    
    path('admin-course-orders/', CourseOrdersListAPIView.as_view(), name='admin_course_orders'),
    
    path('send-course-link/', SendCourseLinkAPIView.as_view(), name='send_course_link'),
]