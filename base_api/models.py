import uuid
from django.utils.text import slugify

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone_whatsapp, password=None, **extra_fields):
        if not phone_whatsapp:
            raise ValueError("Le numéro WhatsApp est obligatoire")
        user = self.model(phone_whatsapp=phone_whatsapp, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_whatsapp, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Important pour l'admin

        return self.create_user(phone_whatsapp, password, **extra_fields)

class User(AbstractUser):
    # Supprime le champ username par défaut
    username = None 
    phone_whatsapp = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=False)
    
    # On branche le nouveau manager
    objects = UserManager()

    USERNAME_FIELD = 'phone_whatsapp'
    REQUIRED_FIELDS = [] # Plus besoin de username ici

    def __str__(self):
        return self.phone_whatsapp
  
class Business(models.Model):
    TYPES = [
        ('SHOP', 'Boutique / Vente'),
        ('TROC', 'Troc / Échange'),
        ('IMMO', 'Immobilier'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    business_type = models.CharField(max_length=10, choices=TYPES, default='SHOP')
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
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        if self.is_available is None:
            self.is_available = True
        super().save(*args, **kwargs)
    

class OTPCode(models.Model):
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']



