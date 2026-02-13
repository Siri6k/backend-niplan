from rest_framework import serializers
from .models import OTPCode, User, Business, Product


class RequestOTPSerializer(serializers.Serializer):
    phone_whatsapp = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    phone_whatsapp = serializers.CharField()
    code = serializers.CharField()
class AdminUserSerializer(serializers.ModelSerializer):
    business = serializers.ReadOnlyField(source='business.name')
    business_type = serializers.ReadOnlyField(source='business.business_type')

    class Meta:
        model = User
        fields = ["id", "phone_whatsapp", "is_active", "is_staff", 
                  "is_superuser", "date_joined", "business", "business_type"]

class OTPLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPCode
        fields = ["id", "phone_number", "code", "updated_at"]

# Serializer pour les produits
class ProductSerializer(serializers.ModelSerializer):
    business_name = serializers.ReadOnlyField(source='business.name')
    vendor_phone = serializers.ReadOnlyField(source='business.owner.phone_whatsapp')

    class Meta:
        model = Product
        fields = [
            'id', 'business', 'business_name', 'name', 'description', 
            'price', 'currency', 'image', 'exchange_for', 'slug',
            'location', 'is_available', 'created_at', 'business', "updated_at", 
            'vendor_phone'
        ]
        read_only_fields = ['business'] # <--- AJOUTE CECI

# Serializer pour le Business (Profil de la boutique)
class BusinessSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True) # Affiche les produits de la boutique
    owner_phone = serializers.ReadOnlyField(source='owner.phone_whatsapp')

    class Meta:
        model = Business
        fields = [
            'id', 'owner_phone', 'name', 'slug', 'description', 
            'logo', 'business_type', 'products', 'created_at', 'location'
        ]

# Serializer pour l'Utilisateur
class UserSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone_whatsapp', 'business']