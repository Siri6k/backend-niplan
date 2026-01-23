from rest_framework import serializers
from .models import UserProfile, Listing, ListingImage, VerificationRequest
from base_api.models import Business
from base_api.serializers import BusinessSerializer

# filepath: c:\Users\VISION TAG\Documents\project\niplan\backend\listing\serializers.py


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'first_name', 'last_name', 'account_type', 'phone_number', 'is_verified']
        read_only_fields = ['user']


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'is_main']


class ListingSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'business', 'business_name', 'title', 'description', 'price',
            'currency', 'category', 'specs', 'is_for_barter', 'barter_target',
            'commune', 'quartier', 'is_active', 'is_promoted', 'created_at',
            'updated_at', 'images'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ListingDetailSerializer(ListingSerializer):
    """Extended serializer with full business details"""
    business = serializers.SerializerMethodField()

    def get_business(self, obj):
        return BusinessSerializer(obj.business).data


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'currency', 'category', 'specs',
            'is_for_barter', 'barter_target', 'commune', 'quartier', 'is_active', 'images'
        ]

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


class VerificationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = ['id', 'user', 'doc_front', 'status', 'submitted_at']
        read_only_fields = ['submitted_at', 'status']