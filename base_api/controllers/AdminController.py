from rest_framework import generics, permissions
from rest_framework.permissions import IsAdminUser
from base_api.models import User, OTPCode
from base_api.serializers import AdminUserSerializer, OTPLogSerializer


class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by('-date_joined')

class AdminOTPLogView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = OTPLogSerializer

    def get_queryset(self):
        return OTPCode.objects.all().order_by('-id')[:20]