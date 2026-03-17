from rest_framework import serializers
from .models import BlogPost, Category, CertificateImage, CourseGalleryImage, Tag, WebPageHeroImages, WebPageModel
from django.utils import timezone
from django.utils.text import slugify

class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']
        
        
class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
        
class CategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'is_deleted']

    def update(self, instance, validated_data):
        new_name = validated_data.get('name')
        is_deleted_signal = validated_data.get('is_deleted')

        if new_name and instance.name != new_name:
            instance.name = new_name
            instance.slug = slugify(new_name)

        if is_deleted_signal is True:
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.category_posts.clear() 
        
        elif is_deleted_signal is False:
            instance.is_deleted = False
            instance.deleted_at = None

        instance.save()
        return instance


class BlogPostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'categories', 'tags', 'image_url', 'image_public_id']

    def validate_title(self, value):
        generated_slug = slugify(value)
        if BlogPost.objects.filter(slug=generated_slug).exists():
            raise serializers.ValidationError("Bu başlığa benzer bir blog yazısı zaten mevcut. Lütfen başlığı değiştirin.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        
        categories_data = validated_data.pop('categories', [])
        tags_names = validated_data.pop('tags', [])
        
        blog_post = BlogPost.objects.create(author=user, **validated_data)
        
        tag_objects = []
        for name in tags_names:
            tag, created = Tag.objects.get_or_create(
                name=name.strip().lower(),
                defaults={'is_deleted': False}
            )
            
            if tag.is_deleted:
                tag.is_deleted = False
                tag.save()
                
            tag_objects.append(tag)
        
        blog_post.categories.set(categories_data)
        blog_post.tags.set(tag_objects)
        
        return blog_post
    
class BlogPostListSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
    author_user_type = serializers.ReadOnlyField(source='author.user_type')
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'author_username', 'author_first_name', 'author_last_name', 'author_user_type', 'content', 'title', 'slug', 
            'image_url', 'view_count', 'created_at',
            'is_deleted', 'categories', 'tags'
        ]
        
    def get_categories(self, obj):
        active_categories = obj.categories.filter(is_deleted=False)
        return [{"name": category.name} for category in active_categories]

    def get_tags(self, obj):
        active_tags = obj.tags.filter(is_deleted=False)
        return [{"name": tag.name} for tag in active_tags]
        
class BlogEditSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )

    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'categories', 'tags', 'image_url', 'image_public_id', 'is_deleted']

    def update(self, instance, validated_data):
        categories_data = validated_data.pop('categories', None)
        tags_names = validated_data.pop('tags', None)

        if validated_data.get('is_deleted') is True:
            instance.is_deleted = True
            instance.deleted_at = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if 'title' in validated_data:
            instance.slug = slugify(validated_data['title'])

        instance.save()

        if categories_data is not None:
            instance.categories.set(categories_data)

        if tags_names is not None:
            tag_objects = []
            for name in tags_names:
                tag_name = name.strip().lower()
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'is_deleted': False}
                )
                
                if tag.is_deleted:
                    tag.is_deleted = False
                    tag.save()
                
                tag_objects.append(tag)
            
            instance.tags.set(tag_objects)

        return instance
    


class WebPageHeroImagesCreateSerializer(serializers.Serializer):
    image_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    image_public_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    order = serializers.IntegerField(required=False, default=0)


class WebPageContentCreateSerializer(serializers.ModelSerializer):
    hero_images = WebPageHeroImagesCreateSerializer(many=True, required=False)

    class Meta:
        model = WebPageModel
        fields = [
            "logo_url",
            "logo_public_id",
            "hero_title_first",
            "hero_title_second",
            "hero_title_third",
            "hero_images",
        ]
        extra_kwargs = {
            "logo_url": {"required": False, "allow_null": True, "allow_blank": True},
            "logo_public_id": {"required": False, "allow_null": True, "allow_blank": True},
            "hero_title_first": {"required": False, "allow_null": True, "allow_blank": True},
            "hero_title_second": {"required": False, "allow_null": True, "allow_blank": True},
            "hero_title_third": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def create(self, validated_data):
        hero_images_data = validated_data.pop("hero_images", [])

        logo_url = validated_data.get("logo_url")
        hero_title_first = validated_data.get("hero_title_first")
        hero_title_second = validated_data.get("hero_title_second")
        hero_title_third = validated_data.get("hero_title_third")

        content_type = None

        if hero_images_data:
            content_type = "hero_images"
        elif hero_title_first or hero_title_second or hero_title_third:
            content_type = "hero_title"
        elif logo_url:
            content_type = "logo"

        validated_data["type"] = content_type

        webpage = WebPageModel.objects.filter(
            is_deleted=False,
            type=content_type
        ).first()

        if webpage:
            for attr, value in validated_data.items():
                setattr(webpage, attr, value)
            webpage.save()

            if hero_images_data:
                WebPageHeroImages.objects.filter(
                    webpage=webpage,
                    is_deleted=False
                ).update(is_deleted=True)

                hero_image_objects = []
                for item in hero_images_data:
                    image_url = item.get("image_url")
                    image_public_id = item.get("image_public_id")

                    if image_url or image_public_id:
                        hero_image_objects.append(
                            WebPageHeroImages(
                                webpage=webpage,
                                image_url=image_url or "",
                                image_public_id=image_public_id or "",
                                order=item.get("order", 0)
                            )
                        )

                if hero_image_objects:
                    WebPageHeroImages.objects.bulk_create(hero_image_objects)

            return webpage

        webpage = WebPageModel.objects.create(**validated_data)

        if hero_images_data:
            hero_image_objects = []
            for item in hero_images_data:
                image_url = item.get("image_url")
                image_public_id = item.get("image_public_id")

                if image_url or image_public_id:
                    hero_image_objects.append(
                        WebPageHeroImages(
                            webpage=webpage,
                            image_url=image_url or "",
                            image_public_id=image_public_id or "",
                            order=item.get("order", 0)
                        )
                    )

            if hero_image_objects:
                WebPageHeroImages.objects.bulk_create(hero_image_objects)

        return webpage
    


class WebPageContentListSerializer(serializers.ModelSerializer):
    hero_images = WebPageHeroImagesCreateSerializer(many=True, read_only=True)

    class Meta:
        model = WebPageModel
        fields = [
            "id",
            "type",
            "logo_url",
            "logo_public_id",
            "hero_title_first",
            "hero_title_second",
            "hero_title_third",
            "hero_images",
            "created_at",
            "updated_at",
        ]
        

class CourseGalleryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseGalleryImage
        fields = [
            "image_url",
            "image_public_id"
        ]



class CourseGalleryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseGalleryImage
        fields = [
            "id",
            "image_url",
            "image_public_id",
            "created_at",
            "updated_at",
        ]
        
        


class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateImage
        fields = [
            "image_url",
            "image_public_id"
        ]



class CertificateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateImage
        fields = [
            "id",
            "image_url",
            "image_public_id",
            "created_at",
            "updated_at",
        ]