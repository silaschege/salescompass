from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import AccountsUserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_accounts_user_profile(sender, instance, created, **kwargs):
    if created:
        AccountsUserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_accounts_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'accounts_profile'):
        instance.accounts_profile.save()
