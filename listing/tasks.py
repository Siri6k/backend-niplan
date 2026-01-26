from celery import shared_task
from .models import Listing
import time

@shared_task
def notify_subscribers_task(listing_id):
    listing = Listing.objects.get(id=listing_id)
    # Simulation d'un travail lourd (envoi de 1000 emails ou SMS)
    # ... logique d'envoi ...
    return f"Notifications envoyées pour {listing.title}"
