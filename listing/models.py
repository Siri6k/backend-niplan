import uuid
from django.db import models
from django.utils.text import slugify
from PIL import Image
from io import BytesIO
from django.core.files import File

from base_api.models import Business, User

# --- 1. PROFIL UTILISATEUR (Identité de base) ---
class UserProfile(models.Model):
    ACCOUNT_LEVELS = [
        ('BASIC', 'Compte Gratuit'),
        ('PRO', 'Professionnel / Fournisseur'),
        ('OFFICIAL', 'Marque Officielle'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    account_type = models.CharField(max_length=15, choices=ACCOUNT_LEVELS, default='BASIC')
    phone_number = models.CharField(max_length=20, unique=True)
    is_verified = models.BooleanField(default=False) # Badge de confiance
    
    def __str__(self):
        return f"Profil de {self.user.phone_whatsapp}"

    
# --- 2. LISTING (L'Annonce Flexible) ---
class Listing(models.Model):
    # Lien vers le business (Propriétaire)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='listings')
    
    # Champs de base
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    category = models.CharField(max_length=50) # Ex: Appartement, Smartphone
    
    # La puissance de la 2.0 : Attributs spécifiques (JSON)
    # Ex: {"chambres": 3, "etat": "neuf", "stock": 10}
    specs = models.JSONField(default=dict, blank=True)
    
    # Options Troc
    is_for_barter = models.BooleanField(default=False)
    barter_target = models.CharField(max_length=255, blank=True) # Ce qu'il veut en échange

    # Localisation propre à l'annonce
    ville = models.CharField(max_length=100, default='Kinshasa')
    commune = models.CharField(max_length=100, blank=True, null=True)
    quartier = models.CharField(max_length=100, blank=True, null=True)

    # État de l'annonce
    is_active = models.BooleanField(default=True)
    is_promoted = models.BooleanField(default=False)
    
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True)
    # Timestamps (Indispensable pour le cache et le tri)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['business', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Optionnel: ajouter un ID unique si deux produits ont le même nom
            if Listing.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-by-{slugify(self.business.name)}"
                if Listing.objects.filter(slug=self.slug).exists():
                    self.slug = f"{self.slug}-{slugify(self.business.name)}-{str(uuid.uuid4())[:8]}"
        self.is_active = True
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title

# --- 4. IMAGES (Multi-upload & Compression) ---
class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/%Y/%m/')
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Compression automatique avant de sauvegarder
        new_img = self.compress_image(self.image)
        self.image = new_img
        super().save(*args, **kwargs)

    def compress_image(self, image):
        img = Image.open(image)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionnement max pour mobile
        img.thumbnail((1200, 1200))
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=70, optimize=True)
        output.seek(0)
        
        return File(output, name=image.name.split('.')[0] + '.jpg')

# --- 5. VERIFICATION (Système KYC) ---
class VerificationRequest(models.Model):
    STATUS = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
    ]
    DOC_TYPES = [
        ('ID_CARD', 'Carte d’identité / Électeur'),
        ('PASSPORT', 'Passeport'),
        ('RCCM', 'Registre de Commerce (Pro)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOC_TYPES, default='ID_CARD')
    document_front = models.ImageField(upload_to='kyc/front/%Y/')
    document_back = models.ImageField(upload_to='kyc/back/%Y/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Si la vérification est approuvée, on met à jour le profil utilisateur
        if self.status == 'APPROVED':
            profile = self.user.userprofile
            profile.is_verified = True
            profile.save()
        super().save(*args, **kwargs)