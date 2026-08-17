from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SchoolProfile, SMSWallet


@receiver(post_save, sender=SchoolProfile)
def create_sms_wallet(sender, instance, created, **kwargs):

    if created:
        SMSWallet.objects.get_or_create(
            school=instance
        )