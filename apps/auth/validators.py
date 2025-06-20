import re
from django.conf import settings
from django.core.validators import validate_email
from rest_framework.validators import ValidationError

from .choices import (
    OtpPurpose,
)


def is_valid_email(email):
    try:
        return validate_email(email) == None
    except:
        return False    

def validate_otp_request_purpose(otp_purpose_key):
    if otp_purpose_key is None or otp_purpose_key not in (key for key, value in OtpPurpose.choices):
        raise ValidationError(
            detail="Invalid purpose to request for OTP.",
        )
    return otp_purpose_key

def validate_otp_recipient(recipient):
    if not is_valid_email(recipient):
        raise ValidationError(
            detail="Invalid recipient",
        )
    return recipient.lower()


def validate_otp_code(code, min_len=None, max_len=None, exact_len=None):
    pattern = r'^[A-Z0-9]'

    if exact_len:
        pattern = pattern + '{'+str(exact_len)+'}$'
    else:
        if min_len and max_len:
            pattern = pattern + '{'+str(min_len) + ', '+ str(max_len)+'}$'
        elif min_len:
            pattern = pattern + '{'+str(min_len)+'}+$'
        elif max_len:
            pattern = pattern + '{0, '+str(max_len)+'}$'

    if pattern[-1] != '$': # means no len provided, default to 6 digits
        pattern = pattern + rf'{{{settings.OTP_CHAR_LENGTH}}}$'
    valid_code = bool(re.match(pattern=pattern, string=code))
    if not valid_code:
        raise ValidationError(
            detail=f"Invalid otp Code"
        )
    return code