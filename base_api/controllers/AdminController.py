from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.permissions import IsAdminUser
from base_api.models import User, OTPCode
from base_api.serializers import AdminUserSerializer, OTPLogAdminSerializer


class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by('-date_joined')

class AdminOTPLogView(generics.ListAPIView):
    serializer_class = OTPLogAdminSerializer  # Use the admin version
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        yesterday = timezone.now() - timedelta(days=1)
        return OTPCode.objects.filter(
            created_at__gte=yesterday
        ).order_by('-created_at')