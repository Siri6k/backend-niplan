# Standard lib
import json
import os
import random

# Django
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model

# DRF
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError

# JWT
from rest_framework_simplejwt.tokens import RefreshToken

# HTTP
import requests

# Local apps
from base_api.tasks import send_welcome_sms_task, notify_subscribers_task
from base_api.models import User, Business, Product, OTPCode
from base_api.serializers import UserSerializer, BusinessSerializer, ProductSerializer
