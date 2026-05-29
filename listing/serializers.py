from rest_framework import serializers
from .models import UserProfile, Listing, ListingImage, VerificationRequest
from base_api.models import Business
from base_api.serializers import BusinessPublicSerializer, BusinessSerializer


# =======================
# USER PROFILE
# =======================
class UserProfileSerializer(serializers.ModelSerializer):
    business_slug = serializers.CharField(source='user.business.slug', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'account_type', 'is_verified', 'business_slug']
        read_only_fields = fields


# =======================
# LISTING IMAGES
# =======================
class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'is_main']


# =======================
# PUBLIC LISTING (HOME)
# =======================
class ListingPublicSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_slug = serializers.CharField(source='business.slug', read_only=True)
    vendor_phone = serializers.CharField(source='business.owner.phone_whatsapp', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'price', 'currency',
            'category', 'commune', 'quartier',
            'slug', 'business_name', 'business_slug', 'vendor_phone', 'main_image',
            'created_at', 'is_for_barter', 'is_new'
        ]

    def get_main_image(self, obj):
        # Optimisation N+1 Query : Utilise prefetch_related loaded data
        images = obj.images.all()
        for img in images:
            if img.is_main:
                return img.image.url
        return images[0].image.url if images else None
    
    is_new = serializers.SerializerMethodField()
    def get_is_new(self, obj):
        from django.utils import timezone
        import datetime
        return obj.created_at > timezone.now() - datetime.timedelta(days=2)


# =======================
# DETAIL PAGE
# =======================
class ListingDetailSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_slug = serializers.CharField(source='business.slug', read_only=True)
    business_logo = serializers.SerializerMethodField()
    vendor_phone = serializers.CharField(source='business.owner.phone_whatsapp', read_only=True)
    is_verified = serializers.BooleanField(source='business.owner.is_phone_verified', read_only=True) 
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'currency',
            'category', 'specs', 'is_for_barter', 'barter_target',
            'commune', 'quartier', 'created_at', 'updated_at',
            'slug', 'images', 'business_name', 'business_slug', 
            'business_logo', 'vendor_phone', 'is_verified'
        ]
    
    def get_business_logo(self, obj):
        return obj.business.logo.url if obj.business.logo else None


# =======================
# OWNER DASHBOARD
# =======================
class ListingOwnerSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = "__all__"


# =======================
# CREATE / UPDATE
# =======================
class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'currency', 'category',
            'specs', 'is_for_barter', 'barter_target', 'description',
            'commune', 'quartier', 'is_active', 'images'
        ]

    def validate(self, data):
        if data.get("is_for_barter") and not data.get("barter_target"):
            raise serializers.ValidationError(
                "barter_target est requis si is_for_barter=True"
            )
        return data

    def create(self, validated_data):
        # Le business est injecté via perform_create dans le controlleur
        images = validated_data.pop('images', [])
        listing = Listing.objects.create(**validated_data)

        for idx, image in enumerate(images):
            ListingImage.objects.create(
                listing=listing,
                image=image,
                is_main=(idx == 0)
            )

        return listing

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if images is not None:
            instance.images.all().delete()
            for idx, image in enumerate(images):
                ListingImage.objects.create(
                    listing=instance,
                    image=image,
                    is_main=(idx == 0)
                )

        return instance


# =======================
# VERIFICATION REQUEST
# =======================
class VerificationRequestSerializer(serializers.ModelSerializer):
    doc_front = serializers.ImageField(source='document_front')

    class Meta:
        model = VerificationRequest
        fields = ['id', 'doc_front', 'status', 'submitted_at']
        read_only_fields = ['status', 'submitted_at']
