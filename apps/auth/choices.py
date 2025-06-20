from django.db import models


class OtpPurpose(models.TextChoices):
    CHANGE_PASSWORD = 'change_password', 'Change Password'
    CREATE_NEW_ACCOUNT = 'create_new_account', 'Create New Account'
    DELETE_ACCOUNT = "delete_account", "Delete Account"
    RESET_PASSWORD = 'reset_password', 'Reset Password'
    VERIFY_EMAIL = 'verify_email', 'Verify Email'


class UserType(models.TextChoices):
    ASSISTANT = 'assistant', 'Assistant '
    USER = 'user', 'User'