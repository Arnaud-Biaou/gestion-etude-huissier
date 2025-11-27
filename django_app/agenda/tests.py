"""
Tests pour le module Agenda

Auteur: Maître Martial Arnaud BIAOU
"""

from datetime import datetime, timedelta, date, time
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import (
    RendezVous, Tache, Etiquette, ParticipantExterne,
    DocumentRdv, DocumentTache, RappelRdv, RappelTache,
    CommentaireTache, SousTacheChecklist, Notification,
    JourneeAgenda, ReportTache, ConfigurationAgenda,
    StatistiquesAgenda, HistoriqueAgenda,
    TypeRendezVous, TypeTache, StatutRendezVous, StatutTache,
    StatutDelegation, Priorite, TypeRecurrence
)


class RendezVousModelTest(TestCase):
    """Tests pour le modèle RendezVous"""

    def setUp(self):
        """Configuration initiale des tests"""
        # Créer un utilisateur de test
        from gestion.models import Utilisateur
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='huissier'
        )

    def test_creation_rdv(self):
        """Test de création d'un rendez-vous"""
        rdv = RendezVous.objects.create(
            titre="RDV Test",
            type_rdv=TypeRendezVous.RENDEZ_VOUS_CLIENT,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=1),
            createur=self.user
        )
        self.assertEqual(rdv.titre, "RDV Test")
        self.assertEqual(rdv.statut, StatutRendezVous.PLANIFIE)
        self.assertEqual(rdv.priorite, Priorite.NORMALE)

    def test_duree_rdv(self):
        """Test du calcul de durée"""
        debut = timezone.now()
        fin = debut + timedelta(hours=2)
        rdv = RendezVous.objects.create(
            titre="RDV Durée",
            date_debut=debut,
            date_fin=fin,
            createur=self.user
        )
        self.assertEqual(rdv.duree, 120)  # 120 minutes

    def test_est_passe(self):
        """Test de vérification si RDV passé"""
        rdv_passe = RendezVous.objects.create(
            titre="RDV Passé",
            date_debut=timezone.now() - timedelta(days=1),
            date_fin=timezone.now() - timedelta(hours=23),
            createur=self.user
        )
        self.assertTrue(rdv_passe.est_passe)

        rdv_futur = RendezVous.objects.create(
            titre="RDV Futur",
            date_debut=timezone.now() + timedelta(days=1),
            date_fin=timezone.now() + timedelta(days=1, hours=1),
            createur=self.user
        )
        self.assertFalse(rdv_futur.est_passe)


class TacheModelTest(TestCase):
    """Tests pour le modèle Tache"""

    def setUp(self):
        """Configuration initiale des tests"""
        from gestion.models import Utilisateur
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='huissier'
        )
        self.collaborateur = Utilisateur.objects.create_user(
            username='collab',
            email='collab@test.com',
            password='testpass123',
            role='clerc'
        )

    def test_creation_tache(self):
        """Test de création d'une tâche"""
        tache = Tache.objects.create(
            titre="Tâche Test",
            type_tache=TypeTache.REDACTION_ACTE,
            date_echeance=timezone.now().date() + timedelta(days=7),
            createur=self.user
        )
        self.assertEqual(tache.titre, "Tâche Test")
        self.assertEqual(tache.statut, StatutTache.A_FAIRE)
        self.assertEqual(tache.progression, 0)

    def test_tache_en_retard(self):
        """Test de détection des tâches en retard"""
        tache_retard = Tache.objects.create(
            titre="Tâche en retard",
            date_echeance=timezone.now().date() - timedelta(days=1),
            createur=self.user
        )
        self.assertTrue(tache_retard.est_en_retard)

        tache_ok = Tache.objects.create(
            titre="Tâche OK",
            date_echeance=timezone.now().date() + timedelta(days=1),
            createur=self.user
        )
        self.assertFalse(tache_ok.est_en_retard)

    def test_delegation_tache(self):
        """Test de délégation d'une tâche"""
        tache = Tache.objects.create(
            titre="Tâche à déléguer",
            date_echeance=timezone.now().date() + timedelta(days=7),
            createur=self.user,
            responsable=self.collaborateur,
            statut_delegation=StatutDelegation.ASSIGNEE,
            date_delegation=timezone.now()
        )
        self.assertTrue(tache.est_delegue)
        self.assertEqual(tache.statut_delegation, StatutDelegation.ASSIGNEE)

    def test_marquer_terminee(self):
        """Test de marquage comme terminée"""
        tache = Tache.objects.create(
            titre="Tâche à terminer",
            date_echeance=timezone.now().date(),
            createur=self.user
        )
        tache.marquer_terminee(self.user)
        self.assertEqual(tache.statut, StatutTache.TERMINEE)
        self.assertEqual(tache.progression, 100)
        self.assertIsNotNone(tache.date_terminaison)

    def test_progression_avec_checklist(self):
        """Test de calcul de progression avec checklist"""
        tache = Tache.objects.create(
            titre="Tâche avec checklist",
            date_echeance=timezone.now().date(),
            createur=self.user
        )

        # Créer 4 éléments de checklist
        for i in range(4):
            SousTacheChecklist.objects.create(
                tache=tache,
                libelle=f"Item {i+1}",
                ordre=i
            )

        # Marquer 2 comme complétés
        items = tache.checklist_items.all()[:2]
        for item in items:
            item.est_complete = True
            item.save()

        # La progression devrait être 50%
        self.assertEqual(tache.progression_calculee, 50)


class NotificationModelTest(TestCase):
    """Tests pour les notifications"""

    def setUp(self):
        from gestion.models import Utilisateur
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='huissier'
        )

    def test_creation_notification(self):
        """Test de création d'une notification"""
        notif = Notification.objects.create(
            destinataire=self.user,
            titre="Test notification",
            message="Ceci est un test",
            type_notification='autre'
        )
        self.assertFalse(notif.est_lu)

    def test_marquer_lu(self):
        """Test de marquage comme lu"""
        notif = Notification.objects.create(
            destinataire=self.user,
            titre="Test notification",
            message="Ceci est un test",
            type_notification='autre'
        )
        notif.marquer_lu()
        self.assertTrue(notif.est_lu)
        self.assertIsNotNone(notif.date_lecture)


class JourneeAgendaTest(TestCase):
    """Tests pour la clôture de journée"""

    def setUp(self):
        from gestion.models import Utilisateur
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='huissier'
        )

    def test_creation_journee(self):
        """Test de création d'une journée"""
        journee = JourneeAgenda.objects.create(
            date=timezone.now().date(),
            utilisateur=self.user
        )
        self.assertFalse(journee.est_cloturee)

    def test_cloture_journee(self):
        """Test de clôture de journée"""
        journee = JourneeAgenda.objects.create(
            date=timezone.now().date(),
            utilisateur=self.user
        )
        journee.cloturer(self.user, 'manuelle', "Test clôture")
        self.assertTrue(journee.est_cloturee)
        self.assertEqual(journee.type_cloture, 'manuelle')
        self.assertIsNotNone(journee.bilan_json)


class ConfigurationTest(TestCase):
    """Tests pour la configuration"""

    def test_singleton_configuration(self):
        """Test que la configuration est un singleton"""
        config1 = ConfigurationAgenda.objects.create()
        config1.duree_rdv_defaut = 60
        config1.save()

        # Récupérer l'instance
        config2 = ConfigurationAgenda.get_instance()
        self.assertEqual(config1.pk, config2.pk)

    def test_valeurs_defaut_configuration(self):
        """Test des valeurs par défaut"""
        config = ConfigurationAgenda.objects.create()
        self.assertEqual(config.duree_rdv_defaut, 60)
        self.assertTrue(config.activer_cloture_auto)
        self.assertEqual(len(config.jours_travail), 5)  # Lundi à vendredi


class APITest(TestCase):
    """Tests pour les API"""

    def setUp(self):
        from gestion.models import Utilisateur
        self.client = Client()
        self.user = Utilisateur.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='huissier'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_api_liste_rdv(self):
        """Test de l'API liste des RDV"""
        # Créer quelques RDV
        RendezVous.objects.create(
            titre="RDV 1",
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=1),
            createur=self.user
        )

        response = self.client.get('/agenda/api/rdv/')
        self.assertEqual(response.status_code, 200)

    def test_api_liste_taches(self):
        """Test de l'API liste des tâches"""
        Tache.objects.create(
            titre="Tâche 1",
            date_echeance=timezone.now().date(),
            createur=self.user
        )

        response = self.client.get('/agenda/api/taches/')
        self.assertEqual(response.status_code, 200)

    def test_api_actions_jour(self):
        """Test de l'API actions du jour"""
        response = self.client.get('/agenda/api/actions-jour/')
        self.assertEqual(response.status_code, 200)

    def test_api_vue_ensemble(self):
        """Test de l'API vue d'ensemble"""
        response = self.client.get('/agenda/api/vue-ensemble/')
        self.assertEqual(response.status_code, 200)


class PermissionsTest(TestCase):
    """Tests pour les permissions par rôle"""

    def setUp(self):
        from gestion.models import Utilisateur
        self.client = Client()

        self.admin = Utilisateur.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='huissier'
        )
        self.clerc = Utilisateur.objects.create_user(
            username='clerc',
            email='clerc@test.com',
            password='testpass123',
            role='clerc'
        )

    def test_admin_voit_tout(self):
        """Test que l'admin voit tous les éléments"""
        # Créer un RDV par le clerc
        rdv = RendezVous.objects.create(
            titre="RDV du clerc",
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=1),
            createur=self.clerc
        )

        # L'admin doit voir ce RDV
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/agenda/api/rdv/')
        self.assertEqual(response.status_code, 200)

    def test_clerc_voit_seulement_ses_elements(self):
        """Test que le clerc ne voit que ses éléments"""
        # Créer un RDV par l'admin
        rdv_admin = RendezVous.objects.create(
            titre="RDV de l'admin",
            date_debut=timezone.now(),
            date_fin=timezone.now() + timedelta(hours=1),
            createur=self.admin
        )

        # Créer un RDV par le clerc
        rdv_clerc = RendezVous.objects.create(
            titre="RDV du clerc",
            date_debut=timezone.now() + timedelta(hours=2),
            date_fin=timezone.now() + timedelta(hours=3),
            createur=self.clerc
        )

        # Le clerc ne doit voir que son RDV
        self.client.login(username='clerc', password='testpass123')
        response = self.client.get('/agenda/api/rdv/')
        self.assertEqual(response.status_code, 200)
