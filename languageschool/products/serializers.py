from rest_framework import serializers
from products.models import DigitalProduct, DigitalProductCategory, DigitalProductImage, DigitalProductOrder
from django.utils.text import slugify

class DigitalProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProductImage
        fields = ['digital_product_image_url', 'digital_product_public_id', 'order']

class DigitalProductCreateSerializer(serializers.ModelSerializer):
    images = DigitalProductImageSerializer(many=True, required=False)

    class Meta:
        model = DigitalProduct
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discounted_price', 
            'stock', 'is_active', 'product_type', 'external_link', 
            'download_limit', 'images'
        ]

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        
        product = DigitalProduct.objects.create(**validated_data)
        
        for image_data in images_data:
            DigitalProductImage.objects.create(product=product, **image_data)
            
        return product

class DigitalProductImageEditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = DigitalProductImage
        fields = ['id', 'digital_product_image_url', 'digital_product_public_id', 'order', 'is_deleted']

class DigitalProductEditSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(
        queryset=DigitalProductCategory.objects.filter(is_deleted=False),
        required=False,
        allow_null=True
    )

    class Meta:
        model = DigitalProduct
        fields = [
            'category', 'name', 'slug', 'description', 'price', 
            'discounted_price', 'stock', 'is_active', 'is_deleted', 
            'product_type', 'external_link', 'download_limit', 'images'
        ]

    def get_images(self, obj):
        active_images = obj.images.filter(is_deleted=False).order_by('order')
        return DigitalProductImageEditSerializer(active_images, many=True).data

    def update(self, instance, validated_data):
        if 'category' in validated_data:
            instance.category = validated_data.get('category')

        new_name = validated_data.get('name', instance.name)
        if new_name != instance.name:
            instance.name = new_name
            instance.slug = slugify(new_name)

        for attr, value in validated_data.items():
            if attr not in ['images', 'category', 'name']:
                setattr(instance, attr, value)
        
        if instance.is_deleted:
            instance.images.all().update(is_deleted=True)
        
        instance.save()

        images_data = self.initial_data.get('images')
        if images_data is not None:
            current_image_ids = []
            for image_item in images_data:
                img_id = image_item.get('id')
                
                if img_id:
                    try:
                        img_obj = DigitalProductImage.objects.get(id=img_id, product=instance)
                        for attr, value in image_item.items():
                            if attr != 'id':
                                setattr(img_obj, attr, value)
                        img_obj.save()
                        current_image_ids.append(img_obj.id)
                    except DigitalProductImage.DoesNotExist:
                        continue
                else:
                    new_image = DigitalProductImage.objects.create(product=instance, **image_item)
                    current_image_ids.append(new_image.id)

            if not instance.is_deleted:
                instance.images.exclude(id__in=current_image_ids).update(is_deleted=True)

        return instance
    
    

class DigitalProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = DigitalProduct
        fields = [
            'id', 'name', 'slug', 'description', 
            'price', 'discounted_price', 'stock', 'main_image'
        ]

    def get_main_image(self, obj):
        first_image = obj.images.filter(is_deleted=False).order_by('order').first()
        if first_image:
            return {
                "id": first_image.id,
                "url": first_image.digital_product_image_url,
                "public_id": first_image.digital_product_public_id
            }
        return None
    


class DigitalProductImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProductImage
        fields = ['id', 'digital_product_image_url', 'digital_product_public_id', 'order']

class DigitalProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = DigitalProduct
        fields = [
            'id', 'name', 'slug', 'description', 
            'price', 'discounted_price', 'stock', 'is_active', 
            'images', 'product_type', 'external_link', 'download_limit'
        ]

    def get_images(self, obj):
        active_images = obj.images.filter(is_deleted=False).order_by('order')
        return DigitalProductImageDetailSerializer(active_images, many=True).data
    
    
class DigitalProductImageDetailSerializerCustomer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProductImage
        fields = ['id', 'digital_product_image_url', 'digital_product_public_id', 'order']

class DigitalProductDetailSerializerCustomer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = DigitalProduct
        fields = [
            'id', 'name', 'slug', 'description', 
            'price', 'discounted_price', 'stock', 'is_active', 
            'images', 'product_type'
        ]

    def get_images(self, obj):
        active_images = obj.images.filter(is_deleted=False).order_by('order')
        return DigitalProductImageDetailSerializer(active_images, many=True).data


class DigitalProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProductCategory
        fields = [
            'id', 'name', 'slug', 'description', 
            'is_active', 'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        


class DigitalProductCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProductCategory
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DigitalProductOrder
        fields = ['product_id', 'merchant_oid', 'total_amount', 'status']
        read_only_fields = ['merchant_oid', 'total_amount', 'status']

    def validate_product_id(self, value):
        if not DigitalProduct.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Geçerli bir ürün bulunamadı.")
        return value
    


class OrderAdminListSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DigitalProductOrder
        fields = [
            'merchant_oid', 'user_full_name', 'user_email', 
            'product_name', 'total_amount', 'status', 'created_at'
        ]
        

class AdminOrderNotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = DigitalProductOrder
        fields = [
            'merchant_oid', 
            'user_name', 
            'user_email', 
            'product_name', 
            'total_amount', 
            'status', 
            'created_at'
        ]
        
        


class ProductsOrderListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    order_date = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = DigitalProductOrder
        fields = [
            'id', 
            'merchant_oid',
            'order_date',
            'first_name', 
            'last_name', 
            'email', 
            'product_name',
            'total_amount',
            'status',
            'refund_requested',
            'is_link_send'
        ]