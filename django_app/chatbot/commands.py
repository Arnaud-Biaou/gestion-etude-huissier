"""
Executeurs de commandes pour le chatbot.
Section 18 DSTD v3.2 - Commandes pour tresorerie, comptabilite, dossiers, courriers.
"""

from decimal import Decimal
from django.utils import timezone


def get_solde_tresorerie(utilisateur):
    """Recupere le solde de tresorerie."""
    try:
        from tresorerie.models import CompteBancaire
        comptes = CompteBancaire.objects.filter(actif=True)
        total = sum(c.solde_actuel for c in comptes)
        return {
            'success': True,
            'message': f"Solde total de tresorerie: {total:,.0f} FCFA".replace(',', ' '),
            'data': {'solde_total': str(total)}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Erreur lors de la recuperation du solde: {str(e)}",
            'data': {}
        }


def get_programme_jour(utilisateur):
    """Recupere le programme du jour."""
    try:
        from agenda.models import RendezVous, Tache
        aujourdhui = timezone.now().date()

        rdvs = RendezVous.objects.filter(
            date=aujourdhui,
            utilisateur=utilisateur
        ).order_by('heure_debut')

        taches = Tache.objects.filter(
            date_echeance=aujourdhui,
            utilisateur=utilisateur,
            terminee=False
        )

        message = f"Programme du {aujourdhui.strftime('%d/%m/%Y')}:\n"

        if rdvs.exists():
            message += f"\n{rdvs.count()} rendez-vous:"
            for rdv in rdvs[:5]:
                message += f"\n- {rdv.heure_debut.strftime('%H:%M')}: {rdv.titre}"
        else:
            message += "\nAucun rendez-vous."

        if taches.exists():
            message += f"\n\n{taches.count()} taches:"
            for tache in taches[:5]:
                message += f"\n- {tache.titre}"
        else:
            message += "\nAucune tache en cours."

        return {
            'success': True,
            'message': message,
            'data': {
                'rdvs': rdvs.count(),
                'taches': taches.count()
            }
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Erreur: {str(e)}",
            'data': {}
        }


def rechercher_dossier(terme, utilisateur):
    """Recherche un dossier."""
    try:
        from gestion.models import Dossier
        from django.db.models import Q

        dossiers = Dossier.objects.filter(
            Q(reference__icontains=terme) |
            Q(debiteur__nom__icontains=terme) |
            Q(creancier__nom__icontains=terme)
        )[:10]

        if not dossiers.exists():
            return {
                'success': True,
                'message': f"Aucun dossier trouve pour '{terme}'.",
                'data': {'resultats': []}
            }

        message = f"Resultats pour '{terme}':"
        for d in dossiers:
            message += f"\n- {d.reference}: {d.debiteur}"

        return {
            'success': True,
            'message': message,
            'data': {'resultats': [d.reference for d in dossiers]}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Erreur: {str(e)}",
            'data': {}
        }
