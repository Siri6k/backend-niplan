from rest_framework import serializers
from .models import UserProfile, Listing, ListingImage, VerificationRequest
from base_api.models import Business
from base_api.serializers import BusinessSerializer


# =======================
# USER PROFILE
# =======================
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'account_type', 'is_verified']
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

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'price', 'currency',
            'category', 'commune', 'quartier',
            'slug', 'business_name', 'main_image'
        ]

    def get_main_image(self, obj):
        img = obj.images.filter(is_main=True).first()
        return img.image.url if img else None


# =======================
# DETAIL PAGE
# =======================
class ListingDetailSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'currency',
            'category', 'specs', 'is_for_barter', 'barter_target',
            'commune', 'quartier', 'created_at', 'updated_at',
            'slug', 'images', 'business'
        ]


# =======================
# OWNER DASHBOARD
# =======================
class ListingOwnerSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'price', 'currency',
            'category', 'is_active', 'is_promoted',
            'created_at', 'updated_at', 'slug', 'images'
        ]


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
            'specs', 'is_for_barter', 'barter_target',
            'commune', 'quartier', 'is_active', 'images'
        ]

    def validate(self, data):
        if data.get("is_for_barter") and not data.get("barter_target"):
            raise serializers.ValidationError(
                "barter_target est requis si is_for_barter=True"
            )
        return data

    def create(self, validated_data):
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
    class Meta:
        model = VerificationRequest
        fields = ['id', 'doc_front', 'status', 'submitted_at']
        read_only_fields = ['status', 'submitted_at']
