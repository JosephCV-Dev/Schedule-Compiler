"""Sustitución temporal de ofertas sin modificar el catálogo de origen."""

from dataclasses import replace

from schedule_compiler.domain.models import Catalog, Offer


def overlay_offers(catalog: Catalog, declarations: tuple[Offer, ...]) -> Catalog:
    ids = [offer.id for offer in declarations]
    if len(ids) != len(set(ids)):
        raise ValueError("DECLARACION_DUPLICADA: dos propuestas tienen el mismo ID.")
    merged = {offer.id: offer for offer in catalog.offers}
    merged.update((offer.id, offer) for offer in declarations)
    return replace(catalog, offers=tuple(merged.values()))
