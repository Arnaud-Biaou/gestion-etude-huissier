"""
Vues publiques pour la vérification des actes sécurisés.
Étude Me Martial Arnaud BIAOU - Huissier de Justice - Parakou
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from django.utils import timezone

from .models import ActeSecurise
from .services.qr_service import ActeSecuriseService


@require_GET
def verification_acte(request, code):
    """
    Page publique de vérification d'un acte.
    Accessible par scan du QR code - PAS DE LOGIN REQUIS.

    URL: /v/<code>/ ou /verification/<code>/
    """
    # Nettoyer le code (enlever espaces éventuels)
    code = code.strip().upper()

    # Vérifier l'acte
    est_valide, infos = ActeSecuriseService.verifier_acte(code)

    if est_valide:
        return render(request, 'gestion/verification/acte_valide.html', {
            'acte': infos,
            'code': code,
            'valide': True,
        })
    else:
        return render(request, 'gestion/verification/acte_invalide.html', {
            'code': code,
            'valide': False,
            'raison': infos.get('raison') if infos else None,
        })


@require_GET
def verification_acte_api(request, code):
    """
    API JSON de vérification d'un acte.
    Utile pour intégrations tierces.

    URL: /api/verification/<code>/
    """
    code = code.strip().upper()

    est_valide, infos = ActeSecuriseService.verifier_acte(code)

    if est_valide:
        return JsonResponse({
            'valide': True,
            'acte': {
                'code': infos['code'],
                'type': infos['type_acte'],
                'titre': infos['titre'],
                'date': infos['date_acte'].isoformat() if infos['date_acte'] else None,
                'parties': infos['parties'],
                'reference_dossier': infos['reference_dossier'],
                'verifications': infos['nombre_verifications'],
            },
            'emetteur': {
                'nom': 'Étude Me Martial Arnaud BIAOU',
                'qualite': 'Huissier de Justice',
                'juridiction': 'TPI et Cour d\'Appel de Parakou',
                'pays': 'Bénin',
            }
        })
    else:
        return JsonResponse({
            'valide': False,
            'code': code,
            'raison': infos.get('raison') if infos else 'Acte non trouvé',
            'message': 'Ce code de vérification n\'existe pas dans notre système.',
        }, status=404)


@require_GET
def verification_accueil(request):
    """
    Page d'accueil de vérification avec formulaire de saisie manuelle.
    Pour les cas où le QR ne peut pas être scanné.

    URL: /verification/
    """
    code = request.GET.get('code', '').strip().upper()

    if code:
        # Rediriger vers la vérification
        est_valide, infos = ActeSecuriseService.verifier_acte(code)

        if est_valide:
            return render(request, 'gestion/verification/acte_valide.html', {
                'acte': infos,
                'code': code,
                'valide': True,
            })
        else:
            return render(request, 'gestion/verification/acte_invalide.html', {
                'code': code,
                'valide': False,
                'raison': infos.get('raison') if infos else None,
            })

    # Afficher le formulaire
    return render(request, 'gestion/verification/accueil.html')
