from django.contrib import admin
from .models import User, Business, Product, OTPCode

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_whatsapp', 'is_active', 'date_joined')
    search_fields = ('phone_whatsapp',)
    list_filter = ('is_active',)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'business_type', 'created_at')
    search_fields = ('name', 'slug', 'owner__phone_whatsapp')
    prepopulated_fields = {'slug': ('name',)} # Remplissage auto du slug
    list_filter = ('business_type',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'price', 'currency', 'is_available')
    list_filter = ('is_available', 'currency', 'business')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available') # Permet de modifier direct dans la liste

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created_at')