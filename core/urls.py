from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from base_api.controllers.ProductController import (
    ProductListView,
    MyProductViewSet,
)
from base_api.controllers.AuthController import (
    # Nouveau système
    DetectUserFlowView,
    NewUserRequestOTPView,
    NewUserVerifyOTPView,
    LegacyUserSetPasswordView,
    LoginView,
    # Ancien (deprecated)
    RequestOTPView,
    VerifyOTPView,
)
from base_api.controllers.AdminController import AdminUserListView, AdminOTPLogView
from base_api.controllers.BusinessController import BusinessDetailView, MyBusinessUpdateView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'my-products', MyProductViewSet, basename='my-product')


urlpatterns = [
    path('admin/', admin.site.urls),

   
    # URLs pour la documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Vue Swagger UI : ta documentation interactive !
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # --- AUTHENTIFICATION ---
     # === NOUVEAU SYSTÈME ===
    
    # Détection intelligente (recommandé en premier)
    path('api/auth/detect-flow/', DetectUserFlowView.as_view(), name='detect-flow'),
    
    # Nouveaux utilisateurs (OTP + création compte)
    path('api/auth/register/request-otp/', NewUserRequestOTPView.as_view(), name='register-request-otp'),
    path('api/auth/register/verify-otp/', NewUserVerifyOTPView.as_view(), name='register-verify-otp'),
    
    # Anciens utilisateurs (setup MDP sans OTP)
    path('api/auth/legacy/set-password/', LegacyUserSetPasswordView.as_view(), name='legacy-set-password'),
    
    # Login standard
    path('api/auth/login/', LoginView.as_view(), name='login'),
    
    # === ANCIEN SYSTÈME (temporaire) ===
    path('api/phone/request-otp/', RequestOTPView.as_view(), name='request-otp-deprecated'),
    path('api/phone/verify-otp/', VerifyOTPView.as_view(), name='verify-otp-deprecated'),
    #----------------------------------------------------------------#
    
    # --- PRODUITS PUBLIC ---
    path('api/products/', ProductListView.as_view(), name='product-list'),

    # --- CRUD PRIVÉ (La correction est ici) ---
    # On inclut simplement les URLs du router à la racine de 'api/'
    # Le router va générer : 
    # GET/POST  -> api/my-products/
    # GET/PUT/PATCH/DELETE -> api/my-products/<slug>/
    path('api/', include(router.urls)),
    
    # --- BUSINESS / BOUTIQUE ---
    path('api/business/<slug:slug>/', BusinessDetailView.as_view(), name='business-detail'),
    path('api/my-business/update/', MyBusinessUpdateView.as_view(), name='business-update'),

    # --- ADMIN ---
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('api/admin/otps/', AdminOTPLogView.as_view(), name='admin-otps'),

    # --- LISTING (Annonces) ---
    path('api/v2/', include('listing.urls')),
]

# Servir les fichiers média en local (Cloudinary prend le relais en prod)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)