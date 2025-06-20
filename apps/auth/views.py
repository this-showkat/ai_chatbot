from django.db import transaction
from django.shortcuts import render
from django.utils import timezone

from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .choices import (
    OtpPurpose,
)
from .serializers import (
    SendOtpSerializer,
    VerifyOtpSerializer,
    CreateUserSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    UserMeSerializer,

)
from .utils import (
    send_otp,
)

class AuthViewSet(GenericViewSet):
    permission_classes = (AllowAny,)

    @action(methods=['POST'], detail=False, url_path='send-otp')
    def send_otp(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = SendOtpSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            last_otp = serializer.create(serializer.validated_data)
            # now send the otp
            try:
                send_otp(last_otp)
                return Response(
                    data={"message": "OTP Sent", "expires_at": timezone.localtime(last_otp.expires_at)},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    data={"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
    @action(url_path='verify-otp', methods=['POST'], detail=False)
    def verify_otp(self, request, *args, **kwargs):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_obj = serializer.create(serializer.validated_data)
        return Response(
            data={"message": "OTP verified."},
            status=status.HTTP_200_OK
        )

    @action(url_path='create-account', methods=['POST'], detail=False)
    def create_account(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response(
                data={"error": "You already have an account and you are logged in from the account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(serializer.validated_data)

        return Response(
            data={"message": f"Congratulatins, {user.first_name}! You have successfully created an account."},
            status=status.HTTP_201_CREATED
        )
    
    @action(methods=['POST'], detail=False, url_path='reset-password')
    def reset_password(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data)
        return Response(
            data='Password reset successful. Try login now',
            status=status.HTTP_200_OK
        )


    @action(methods=('POST',), detail=False, url_path='login')
    def login(self, request):
        view = TokenObtainPairView.as_view()
        return view(request._request)
    
    @action(methods=('POST',), detail=False, url_path='refresh-token')
    def refresh_token(self, request):
        view = TokenRefreshView.as_view()
        return view(request._request)
    
    @action(methods=('POST',), detail=False, url_path='verify-token')
    def verify_token(self, request):
        view = TokenVerifyView.as_view()
        return view(request._request)
    
    @action(methods=('POST',), detail=False, url_path='logout', permission_classes=(IsAuthenticated,))
    def logout(self, request):
        try:
            token = request.data['refresh']
            token_instance = RefreshToken(token)
            token_instance.blacklist()
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except KeyError:
            return Response(
                {"detail": "Refresh token required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"{str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(methods=('GET',), detail=False, url_path='otp-purpose-list')
    def get_otp_purpose_list(self, request):
        otp_purposes = [{'key': key, 'label': label} for key, label in OtpPurpose.choices]
        return Response(otp_purposes)
    

class ProfileViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated,)

    @action(methods=('GET',), detail=False, url_path='me')
    def get_me(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
    