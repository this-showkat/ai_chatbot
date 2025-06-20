import random
import string
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.validators import ValidationError
from .choices import (
    OtpPurpose,
)
from .models import (
    Otp,
)


User = get_user_model()

def generate_otp(otp_char_length=settings.OTP_CHAR_LENGTH):
    character_domain = string.ascii_uppercase + string.digits
    otp = ''.join(random.choices(character_domain, k=otp_char_length))
    return otp

def get_otp_purpose_label_by_key(given_key):
    label = [label for key, label in OtpPurpose.choices if key==given_key]
    return ''.join(label)

def send_otp(otp_obj):
    if not isinstance(otp_obj, Otp):
        raise ValidationError(detail="Incorrect otp instance.")
    subject = f"{settings.APP_SHORT_NAME}: OTP for {get_otp_purpose_label_by_key(otp_obj.purpose).title()}!"
    message_lines = [
        "Dear User,",
        f"Greetings from {settings.APP_FULL_NAME}!",
        f"Your OTP to {get_otp_purpose_label_by_key(otp_obj.purpose).lower()} at {settings.APP_SHORT_NAME} is: {otp_obj.code} and it is only valid for {settings.OTP_VALIDITY_IN_MINUTES} minutes!",
        "Please remember, you must not share this OTP with anyone else.",
        "",
        "---",
        "Regards,",
        f"{settings.APP_SHORT_NAME} Community",
        f"{settings.APP_DOMAIN_NAME}"
    ]
    send_mail(
        subject=subject,
        message='\n'.join(message_lines),
        from_email=f"{settings.EMAIL_SENDER_NAME_FOR_OTP}<{settings.EMAIL_HOST_USER}>",
        recipient_list=[otp_obj.recipient],
        fail_silently=False
    )
    return True


def otp_applicability_test(code, purpose, recipient, _purpose=[], user=None):
    """
    return otp object if valid, otherwise raise exception
    """

    try:
        otp_obj = Otp.objects.get(purpose=purpose, recipient=recipient, code=code, is_verified=True)

    except Otp.DoesNotExist:
        raise ValidationError(
            detail="OTP verification is required."
        )
    
    if otp_obj.purpose not in _purpose:
        raise ValidationError(
            detail="Invalid purpose detected"
        )
    if otp_obj.purpose == OtpPurpose.CREATE_NEW_ACCOUNT:
        try:
            existing_user = User.objects.get(email=otp_obj.recipient)
            if existing_user.is_deleted:
                raise ValidationError(
                    detail=f"you had an account with this {otp_obj.recipient_type} and it was deleted. Please contact support for creating new accoun."
                )
            raise ValidationError(
                detail=f"An user with '{otp_obj.recipient}' already exists.",
            )
        
        except User.DoesNotExist:
            pass 

    elif otp_obj.purpose in [k for k, v in OtpPurpose.choices]:
        try:
            target_user = User.objects.get(email=otp_obj.recipient)
            if target_user != user:
                raise ValidationError(
                    detail='Permission denied'
                )
        
        except User.DoesNotExist:
            raise ValidationError(
                detail=f"User with '{otp_obj.recipient}' doesn't exist."
            )
    
    else:
        raise ValidationError(
            detail="Invalid purpose detected"
        )
    if otp_obj.is_applied or otp_obj.verified_at is None:
        raise ValidationError(
            "The OTP is invalid. Please start over again."
        )
    
    otp_apply_expires_at = otp_obj.verified_at + timedelta(minutes=settings.VERIFIED_OTP_APPLICABLE_IN_MINUTES)
    
    if otp_apply_expires_at < timezone.now():
        raise ValidationError(
            f"Action must be completed by {settings.VERIFIED_OTP_APPLICABLE_IN_MINUTES} Minutes after OTP verification. Please start over again."
        )
    
    return otp_obj



def set_otp_applied(otp_obj):
    otp_obj.is_deleted=True
    otp_obj.save()