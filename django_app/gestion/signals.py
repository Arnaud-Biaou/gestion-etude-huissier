"""
Signaux Django pour le module Gestion.
Notamment la création automatique de l'arborescence Drive lors de la création d'un dossier.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='gestion.Dossier')
def creer_arborescence_drive(sender, instance, created, **kwargs):
    """
    Signal déclenché après la création d'un dossier juridique.
    Crée automatiquement l'arborescence de dossiers virtuels dans le Drive.

    Note: Ce signal est un filet de sécurité. La création principale
    est faite dans la vue nouveau_dossier() après l'ajout des parties,
    pour avoir accès au créancier/demandeur dans le nom du dossier.

    Ce signal ne crée l'arborescence que si elle n'existe pas déjà.
    """
    if not created:
        return

    # Vérifier si l'arborescence existe déjà (créée par la vue)
    from documents.models import DossierVirtuel
    if DossierVirtuel.objects.filter(dossier_juridique=instance).exists():
        return

    try:
        from documents.services.document_service import DocumentService

        # Récupérer l'utilisateur créateur si disponible
        user = getattr(instance, 'cree_par', None)

        service = DocumentService(utilisateur=user)
        service.creer_structure_dossier_juridique(instance, user=user)

        logger.info(
            f"Arborescence Drive créée automatiquement pour le dossier {instance.reference}"
        )

    except Exception as e:
        # Ne pas bloquer la création du dossier en cas d'erreur
        logger.error(
            f"Erreur création arborescence Drive pour dossier {instance.reference}: {e}"
        )
