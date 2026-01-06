from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import User, Business

@receiver(post_save, sender=User)
def create_automated_business(sender, instance, created, **kwargs):
    """
    Lance la création d'une boutique dès qu'un nouvel utilisateur s'inscrit.
    """
    if created:
        # On crée un nom par défaut (ex: Boutique +243...)
        default_name = f"Boutique {instance.phone_whatsapp}"
        
        # On génère un slug unique basé sur le téléphone pour éviter les doublons
        # Ex: boutique-24381000000
        unique_slug = slugify(f"shop-{instance.phone_whatsapp}")

        Business.objects.create(
            owner=instance,
            name=default_name,
            slug=unique_slug,
            description="Bienvenue dans ma nouvelle boutique Kifanyi !"
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Assure la mise à jour automatique si nécessaire.
    """
    instance.business.save()