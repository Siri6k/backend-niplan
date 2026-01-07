from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from base_api.views import (
    AdminOTPLogView, AdminUserListView, MyProductListView, RequestOTPView, VerifyOTPView, 
    ProductListView, MyProductCreateView, MyProductDeleteView,
    BusinessDetailView, MyBusinessUpdateView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- AUTHENTIFICATION ---
    path('api/auth/request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # --- PRODUITS (PUBLIC & PRIVÉ) ---
    path('api/products/', ProductListView.as_view(), name='product-list'),
    path('api/my-products/', MyProductListView.as_view(), name='my-product-list'),
    path('api/my-products/create/', MyProductCreateView.as_view(), name='product-create'),
    path('api/my-products/<int:pk>/delete/', MyProductDeleteView.as_view(), name='product-delete'),

    # --- BUSINESS / BOUTIQUE ---
    path('api/business/<slug:slug>/', BusinessDetailView.as_view(), name='business-detail'),
    path('api/my-business/update/', MyBusinessUpdateView.as_view(), name='business-update'),

    # --- ADMIN ---
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('api/admin/otps/', AdminOTPLogView.as_view(), name='admin-otps'),
]

# Servir les fichiers média en local (Cloudinary prend le relais en prod)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)