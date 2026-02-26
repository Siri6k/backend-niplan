import uuid
from django.utils.text import slugify

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone_whatsapp, password=None, **extra_fields):
        if not phone_whatsapp:
            raise ValueError("Le numéro WhatsApp est obligatoire")
        
        user = self.model(phone_whatsapp=phone_whatsapp, **extra_fields)
        
        if password:
            user.set_password(password)
            user.password_setup_required = False  # MDP défini = setup terminé
        else:
            user.set_unusable_password()
            user.password_setup_required = True   # Doit définir MDP plus tard
            
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_whatsapp, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if not password:
            raise ValueError("Le superuser doit avoir un mot de passe")
            
        return self.create_user(phone_whatsapp, password, **extra_fields)


class User(AbstractUser):
    username = None
    
    phone_whatsapp = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Numéro WhatsApp"
    )
    
    is_active = models.BooleanField(default=False)
    
    # TRUE = ancien user qui doit définir son MDP (ou nouveau sans MDP)
    # FALSE = MDP déjà défini
    password_setup_required = models.BooleanField(default=True)
    
    # TRUE = numéro vérifié par OTP (nouveaux users)
    is_phone_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone_whatsapp'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.phone_whatsapp

    @property
    def can_login_with_password(self):
        """Vérifie si l'utilisateur peut se connecter avec un mot de passe"""
        return not self.password_setup_required and self.has_usable_password()
class Business(models.Model):
    TYPES = [
        ('SHOP', 'Boutique / Vente'),
        ('TROC', 'Troc / Échange'),
        ('IMMO', 'Immobilier'),
        ('SERVICE', 'Services / Prestations'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, default='Kinshasa, RDC')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    business_type = models.CharField(max_length=10, choices=TYPES, default='SHOP')
    
    # Metadata pour stocker horaires, réseaux sociaux, etc.
    metadata = models.JSONField(default=dict, blank=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('CDF', 'Franc Congolais'),
        ]
        
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default="USD") # USD ou CDF
    image = models.ImageField(upload_to='products/')
    # models.py
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True)

    
    # Pour le TROC : Ce que le vendeur recherche en échange
    exchange_for = models.CharField(max_length=200, blank=True, null=True)
    
    # Pour l'IMMO : Ville/Quartier
    location = models.CharField(max_length=100, blank=True, null=True)
    
    is_available = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.business.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Optionnel: ajouter un ID unique si deux produits ont le même nom
            if Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-by-{slugify(self.business.name)}"
                if Product.objects.filter(slug=self.slug).exists():
                    self.slug = f"{self.slug}-{slugify(self.business.name)}-{str(uuid.uuid4())[:8]}"
        self.is_available = True
        super().save(*args, **kwargs)
    


class OTPCode(models.Model):
    phone_number = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)  # Missing field referenced in React
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['phone_number', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.phone_number}: {self.code}"



