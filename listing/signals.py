# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Listing

@receiver([post_save, post_delete], sender=Listing)
def clear_listing_cache(sender, instance, **kwargs):
    # On vide tout le cache des recherches pour forcer l'actualisation
    cache.delete_pattern("listings_*")