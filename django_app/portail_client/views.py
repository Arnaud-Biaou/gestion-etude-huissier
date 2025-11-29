"""
Vues pour le Portail Client
Landing page publique, authentification et espace client sécurisé
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.utils import timezone
from django.db import models
from functools import wraps

from .models import (
    ClientPortail,
    AccesDocument,
    MessagePortail,
    NotificationClient,
    DemandeContact
)


def landing_page(request):
    """Page d'accueil publique du portail"""
    from parametres.models import ConfigurationEtude

    try:
        config = ConfigurationEtude.get_instance()
    except Exception:
        config = None

    return render(request, 'portail_client/landing.html', {
        'config': config,
        'current_year': timezone.now().year,
    })


def portail_connexion(request):
    """Page de connexion client"""
    # Si déjà connecté, rediriger vers le tableau de bord
    if request.session.get('client_id'):
        return redirect('portail_tableau_bord')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        mot_de_passe = request.POST.get('mot_de_passe', '')

        try:
            client = ClientPortail.objects.get(email=email, est_actif=True)

            if client.compte_bloque:
                messages.error(
                    request,
                    "Votre compte est bloqué suite à plusieurs tentatives infructueuses. "
                    "Veuillez contacter l'étude."
                )
                return render(request, 'portail_client/connexion.html')

            if client.check_password(mot_de_passe):
                # Connexion réussie
                request.session['client_id'] = client.id
                client.date_derniere_connexion = timezone.now()
                client.tentatives_connexion = 0
                client.save()
                messages.success(request, f"Bienvenue, {client.nom_complet} !")
                return redirect('portail_tableau_bord')
            else:
                # Mot de passe incorrect
                client.tentatives_connexion += 1
                if client.tentatives_connexion >= 5:
                    client.compte_bloque = True
                    messages.error(
                        request,
                        "Compte bloqué suite à 5 tentatives infructueuses. "
                        "Veuillez contacter l'étude."
                    )
                else:
                    messages.error(request, "Email ou mot de passe incorrect.")
                client.save()

        except ClientPortail.DoesNotExist:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'portail_client/connexion.html')


def portail_deconnexion(request):
    """Déconnexion client"""
    if 'client_id' in request.session:
        del request.session['client_id']
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('landing_page')


def client_requis(view_func):
    """Décorateur pour vérifier l'authentification client"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        client_id = request.session.get('client_id')
        if not client_id:
            messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('portail_connexion')
        try:
            request.client = ClientPortail.objects.get(id=client_id, est_actif=True)
            if request.client.compte_bloque:
                del request.session['client_id']
                messages.error(request, "Votre compte est bloqué. Contactez l'étude.")
                return redirect('portail_connexion')
        except ClientPortail.DoesNotExist:
            del request.session['client_id']
            messages.error(request, "Session expirée. Veuillez vous reconnecter.")
            return redirect('portail_connexion')
        return view_func(request, *args, **kwargs)
    return wrapper


@client_requis
def portail_tableau_bord(request):
    """Tableau de bord client"""
    client = request.client

    # Récupérer les dossiers liés au client
    dossiers = []
    if client.partie:
        from gestion.models import Dossier
        dossiers = Dossier.objects.filter(
            models.Q(demandeurs=client.partie) | models.Q(defendeurs=client.partie)
        ).distinct().order_by('-date_ouverture')[:5]

    # Documents récents
    documents = client.documents_accessibles.all()[:5]

    # Notifications non lues
    notifications = client.notifications.filter(lu=False)[:5]
    notifications_count = client.notifications.filter(lu=False).count()

    # Messages non lus
    messages_non_lus = client.messages.filter(lu=False, est_de_client=False).count()

    return render(request, 'portail_client/tableau_bord.html', {
        'client': client,
        'dossiers': dossiers,
        'documents': documents,
        'notifications': notifications,
        'notifications_count': notifications_count,
        'messages_non_lus': messages_non_lus,
    })


@client_requis
def portail_mes_dossiers(request):
    """Liste des dossiers du client"""
    client = request.client
    dossiers = []

    if client.partie:
        from gestion.models import Dossier
        dossiers = Dossier.objects.filter(
            models.Q(demandeurs=client.partie) | models.Q(defendeurs=client.partie)
        ).distinct().order_by('-date_ouverture')

    return render(request, 'portail_client/mes_dossiers.html', {
        'client': client,
        'dossiers': dossiers,
    })


@client_requis
def portail_dossier_detail(request, dossier_id):
    """Détail d'un dossier"""
    client = request.client
    from gestion.models import Dossier

    # Vérifier que le client a accès à ce dossier
    dossier = get_object_or_404(Dossier, id=dossier_id)

    # Vérifier l'accès
    if client.partie:
        has_access = (
            dossier.demandeurs.filter(id=client.partie.id).exists() or
            dossier.defendeurs.filter(id=client.partie.id).exists()
        )
        if not has_access:
            messages.error(request, "Vous n'avez pas accès à ce dossier.")
            return redirect('portail_mes_dossiers')

    # Documents liés à ce dossier
    documents = client.documents_accessibles.filter(dossier=dossier)

    return render(request, 'portail_client/dossier_detail.html', {
        'client': client,
        'dossier': dossier,
        'documents': documents,
    })


@client_requis
def portail_mes_documents(request):
    """Documents accessibles au client"""
    client = request.client
    documents = client.documents_accessibles.all()

    # Filtres
    type_doc = request.GET.get('type')
    if type_doc:
        documents = documents.filter(type_document=type_doc)

    return render(request, 'portail_client/mes_documents.html', {
        'client': client,
        'documents': documents,
        'type_filter': type_doc,
    })


@client_requis
def portail_telecharger_document(request, doc_id):
    """Télécharger un document"""
    client = request.client
    document = get_object_or_404(AccesDocument, id=doc_id, client=client)

    # Vérifier paiement si requis
    if document.paiement_requis and not document.est_paye:
        messages.error(
            request,
            f"Ce document nécessite un paiement de {document.montant_requis:,.0f} FCFA. "
            "Veuillez régler avant de télécharger."
        )
        return redirect('portail_mes_documents')

    # Mettre à jour les statistiques
    if not document.date_premier_telechargement:
        document.date_premier_telechargement = timezone.now()
    document.nombre_telechargements += 1
    document.save()

    # Retourner le fichier
    return FileResponse(
        document.fichier.open('rb'),
        as_attachment=True,
        filename=document.fichier.name.split('/')[-1]
    )


@client_requis
def portail_mes_messages(request):
    """Messagerie client"""
    client = request.client
    conversations = client.messages.all()

    # Marquer les messages reçus comme lus
    client.messages.filter(lu=False, est_de_client=False).update(
        lu=True,
        date_lecture=timezone.now()
    )

    return render(request, 'portail_client/mes_messages.html', {
        'client': client,
        'conversations': conversations,
    })


@client_requis
@require_POST
def portail_envoyer_message(request):
    """Envoyer un message à l'étude"""
    client = request.client

    sujet = request.POST.get('sujet', '').strip()
    contenu = request.POST.get('contenu', '').strip()
    dossier_id = request.POST.get('dossier_id')

    if not sujet or not contenu:
        messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        return redirect('portail_mes_messages')

    message_obj = MessagePortail(
        client=client,
        sujet=sujet,
        contenu=contenu,
        est_de_client=True,
    )

    if dossier_id:
        from gestion.models import Dossier
        try:
            dossier = Dossier.objects.get(id=dossier_id)
            message_obj.dossier = dossier
        except Dossier.DoesNotExist:
            pass

    # Gérer la pièce jointe
    if 'piece_jointe' in request.FILES:
        message_obj.piece_jointe = request.FILES['piece_jointe']

    message_obj.save()

    # Créer une notification pour l'étude (optionnel)
    messages.success(request, "Votre message a été envoyé avec succès.")
    return redirect('portail_mes_messages')


@client_requis
def portail_notifications(request):
    """Liste des notifications"""
    client = request.client
    notifications = client.notifications.all()

    return render(request, 'portail_client/notifications.html', {
        'client': client,
        'notifications': notifications,
    })


@client_requis
@require_POST
def portail_marquer_notification_lue(request, notif_id):
    """Marquer une notification comme lue"""
    client = request.client
    notification = get_object_or_404(NotificationClient, id=notif_id, client=client)
    notification.lu = True
    notification.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    # Rediriger vers le lien si présent
    if notification.lien:
        return redirect(notification.lien)
    return redirect('portail_notifications')


@client_requis
def portail_mon_profil(request):
    """Profil du client"""
    client = request.client

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            telephone = request.POST.get('telephone', '').strip()
            if telephone:
                client.telephone = telephone
                client.save()
                messages.success(request, "Profil mis à jour avec succès.")

        elif action == 'change_password':
            ancien_mdp = request.POST.get('ancien_mot_de_passe')
            nouveau_mdp = request.POST.get('nouveau_mot_de_passe')
            confirm_mdp = request.POST.get('confirmer_mot_de_passe')

            if not client.check_password(ancien_mdp):
                messages.error(request, "L'ancien mot de passe est incorrect.")
            elif nouveau_mdp != confirm_mdp:
                messages.error(request, "Les mots de passe ne correspondent pas.")
            elif len(nouveau_mdp) < 8:
                messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            else:
                client.set_password(nouveau_mdp)
                client.save()
                messages.success(request, "Mot de passe modifié avec succès.")

        return redirect('portail_mon_profil')

    return render(request, 'portail_client/mon_profil.html', {
        'client': client,
    })


def portail_contact(request):
    """Formulaire de contact public"""
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip().lower()
        telephone = request.POST.get('telephone', '').strip()
        message_content = request.POST.get('message', '').strip()

        if not nom or not email or not message_content:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('landing_page')

        # Enregistrer la demande de contact
        DemandeContact.objects.create(
            nom=nom,
            email=email,
            telephone=telephone,
            message=message_content
        )

        messages.success(
            request,
            "Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais."
        )
        return redirect('landing_page')

    return redirect('landing_page')


# API endpoints pour AJAX
@client_requis
@require_GET
def api_notifications_count(request):
    """Retourne le nombre de notifications non lues"""
    client = request.client
    count = client.notifications.filter(lu=False).count()
    return JsonResponse({'count': count})


@client_requis
@require_GET
def api_messages_count(request):
    """Retourne le nombre de messages non lus"""
    client = request.client
    count = client.messages.filter(lu=False, est_de_client=False).count()
    return JsonResponse({'count': count})
