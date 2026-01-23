import os
from pathlib import Path
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SÉCURITÉ ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-123')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*'] # À restreindre plus tard à ton domaine .vercel.app ou .railway.app

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage', # Pour Cloudinary
    'cloudinary',
    'whitenoise.runserver_nostatic',

    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'drf_spectacular', # Pour la documentation API
    'base_api',
    'listing',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Pour les fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Indispensable pour React
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ['core/templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'





# --- BASE DE DONNÉES (Railway auto-config) ---
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}
# AJOUTE CECI JUSTE EN DESSOUS :
if not DEBUG:  # Si on est en production sur Render
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }

    
# --- AUTHENTIFICATION ---
AUTH_USER_MODEL = 'base_api.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # AJOUTE CETTE LIGNE :
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30), # Longue durée pour le confort du vendeur
    'ROTATE_REFRESH_TOKENS': True,
    'SIGNING_KEY': SECRET_KEY,
}

# --- FICHIERS STATIQUES & MÉDIA (Cloudinary) ---
# settings.py

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Utilise cette classe plus simple (elle compresse mais ne crée pas de manifeste complexe)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Indispensable pour éviter que le build plante sur un fichier JS de l'admin
WHITENOISE_MANIFEST_STRICT = False

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# --- CORS (Pour la connexion avec le Frontend Vercel) ---
CORS_ALLOW_ALL_ORIGINS = True # Pour le MVP, simplifie la connexion avec Vercel
# À restreindre plus tard avec CORS_ALLOWED_ORIGINS = [...]
CORS_ALLOW_ALLOWED_ORIGINS = [
    'https://niplan-market.vercel.app',
    'http://localhost:3000', # Pour le développement local
]


# Configure le schéma OpenAPI
SPECTACULAR_SETTINGS = {
    'TITLE': 'Niplan API',
    'DESCRIPTION': 'Documentation de l\'API Niplan pour les vendeurs et les clients.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False, # Pour servir la doc HTML sans le fichier schema brut
    # ... autres options si besoin
}

# --- CACHE (Redis) ---
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CACHE_TTL = 60 * 5  # 5 minutes