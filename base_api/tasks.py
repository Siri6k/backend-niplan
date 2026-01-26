from celery import shared_task
from .models import Product
import time

@shared_task
def notify_subscribers_task(product_id):
    product = Product.objects.get(id=product_id)
    # Simulation d'un travail lourd (envoi de 1000 emails ou SMS)
    # ... logique d'envoi ...
    return f"Notifications envoyées pour {product.title}"

@shared_task
def send_welcome_sms_task(phone_number, business_name):
    # Simuler l'envoi d'un SMS via une API externe
    print(f"Envoi du SMS à {phone_number}...")
    time.sleep(5) # On simule une attente de 5 secondes (l'API répond lentement)
    return f"SMS envoyé avec succès à {business_name}"