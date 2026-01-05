import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password"""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        verbose_name=_('email address'),
        help_text=_('Required. A valid email address.'),
    )
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        help_text=_('Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ only.'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('full name'),
        help_text=_('Required. Your full name.'),
    )
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        default='default-profile.jpg',
        verbose_name=_('profile picture'),
        help_text=_('Optional. Upload a profile picture.'),
    )
    # Optional fields
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Enter a valid phone number.'),
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name=_('phone number'),
        help_text=_('Optional. International format preferred.'),
    )
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text=_('Designates that this user has all permissions without explicitly assigning them.'),
    )

    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        db_table = 'custom_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['date_joined']),
        ]

    def __str__(self):
        return self.name or self.email

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name.split()[0] if self.name else self.username
    
    def profile_pic_url(self):
        if self.profile_pic and self.profile_pic != 'default-profile.png':
            return self.profile_pic.url
        return f"{settings.STATIC_URL}images/default-profile.png" if hasattr(settings, 'STATIC_URL') else ''