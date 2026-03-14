from django.utils import timezone
from rest_framework import serializers
from users.models import SupportModel, Users, GoogleReview, YouTubeLink
from django.contrib.auth import authenticate
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from courses.models import CourseOrder
from products.models import DigitalProductImage, DigitalProductOrder

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"message": "Şifreler eşleşmiyor."})
        
        if Users.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"message": "Bu e-posta adresi zaten kullanılıyor."})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        
        user = Users.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type='student'
        )
        return user
    
    

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('username_or_email')
        password = attrs.get('password')

        if identifier and password:
            try:
                user_obj = Users.objects.get(Q(username=identifier) | Q(email=identifier))
                user = authenticate(username=user_obj.username, password=password)
            except Users.DoesNotExist:
                user = None

            if not user:
                raise serializers.ValidationError("Kullanıcı adı veya şifre hatalı.")
            
            if not user.is_active:
                raise serializers.ValidationError("Kullanıcı hesabı devre dışı bırakılmış.")
        else:
            raise serializers.ValidationError("Kullanıcı adı ve şifre alanları zorunludur.")

        attrs['user'] = user
        return attrs
    
    
    

class EditProfileSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'email', 'username', 'current_password', 'new_password', 'is_deleted', 'avatar_url', 'avatar_url_id', 'phone']

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        is_deleted = attrs.get('is_deleted')
        current_password = attrs.get('current_password')

        if new_password or is_deleted:
            if not current_password:
                raise serializers.ValidationError({"message": "Hassas işlemler için mevcut şifreyi girmelisiniz."})
            
            if not check_password(current_password, self.instance.password):
                raise serializers.ValidationError({"message": "Mevcut şifre hatalı."})

        if new_password and current_password == new_password:
            raise serializers.ValidationError({"message": "Yeni şifre eski şifreyle aynı olamaz."})

        return attrs

    def update(self, instance, validated_data):
        new_password = validated_data.pop('new_password', None)
        current_password = validated_data.pop('current_password', None)
        is_deleted = validated_data.get('is_deleted', False)

        if is_deleted:
            instance.is_deleted = True
            instance.is_active = False
            instance.deleted_at = timezone.now()
            
            if not instance.email.startswith('dlt__'):
                instance.email = f"dlt__{instance.email}"
            
            if not instance.username.startswith('dlt__'):
                instance.username = f"dlt__{instance.username}"
            
            instance.save()
            return instance

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if new_password:
            instance.set_password(new_password)

        instance.save()
        return instance
    
    

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'username', 'email', 'user_type', 'date_joined', 'is_active', 
                  'avatar_url', 'avatar_url_id', 'phone', 'address_data', 'phone']



class GoogleReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleReview
        fields = [
            'id', 
            'author_name', 
            'author_avatar_url', 
            'rating', 
            'review_text', 
            'review_date'
        ]
        read_only_fields = fields
        


class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Users
        fields = [
            'id', 
            'username', 
            'full_name', 
            'email', 
            'phone', 
            'address_data', 
            'date_joined'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    

class YouTubeLinkSerializer(serializers.ModelSerializer):
    video_id = serializers.ReadOnlyField()

    class Meta:
        model = YouTubeLink
        fields = [
            'id', 
            'name', 
            'youtube_url', 
            'video_id', 
            'is_active', 
            'created_at', 
            'updated_at',
            'type'
        ]
        

class MyCourseOrderSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_image = serializers.URLField(source='course.image_url', read_only=True)
    course_level = serializers.CharField(source='course.level', read_only=True)
    course_type = serializers.CharField(source='course.type', read_only=True)

    class Meta:
        model = CourseOrder
        fields = [
            'id', 
            'merchant_oid', 
            'total_amount', 
            'status', 
            'course_name', 
            'course_image', 
            'course_level', 
            'course_type', 
            'created_at'
        ]
        
        


class MyDigitalProductsOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    purchase_price = serializers.DecimalField(source='total_amount', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = DigitalProductOrder
        fields = [
            'id', 
            'merchant_oid', 
            'status', 
            'product_name', 
            'purchase_price', 
            'product_image', 
            'created_at'
        ]

    def get_product_image(self, obj):
        image = DigitalProductImage.objects.filter(
            product=obj.product, 
            is_deleted=False
        ).order_by('order').first()
        return image.digital_product_image_url if image else None
    


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportModel
        fields = [
            'id', 'name', 'message', 'image_url', 'image_url_id', 
            'priority', 'created_at', 'email', 'phone', 
            'is_whatsapp', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'name': {'required': False, 'allow_null': True},
            'email': {'required': False, 'allow_null': True},
            'phone': {'required': False, 'allow_null': True},
            'first_name': {'required': False, 'allow_null': True},
            'last_name': {'required': False, 'allow_null': True},
        }

    def validate_priority(self, value):
        valid_priorities = ['low', 'normal', 'high']
        if value not in valid_priorities:
            raise serializers.ValidationError("Geçersiz öncelik seviyesi.")
        return value
    
    
class SupportListSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(default=None)
    last_name = serializers.ReadOnlyField(default=None)
    phone = serializers.ReadOnlyField(default=None)

    class Meta:
        model = SupportModel
        fields = [
            'id', 'name', 'email', 'first_name', 'last_name', 'phone',
            'message', 'image_url', 'image_url_id', 'priority', 'created_at', 'status'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        search_email = instance.email.strip().lower()
        
        user = Users.objects.filter(email__iexact=search_email, is_deleted=False).first()
        
        if user:
            representation['first_name'] = user.first_name
            representation['last_name'] = user.last_name
            representation['phone'] = user.phone
        else:
            print(f"DEBUG: Kullanıcı bulunamadı! Aranan Email: '{search_email}'")
            
        return representation
    


class SupportStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportModel
        fields = ['status']