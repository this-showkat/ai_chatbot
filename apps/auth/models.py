from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from channels.db import database_sync_to_async

from .choices import (
    OtpPurpose,
    UserType,
)
from .validators import (
    is_valid_email,
)


class Otp(models.Model):
    purpose = models.CharField(max_length=20, choices=OtpPurpose.choices)
    recipient = models.CharField(max_length=200)
    code = models.CharField(max_length=6)
    last_resent_at = models.DateTimeField(blank=True, null=True)
    resents = models.PositiveSmallIntegerField(default=0)
    invalid_attempts = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    is_applied = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, **kwargs):
        self.recipient = self.recipient.lower()
        return super().save(**kwargs)

    @property    
    def expires_at(self):
        otp_created_at = self.last_resent_at if self.last_resent_at is not None else self.created_at
        otp_expires_at = otp_created_at + timedelta(minutes=settings.OTP_VALIDITY_IN_MINUTES)
        return otp_expires_at.replace(microsecond=0)
    
    @property
    def verified_otp_is_applicable(self):
        if self.is_verified and not self.is_applied and self.verified_at is not None and not self.is_deleted:
            return self.verified_at + timedelta(minutes=settings.VERIFIED_OTP_APPLICABLE_IN_MINUTES) > timezone.now()
        return False
    
    @classmethod
    def delete_applied_instances(cls):
        Otp.objects.filter(is_applied=True).update(is_deleted=True, deleted_at=timezone.now())
        return
    
    def __str__(self):
        return f"{self.purpose}: {self.code}"
    

class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='users/profile-photos', blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    user_type = models.CharField(max_length=30, choices=UserType.choices, default=UserType.USER)

    def __str__(self):
        return f"ID: {self.id}, username: {self.username}, email: {self.email}"

    @classmethod
    @database_sync_to_async
    def get_ai_agent(cls, ai_agent_username=None):
        """
        Takes ai_agent_username optionally and return user object. if doesn't exist, create one.
        """
        ai_agent_username = ai_agent_username if ai_agent_username else settings.AI_AGENT_USERNAME
        print(f"ai agent username: {ai_agent_username}")
        user_agent, created = cls.objects.get_or_create(username=ai_agent_username, 
                                              defaults={
                                                  "email": f"{ai_agent_username}@email.ext",
                                                  "user_type": UserType.ASSISTANT,
                                              })
        return user_agent
    
    @property
    def is_admin(self):
        return self.is_superuser or self.is_staff