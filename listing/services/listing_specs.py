from rest_framework import serializers

from listing.services.listing_types import (
    LISTING_TYPE_BARTER,
    LISTING_TYPE_OTHER,
    PRICE_OPTIONAL_TYPES,
)


def validate_listing_payload(data):
    listing_type = data.get("listing_type")
    price = data.get("price")
    barter_target = data.get("barter_target")
    specs = data.get("specs")

    if price is None and listing_type not in PRICE_OPTIONAL_TYPES and listing_type != LISTING_TYPE_BARTER:
        raise serializers.ValidationError(
            {"price": "Le prix est requis pour ce type d'annonce."}
        )

    if listing_type == LISTING_TYPE_BARTER:
        data["is_for_barter"] = True

    if data.get("is_for_barter") and not barter_target:
        raise serializers.ValidationError(
            {"barter_target": "barter_target est requis si is_for_barter=True"}
        )

    if specs is None:
        data["specs"] = {}
    elif not isinstance(specs, dict):
        raise serializers.ValidationError(
            {"specs": "specs doit etre un objet JSON."}
        )

    if listing_type == LISTING_TYPE_OTHER and price is None:
        data.setdefault("currency", "USD")

    return data
