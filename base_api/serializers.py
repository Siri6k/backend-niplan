from rest_framework import serializers
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
from .models import OTPCode, User, Business, Product


# Custom field for phone validation
class PhoneField(serializers.CharField):
    def __init__(self, **kwargs):
        super().__init__(
            max_length=20,
            validators=[
                RegexValidator(
                    regex=r'^\+?1?\d{9,15}$',
                    message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres."
                )
            ],
            **kwargs
        )


class RequestOTPSerializer(serializers.Serializer):
    phone_whatsapp = PhoneField()


class VerifyOTPSerializer(serializers.Serializer):
    phone_whatsapp = PhoneField()
    code = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(min_length=8, write_only=True)
    
    def validate_code(self, value):
        """Ensure code is digits only"""
        if not value.isdigit():
            raise serializers.ValidationError("Le code doit contenir uniquement des chiffres")
        return value


class SetPasswordSerializer(serializers.Serializer):
    phone_whatsapp = PhoneField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Les mots de passe ne correspondent pas"
            })
        
        # Password strength validation
                    
        return data


class LoginSerializer(serializers.Serializer):
    phone_whatsapp = PhoneField()
    password = serializers.CharField(write_only=True)


class OTPLogAdminSerializer(serializers.ModelSerializer):
    """Admin-only serializer that includes the actual OTP code"""
    status = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPCode
        fields = ["id", "phone_number", "code", "status", "time_ago", "created_at", "is_used", "updated_at"]
    
    def get_status(self, obj):
        if obj.is_used:
            return "used"
        if timezone.now() - obj.created_at > timedelta(minutes=5):
            return "expired"
        return "active"
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.updated_at)

class AdminUserSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True, default=None)
    business_type = serializers.CharField(source='business.business_type', read_only=True, default=None)
    business_id = serializers.IntegerField(source='business.id', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "phone_whatsapp", "is_active", "is_staff", 
            "is_superuser", "date_joined", "business_id", 
            "business_name", "business_type"
        ]


class ProductSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    vendor_phone = serializers.CharField(source='business.owner.phone_whatsapp', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'business', 'business_name', 'name', 'description', 
            'price', 'currency', 'image', 'image_url', 'exchange_for', 'slug',
            'location', 'is_available', 'created_at', 'updated_at', 
            'vendor_phone'
        ]
        read_only_fields = ['business', 'slug']
    
    def get_image_url(self, obj):
        """Return full URL for image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate_price(self, value):
        """Ensure price is positive"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif")
        return value


class BusinessSerializer(serializers.ModelSerializer):
    # FIXED: Use StringRelatedField or limit products to avoid N+1
    products = serializers.SerializerMethodField()
    owner_phone = serializers.CharField(source='owner.phone_whatsapp', read_only=True)
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Business
        fields = [
            'id', 'owner_phone', 'name', 'slug', 'description', 
            'logo', 'business_type', 'products', 'product_count',
            'created_at', 'location'
        ]
        read_only_fields = ['slug']
    
    def get_products(self, obj):
        """Limit products to recent 20 to avoid huge payloads"""
        # In view, use prefetch_related('products') to optimize
        products = obj.products.all().order_by('-updated_at')
        return ProductSerializer(products, many=True, context=self.context).data
    
    def validate_name(self, value):
        """Ensure business name is unique"""
        if Business.objects.filter(name__iexact=value).exclude(
            id=getattr(self.instance, 'id', None)
        ).exists():
            raise serializers.ValidationError("Une boutique avec ce nom existe déjà")
        return value


class UserSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = User
        fields = ['id', 'phone_whatsapp', 'business', 'is_active', 'date_joined']
        read_only_fields = ['phone_whatsapp']  # Prevent phone changes via this serializer


    