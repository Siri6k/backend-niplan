from django.core.management.base import BaseCommand
from django.db import transaction

from base_api.models import Product
from listing.models import Listing, ListingImage

class Command(BaseCommand):
    help = "Migre les produits Niplan v1 vers la structure Listing v2"

    def handle(self, *args, **kwargs):
        self.stdout.write("Début de la migration vers Niplan 2.0...")

        with transaction.atomic():
            old_products = Product.objects.all()
            count = 0

            for prod in old_products:
                new_listing = Listing.objects.create(
                    business=prod.business if hasattr(prod, "business") else None,
                    title=prod.name,
                    description=prod.description or "",
                    price=prod.price or 0,
                    currency=prod.currency or "USD",
                    category="Général",
                    is_for_barter=bool(prod.exchange_for),
                    barter_target=prod.exchange_for or "",
                    ville=prod.location or "Kinshasa",
                    specs={
                        "old_id": prod.id,
                        "migrated": True,
                        "condition": getattr(prod, "condition", "unknown"),
                        "stock_status": "in_stock",
                        "location": getattr(prod, "location", "unknown"),
                        "old_slug": getattr(prod, "slug", ""),
                    },
                )

                if getattr(prod, "image", None):
                    ListingImage.objects.create(
                        listing=new_listing,
                        image=prod.image,
                        is_main=True,
                    )

                count += 1

            self.stdout.write(
                self.style.SUCCESS(f"Succès : {count} produits migrés vers Listing 2.0")
            )
