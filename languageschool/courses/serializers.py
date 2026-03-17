from rest_framework import serializers
from django.utils import timezone
from courses.models import (
    Course,
    COURSE_TYPE_CHOICES,
    LEVEL_CHOICES,
    CourseCategory,
    CourseOrder,
    CourseTag,
    LevelExam,
    ExamQuestion
)
from django.utils.text import slugify

class ExamQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = ['question_text', 'question_type', 'audio_url', 'audio_public_id', 'options', 'order']

class LevelExamCreateSerializer(serializers.ModelSerializer):
    questions = ExamQuestionSerializer(many=True, write_only=True)

    class Meta:
        model = LevelExam
        fields = ['id', 'name', 'level', 'slug', 'time_limit', 'questions', 'description']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        exam = LevelExam.objects.create(**validated_data)
        
        for question in questions_data:
            ExamQuestion.objects.create(level=exam, **question)
            
        return exam
    
    

class LevelExamListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = LevelExam
        fields = ['id', 'name', 'level', 'slug', 'time_limit', 'question_count', 'created_at']

    def get_question_count(self, obj):
        return obj.questions.filter(is_deleted=False).count()
    


class ExamQuestionListSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = ExamQuestion
        fields = ['id', 'question_text', 'question_type', 'audio_url', 'options', 'order']

    def get_options(self, obj):
        clean_options = []
        if obj.options and isinstance(obj.options, list):
            for opt in obj.options:
                clean_options.append({
                    "id": opt.get("id"),
                    "text": opt.get("text"),
                    "is_correct": opt.get("is_correct", False)
                })
        return clean_options
    


class ExamQuestionEditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ExamQuestion
        fields = [
            'id', 'question_text', 'question_type', 
            'audio_url', 'audio_public_id', 'options', 
            'order', 'is_deleted'
        ]

class LevelExamEditSerializer(serializers.ModelSerializer):
    questions = ExamQuestionEditSerializer(many=True)

    class Meta:
        model = LevelExam
        fields = ['name', 'level', 'slug',  'time_limit', 'is_deleted', 'questions']

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            instance.name = new_name
            instance.slug = slugify(new_name)
            
        instance.level = validated_data.get('level', instance.level)
        instance.time_limit = validated_data.get('time_limit', instance.time_limit)
        instance.is_deleted = validated_data.get('is_deleted', instance.is_deleted)
        
        if instance.is_deleted:
            instance.deleted_at = timezone.now()
        
        instance.save()

        for question_data in questions_data:
            question_id = question_data.get('id')
            
            if question_id:
                try:
                    question_item = ExamQuestion.objects.get(id=question_id, level=instance)
                    for attr, value in question_data.items():
                        setattr(question_item, attr, value)
                    
                    if question_item.is_deleted and not question_item.deleted_at:
                        question_item.deleted_at = timezone.now()
                    
                    question_item.save()
                except ExamQuestion.DoesNotExist:
                    ExamQuestion.objects.create(level=instance, **question_data)
            else:
                ExamQuestion.objects.create(level=instance, **question_data)

        return instance
    



class CourseCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'is_active']
        read_only_fields = ['slug']
        

class CourseCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'is_active', 'created_at']


class CourseCategoryEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['name', 'is_active']


class CourseCreateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=COURSE_TYPE_CHOICES)
    level = serializers.ChoiceField(choices=LEVEL_CHOICES)
    
    category = serializers.PrimaryKeyRelatedField(
        queryset=CourseCategory.objects.filter(is_deleted=False, is_active=True),
        required=False,
        allow_null=True
    )

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'description', 'image_url', 
            'image_public_id', 'price', 'discounted_price', 
            'type', 'level', 'category', 'tags',
            'quota', 'start_date', 'end_date', 'start_time', 'end_time',
            'education_link', 'first_day', 'last_day', 'is_private_lesson'
        ]

    def validate(self, attrs):
        price = attrs.get('price')
        discounted_price = attrs.get('discounted_price')
        
        if discounted_price and price and discounted_price > price:
            raise serializers.ValidationError(
                {"discounted_price": "İndirimli fiyat normal fiyattan yüksek olamaz."}
            )

        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "Bitiş tarihi başlangıç tarihinden önce olamaz."}
            )

        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_date == end_date and start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    {"end_time": "Aynı gün içindeki kursta bitiş saati başlangıçtan sonra olmalıdır."}
                )
                
        first_day = attrs.get('first_day')
        last_day = attrs.get('last_day')

        if first_day and last_day:
            days_order = {
                'Pazartesi': 0, 'Salı': 1, 'Çarşamba': 2, 'Perşembe': 3,
                'Cuma': 4, 'Cumartesi': 5, 'Pazar': 6
            }
            
            first_idx = days_order.get(first_day)
            last_idx = days_order.get(last_day)

            if first_idx is None or last_idx is None:
                raise serializers.ValidationError(
                    {"first_day": "Lütfen geçerli bir gün adı giriniz (Örn: Pazartesi)."}
                )

            if first_idx >= last_idx:
                raise serializers.ValidationError(
                    {"last_day": "Bitiş günü başlangıç gününden sonra olmalı ve başlangıç ile aynı olamaz."}
                )

        return attrs

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        
        course = Course.objects.create(**validated_data)
        
        for tag_name in tags_data:
            CourseTag.objects.create(course=course, name=tag_name)
            
        return course


class CourseListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    
    tags = serializers.SerializerMethodField()
    registered = serializers.SerializerMethodField()
    education_link = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 
            'name', 
            'description', 
            'image_url', 
            'image_public_id', 
            'price', 
            'discounted_price', 
            'type', 
            'level', 
            'created_at', 
            'category',
            'category_name',
            'tags',
            'quota',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'education_link',
            'registered',
            'first_day',
            'last_day',
            'is_private_lesson'
        ]

    def get_tags(self, obj):
        return obj.tags.values_list('name', flat=True)
    
    def get_registered(self, obj):
        return obj.orders.filter(status='completed').count()
    
    def get_education_link(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.user_type == 'admin':
            return obj.education_link
        return None
        
        
class CourseEditSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=CourseCategory.objects.filter(is_deleted=False),
        required=False, 
        allow_null=True
    )

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    class Meta:
        model = Course
        fields = [
            'name', 'description', 'image_url', 'image_public_id', 
            'price', 'discounted_price', 'type', 'level', 'category', 'is_active', 'tags',
            'quota', 'start_date', 'end_date', 'start_time', 'end_time', 'education_link',
            'is_private_lesson'
        ]

    def validate(self, attrs):
        price = attrs.get('price', self.instance.price)
        discounted_price = attrs.get('discounted_price', self.instance.discounted_price)
        start_date = attrs.get('start_date', self.instance.start_date)
        end_date = attrs.get('end_date', self.instance.end_date)
        start_time = attrs.get('start_time', self.instance.start_time)
        end_time = attrs.get('end_time', self.instance.end_time)
        first_day = attrs.get('first_day', self.instance.first_day)
        last_day = attrs.get('last_day', self.instance.last_day)

        if discounted_price and price and discounted_price > price:
            raise serializers.ValidationError(
                {"discounted_price": "İndirimli fiyat orijinal fiyattan yüksek olamaz."}
            )

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "Bitiş tarihi başlangıç tarihinden önce olamaz."}
            )

        if start_date and end_date and start_date == end_date:
            if start_time and end_time and start_time >= end_time:
                raise serializers.ValidationError(
                    {"end_time": "Aynı gün içindeki kursta bitiş saati başlangıçtan sonra olmalıdır."}
                )
        
        if first_day and last_day:
            days_order = {
                'Pazartesi': 0, 'Salı': 1, 'Çarşamba': 2, 'Perşembe': 3,
                'Cuma': 4, 'Cumartesi': 5, 'Pazar': 6
            }
            
            first_idx = days_order.get(first_day)
            last_idx = days_order.get(last_day)

            if first_idx is None or last_idx is None:
                raise serializers.ValidationError(
                    {"first_day": "Lütfen geçerli bir gün adı giriniz (Örn: Pazartesi)."}
                )

            if first_idx >= last_idx:
                raise serializers.ValidationError(
                    {"last_day": "Bitiş günü başlangıç gününden sonra olmalı ve başlangıç ile aynı olamaz."}
                )

        return attrs

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        
        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.all().delete()
            for tag_name in tags_data:
                CourseTag.objects.create(course=instance, name=tag_name)

        return instance
    


class CourseOrderCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CourseOrder
        fields = ['course_id', 'merchant_oid', 'total_amount', 'status']
        read_only_fields = ['merchant_oid', 'total_amount', 'status']

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value, is_deleted=False, is_active=True)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Geçerli bir kurs bulunamadı.")
            
        if course.quota <= 0:
            raise serializers.ValidationError("Bu kursun kontenjanı kapalıdır.")
            
        completed_orders_count = CourseOrder.objects.filter(course=course, status='completed').count()
        if completed_orders_count >= course.quota:
            raise serializers.ValidationError("Bu kursun kontenjanı dolmuştur.")

        now = timezone.now()
        current_date = now.date()
        current_time = now.time()

        if course.start_date:
            if course.start_date.date() < current_date:
                raise serializers.ValidationError("Bu kursun başlangıç tarihi geçtiği için satın alınamaz.")
            
            if course.start_date.date() == current_date and course.start_time:
                if current_time >= course.start_time:
                    raise serializers.ValidationError("Kursun başlama saati geldiği veya geçtiği için kayıt kapandı.")

        return value
    


class AdminCourseOrderNotificationSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CourseOrder
        fields = [
            'id', 
            'merchant_oid', 
            'user_full_name', 
            'email',
            'course_name', 
            'total_amount', 
            'status', 
            'updated_at'
        ]

    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Bilinmeyen Kullanıcı"
    
    


class CourseOrdersListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_type = serializers.CharField(source='course.type', read_only=True)
    
    order_date = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S", read_only=True)
    is_private_lesson = serializers.BooleanField(source='course.is_private_lesson', read_only=True)

    class Meta:
        model = CourseOrder
        fields = [
            'id', 
            'merchant_oid',
            'order_date',
            'first_name', 
            'last_name', 
            'email', 
            'course_name',
            'course_type',
            'total_amount',
            'status',
            'refund_requested',
            'refund_status',
            'is_private_lesson',
            'is_link_send'
        ]
    