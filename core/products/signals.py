from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile

@receiver(post_save, sender=Product)
def create_thumbnail(sender, instance, **kwargs):
    if instance.image and not instance.thumbnail:
        img = Image.open(instance.image)
        img.convert('RGB')
        img.thumbnail((200, 200))
        
        thumb_io = BytesIO()
        img.save(thumb_io, 'JPEG', quality=85)
        
        # Save thumbnail without triggering another save signal loop
        # We use update_fields or disable signals if needed, 
        # but here we just check if thumbnail exists to avoid recursion
        
        # Actually simplest way to avoid recursion is to save directly to field if using update()
        # or just save with update_fields
        
        thumb_name = os.path.basename(instance.image.name)
        thumb_name = 'thumb_' + thumb_name
        
        instance.thumbnail.save(thumb_name, ContentFile(thumb_io.getvalue()), save=False)
        instance.save(update_fields=['thumbnail'])
