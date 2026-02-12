from rest_framework import serializers
from .models import User, Business, Product
from listing.serializers import UserProfileSerializer

class ProductPublicSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    business_slug = serializers.CharField(source="business.slug", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "price",
            "currency",
            "image",
            "slug",
            "location",
            "business_name",
            "business_slug",
        ]

class ProductOwnerSerializer(serializers.ModelSerializer):
    business_name = serializers.ReadOnlyField(source="business.name")

    class Meta:
        model = Product
        fields = [
            "id",
            "business",
            "business_name",
            "name",
            "description",
            "price",
            "currency",
            "image",
            "exchange_for",
            "slug",
            "location",
            "is_available",
            "created_at",
        ]
        read_only_fields = ["business", "slug", "created_at"]

class ProductAdminSerializer(serializers.ModelSerializer):
    business_name = serializers.ReadOnlyField(source="business.name")
    owner_phone = serializers.ReadOnlyField(source="business.owner.phone_whatsapp")

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["slug", "created_at"]


class BusinessPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "business_type",
            "description",
            "location",
            "is_verified",
        ]

class BusinessOwnerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Business
        fields = [
            "name",
            "slug",
            "description",
            "logo",
            "business_type",
            "location",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]

class BusinessAdminSerializer(serializers.ModelSerializer):
    owner_phone = serializers.ReadOnlyField(source="owner.phone_whatsapp")

    class Meta:
        model = Business
        fields = "__all__"
        read_only_fields = ["slug", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    business = BusinessOwnerSerializer(read_only=True)
    user_profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "phone_whatsapp",
            "is_active",
            "date_joined",
            "user_profile",
            "business",
        ]
        read_only_fields = ["date_joined"]