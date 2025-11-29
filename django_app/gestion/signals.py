"""
Signaux Django pour le module Gestion.
Notamment la création automatique de l'arborescence Drive lors de la création d'un dossier.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

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


@receiver(post_save, sender='gestion.Encaissement')
def creer_mouvement_encaissement(sender, instance, created, **kwargs):
    """Crée un mouvement de trésorerie (entrée) pour chaque encaissement"""
    from tresorerie.models import MouvementTresorerie

    if not instance.compte_tresorerie or instance.mouvement_tresorerie:
        return

    try:
        dossier = getattr(instance, 'dossier', None)
        libelle = f"Encaissement - {dossier.reference if dossier else 'N/A'}"

        mouvement = MouvementTresorerie.objects.create(
            compte=instance.compte_tresorerie,
            type_mouvement='entree',
            montant=instance.montant,
            date_mouvement=getattr(instance, 'date_encaissement', timezone.now().date()),
            libelle=libelle,
            dossier=dossier,
            reference_externe=f"ENC-{instance.pk}",
        )

        sender.objects.filter(pk=instance.pk).update(mouvement_tresorerie=mouvement)
    except Exception as e:
        logger.error(f"Erreur signal encaissement: {e}")


@receiver(post_delete, sender='gestion.Encaissement')
def supprimer_mouvement_encaissement(sender, instance, **kwargs):
    """Supprime le mouvement de trésorerie associé lors de la suppression d'un encaissement"""
    if instance.mouvement_tresorerie:
        try:
            instance.mouvement_tresorerie.delete()
        except:
            pass


@receiver(post_save, sender='gestion.Reversement')
def creer_mouvement_reversement(sender, instance, created, **kwargs):
    """Crée un mouvement de trésorerie (sortie) pour chaque reversement"""
    from tresorerie.models import MouvementTresorerie

    if not instance.compte_tresorerie or instance.mouvement_tresorerie:
        return

    try:
        dossier = getattr(instance, 'dossier', None)
        creancier = getattr(instance, 'creancier', None)
        libelle = f"Reversement"
        if creancier:
            libelle += f" à {creancier}"

        mouvement = MouvementTresorerie.objects.create(
            compte=instance.compte_tresorerie,
            type_mouvement='sortie',
            montant=instance.montant,
            date_mouvement=getattr(instance, 'date_reversement', timezone.now().date()),
            libelle=libelle,
            dossier=dossier,
            reference_externe=f"REV-{instance.pk}",
        )

        sender.objects.filter(pk=instance.pk).update(mouvement_tresorerie=mouvement)
    except Exception as e:
        logger.error(f"Erreur signal reversement: {e}")


@receiver(post_delete, sender='gestion.Reversement')
def supprimer_mouvement_reversement(sender, instance, **kwargs):
    """Supprime le mouvement de trésorerie associé lors de la suppression d'un reversement"""
    if instance.mouvement_tresorerie:
        try:
            instance.mouvement_tresorerie.delete()
        except:
            pass
