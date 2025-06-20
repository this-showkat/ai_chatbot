from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .choices import (
    OtpPurpose,
)
from .models import (
    Otp,
)
from .validators import (
    is_valid_email,
)
from .utils import (
    generate_otp,
    otp_applicability_test,
    set_otp_applied,

)
from .validators import (
    validate_otp_request_purpose,
    validate_otp_recipient,
    validate_otp_code,
)


User = get_user_model()

from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.is_deleted or not self.user.is_active or not self.user.email_verified:
            raise AuthenticationFailed("No active account found with the given credentials")       

        data['id'] = self.user.id
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['photo'] = self.user.photo.url if self.user.photo else None
        return data
    

class SendOtpSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=OtpPurpose.choices)
    recipient = serializers.CharField(max_length=250)

    def validate_purpose(self, value):
        return validate_otp_request_purpose(otp_purpose_key=value)
    
    def validate_recipient(self, value):
        return validate_otp_recipient(recipient=value)

    def create(self, validated_data):
        new_otp = generate_otp()
        recipient = validated_data.pop('recipient', None)
        purpose = validated_data.pop('purpose', None)
        
        try:
            user = User.objects.get(email=recipient)
        except:
            user = None
        if purpose == OtpPurpose.CREATE_NEW_ACCOUNT:
            if user is not None:
                raise serializers.ValidationError(
                    detail="There's an account already exists with this recipient.",
                    code='account_exists'
                )
            
        last_otp = Otp.objects.filter(purpose=purpose, recipient=recipient).last()
        if last_otp is not None:
            now = timezone.now().replace(microsecond=0)
            if last_otp.expires_at > now:
                raise serializers.ValidationError(
                    detail=f"You already have a valid OTP. Please use that or wait until {timezone.localtime(last_otp.expires_at):%B %d, %Y at %I:%M %p}, then try again."
                )
            # Update the code object
            last_otp.code = new_otp
            last_otp.last_resent_at = timezone.now()
            last_otp.resents += 1
            last_otp.invalid_attempts = 0
            last_otp.is_applied = False
            last_otp.is_verified = False
            last_otp.is_deleted = False
            last_otp.save(update_fields=['code', 'last_resent_at', 'resents', 'invalid_attempts', 'is_applied', 'is_verified', 'updated_at', 'is_deleted'])
            return last_otp
        
        # create new object
        new_otp_obj = Otp.objects.create(purpose=purpose, recipient=recipient, code=new_otp)
        return new_otp_obj


class VerifyOtpSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=OtpPurpose.choices)
    recipient = serializers.CharField(max_length=250)
    code = serializers.CharField(max_length=6)

    def validate_purpose(self, value):
        return validate_otp_request_purpose(otp_purpose_key=value)
    
    def validate_recipient(self, value):
        return validate_otp_recipient(recipient=value)

    def validate_code(self, value):
        return validate_otp_code(code=value)

    def create(self, validated_data):
        purpose = validated_data.pop('purpose', None)
        recipient = validated_data.pop('recipient', None)
        code = validated_data.pop('code', None)
        try:
            last_otp = Otp.objects.get(purpose=purpose, recipient=recipient, is_deleted=False)
        except:
            raise serializers.ValidationError(
                detail="Otp does not exist"
            )
        now = timezone.now().replace(microsecond=0)
        if last_otp.invalid_attempts >= settings.OTP_MAX_INVALID_ATTEMPTS:
            raise serializers.ValidationError(
                detail=f"Maximum attempts limit '{settings.OTP_MAX_INVALID_ATTEMPTS}' reached for the OTP verfications. Please wait until {timezone.localtime(last_otp.expires_at):%B %d, %Y at %I:%M %p} then request for a new OTP."
            )
        if last_otp.expires_at < now:
            raise serializers.ValidationError(
                detail=f"Your otp has been expired at {timezone.localtime(last_otp.expires_at):%B %d, %Y at %I:%M %p}. Please request again for a new OTP."
            )
        if last_otp.code != code:
            last_otp.invalid_attempts += 1
            last_otp.save(update_fields=['invalid_attempts', 'updated_at'])
            raise serializers.ValidationError(
                detail="OTP did not match"
            )
        
        last_otp.is_verified = True
        last_otp.verified_at = timezone.now()
        last_otp.is_applied = False
        last_otp.save(update_fields=['is_verified', 'verified_at', 'is_applied', 'updated_at'])
        return last_otp


class CreateUserSerializer(VerifyOtpSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    photo = serializers.ImageField(required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    def create(self, validated_data):
        purpose = validated_data.pop('purpose', None)
        recipient = validated_data.pop('recipient', None)
        code = validated_data.pop('code', None)

        otp = otp_applicability_test(code=code, purpose=purpose, recipient=recipient, _purpose=[OtpPurpose.CREATE_NEW_ACCOUNT])
        validated_data['email_verified'] = True
    
        try:
            with transaction.atomic():
                instance = User.objects.create_user(email=recipient, **validated_data)
                set_otp_applied(otp_obj=otp)
            return instance

        except Exception as e:
            raise serializers.ValidationError(
                f"An error occurred during creating the account: {str(e)}"
            )


class ChangePasswordSerializer(VerifyOtpSerializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError(
                detail="Existing password is not correct."
            )
        return value
    
    def validate_new_password(self, value):
        validate_password(password=value, user=self.context.get('request').user)
        return value

    def validate(self, attrs):
        if attrs.get('current_password') == attrs.get('new_password'):
            raise serializers.ValidationError(
                detail="New password can not be same as current password"
            )
        return super().validate(attrs)

    def create(self, validated_data):
        purpose = validated_data.pop('purpose', None)
        recipient = validated_data.pop('recipient', None)
        code = validated_data.pop('code', None)
        new_password = validated_data.pop('new_password')
        user = self.context.get('request').user
        otp = otp_applicability_test(code=code, purpose=purpose, recipient=recipient, _purpose=[OtpPurpose.CHANGE_PASSWORD], user=self.context.get('request').user)
        with transaction.atomic():
            user.set_password(new_password)
            user.save()
            set_otp_applied(otp_obj=otp)
        return user


class ResetPasswordSerializer(VerifyOtpSerializer):
    new_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('recipient')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                detail="User does does not exist"
            )
        attrs['user'] = user
        validate_password(password=attrs.get('new_password'), user=user)       
        return super().validate(attrs)

    def create(self, validated_data):
        purpose = validated_data.pop('purpose', None)
        recipient = validated_data.pop('recipient', None)
        code = validated_data.pop('code', None)
        new_password = validated_data.pop('new_password')
        user = validated_data.get('user')
        otp = otp_applicability_test(code=code, purpose=purpose, recipient=recipient, _purpose=[OtpPurpose.RESET_PASSWORD], user=user)
        with transaction.atomic():
            user.set_password(new_password)
            user.save()
            set_otp_applied(otp_obj=otp)
        return user
        


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        exclude = ['password']


class UserBioSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'photo')


class UserMeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id', 'last_login', 'username', 'first_name', 'last_name', 'email', 'photo')
