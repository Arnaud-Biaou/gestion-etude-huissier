"""
Tests unitaires pour valider les corrections PHASE 3
- Conformité légale Bénin/OHADA
- Décret 2017-066 (émoluments)
- Loi 2024-10 (majoration 50%)
- Taux UEMOA
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from gestion.models import Dossier, BasculementAmiableForce
from parametres.models import TauxLegal


class TestDossierValidations(TestCase):
    """Tests pour validations du modèle Dossier"""

    def setUp(self):
        """Setup données de test"""
        self.dossier = Dossier.objects.create(
            reference='TEST_0001_1125_MAB',
            type_dossier='recouvrement',
            montant_creance=Decimal('5000000'),
            date_creance=date(2024, 1, 1),
            statut='actif',
            phase='amiable'
        )

    def test_type_dossier_default(self):
        """Vérifier que type_dossier a une valeur par défaut"""
        d = Dossier(reference='TEST_DEFAULT')
        self.assertEqual(d.type_dossier, 'recouvrement')

    def test_type_dossier_choices(self):
        """Vérifier les choix valides pour type_dossier"""
        valid_choices = ['recouvrement', 'expulsion', 'constat', 'signification', 'saisie', 'autre']
        for choice in valid_choices:
            d = Dossier(reference=f'TEST_{choice}', type_dossier=choice)
            # Should not raise
            d.full_clean(exclude=['cree_par'])

    def test_montant_negatif_refuse(self):
        """Vérifier qu'un montant négatif est rejeté"""
        d = Dossier(
            reference='TEST_NEG',
            montant_creance=Decimal('-1000'),
            type_dossier='recouvrement'
        )
        with self.assertRaises(ValidationError) as context:
            d.full_clean()
        self.assertIn('montant_creance', str(context.exception))

    def test_montant_zero_accepte(self):
        """Vérifier qu'un montant zéro est accepté"""
        d = Dossier(
            reference='TEST_ZERO',
            montant_creance=Decimal('0'),
            type_dossier='recouvrement'
        )
        # Should not raise
        d.full_clean(exclude=['cree_par'])

    def test_montant_positif_accepte(self):
        """Vérifier qu'un montant positif est accepté"""
        d = Dossier(
            reference='TEST_POS',
            montant_creance=Decimal('1000000'),
            type_dossier='recouvrement'
        )
        # Should not raise
        d.full_clean(exclude=['cree_par'])


class TestStatutTransitions(TestCase):
    """Tests pour les transitions de statut"""

    def setUp(self):
        """Setup données de test"""
        self.dossier = Dossier.objects.create(
            reference='TEST_STATUT_001',
            type_dossier='recouvrement',
            montant_creance=Decimal('1000000'),
            statut='actif',
            phase='amiable'
        )

    def test_transition_actif_vers_urgent(self):
        """Transition valide: actif → urgent"""
        self.dossier.changer_statut('urgent')
        self.assertEqual(self.dossier.statut, 'urgent')

    def test_transition_actif_vers_archive(self):
        """Transition valide: actif → archive"""
        self.dossier.changer_statut('archive')
        self.assertEqual(self.dossier.statut, 'archive')

    def test_transition_actif_vers_cloture_avec_motif(self):
        """Transition valide: actif → cloture (avec motif)"""
        self.dossier.changer_statut('cloture', motif='Créance recouvrée')
        self.assertEqual(self.dossier.statut, 'cloture')

    def test_transition_cloture_vers_actif_interdite(self):
        """Transition invalide: cloture → actif"""
        self.dossier.statut = 'cloture'
        self.dossier.save()

        with self.assertRaises(ValueError) as context:
            self.dossier.changer_statut('actif')
        self.assertIn('Transition interdite', str(context.exception))

    def test_transition_cloture_sans_motif_refuse(self):
        """Clôture sans motif doit échouer"""
        with self.assertRaises(ValueError) as context:
            self.dossier.changer_statut('cloture', motif='')
        self.assertIn('motif est requis', str(context.exception))

    def test_meme_statut_no_op(self):
        """Transition vers le même statut = no-op"""
        self.dossier.changer_statut('actif')
        # Should not raise, should be a no-op
        self.assertEqual(self.dossier.statut, 'actif')


class TestEmolumentsDecret2017066(TestCase):
    """Tests pour la conformité au Décret 2017-066"""

    def test_emoluments_tranche_1(self):
        """Test émoluments 0-5M = 10%"""
        from recouvrement.services.baremes import calculer_emoluments_force

        montant = Decimal('5000000')
        emoluments = calculer_emoluments_force(montant)

        # 5M × 10% = 500K
        self.assertEqual(emoluments, Decimal('500000'))

    def test_emoluments_tranche_2(self):
        """Test émoluments 5M-20M = 3.5%"""
        from recouvrement.services.baremes import calculer_emoluments_force

        montant = Decimal('20000000')
        emoluments = calculer_emoluments_force(montant)

        # 5M × 10% + 15M × 3.5% = 500K + 525K = 1025K
        self.assertEqual(emoluments, Decimal('1025000'))

    def test_emoluments_15m(self):
        """Test émoluments pour 15M (cas documenté)"""
        from recouvrement.services.baremes import calculer_emoluments_force

        montant = Decimal('15000000')
        emoluments = calculer_emoluments_force(montant)

        # 5M × 10% + 10M × 3.5% = 500K + 350K = 850K
        self.assertEqual(emoluments, Decimal('850000'))

    def test_emoluments_conforme_pas_ancien_bareme(self):
        """Vérifier que les émoluments ne sont PAS l'ancien barème incorrect"""
        from recouvrement.services.baremes import calculer_emoluments_force

        montant = Decimal('15000000')
        emoluments = calculer_emoluments_force(montant)

        # Ancien barème donnait ~490K, nouveau donne ~850K
        self.assertGreater(emoluments, Decimal('800000'))
        self.assertLess(emoluments, Decimal('900000'))


class TestTauxUEMOA(TestCase):
    """Tests pour les taux légaux UEMOA"""

    @classmethod
    def setUpClass(cls):
        """Initialiser les taux légaux pour les tests"""
        super().setUpClass()
        # Créer quelques taux de test
        TauxLegal.objects.get_or_create(
            annee=2024,
            defaults={'taux': Decimal('5.0336')}
        )
        TauxLegal.objects.get_or_create(
            annee=2023,
            defaults={'taux': Decimal('4.2205')}
        )
        TauxLegal.objects.get_or_create(
            annee=2025,
            defaults={'taux': Decimal('5.5000')}
        )

    def test_taux_2024(self):
        """Vérifier le taux 2024"""
        taux = TauxLegal.get_taux_annee(2024)
        self.assertEqual(taux, Decimal('5.0336'))

    def test_taux_2023(self):
        """Vérifier le taux 2023"""
        taux = TauxLegal.get_taux_annee(2023)
        self.assertEqual(taux, Decimal('4.2205'))

    def test_taux_annee_inconnue_fallback(self):
        """Taux pour année inconnue = dernier taux connu"""
        taux = TauxLegal.get_taux_annee(2030)
        # Doit retourner un taux (pas None)
        self.assertIsNotNone(taux)


class TestCalculInteretsMajoration(TestCase):
    """Tests pour le calcul des intérêts avec majoration 50%"""

    @classmethod
    def setUpClass(cls):
        """Initialiser les taux légaux pour les tests"""
        super().setUpClass()
        TauxLegal.objects.get_or_create(
            annee=2024,
            defaults={'taux': Decimal('5.0336')}
        )

    def test_calcul_sans_majoration(self):
        """Calcul sans date d'exécutorité = pas de majoration"""
        from recouvrement.services.calcul_interets import CalculateurInteretsOHADA

        calc = CalculateurInteretsOHADA()
        result = calc.calculer_avec_majoration(
            principal=Decimal('1000000'),
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 12, 31),
            date_decision_executoire=None
        )

        # Sans majoration, interets_majores = 0
        self.assertEqual(result['interets_majores'], Decimal('0'))
        self.assertGreater(result['total'], Decimal('0'))

    def test_calcul_avec_majoration(self):
        """Calcul avec majoration après 2 mois"""
        from recouvrement.services.calcul_interets import CalculateurInteretsOHADA

        calc = CalculateurInteretsOHADA()

        # Date d'exécutorité il y a 4 mois
        date_exec = date(2024, 1, 1)
        date_fin = date(2024, 6, 1)  # 5 mois après

        result = calc.calculer_avec_majoration(
            principal=Decimal('1000000'),
            date_debut=date(2024, 1, 1),
            date_fin=date_fin,
            date_decision_executoire=date_exec
        )

        # Avec majoration, interets_majores > 0
        self.assertGreater(result['interets_majores'], Decimal('0'))

    def test_majoration_coefficient_1_5(self):
        """Vérifier que la majoration est bien de 50% (×1.5)"""
        from recouvrement.services.calcul_interets import CalculateurInteretsOHADA

        calc = CalculateurInteretsOHADA()

        # Période entièrement après le délai de 2 mois
        date_exec = date(2024, 1, 1)
        date_debut_majore = date(2024, 3, 3)  # > 60 jours après
        date_fin = date(2024, 4, 3)  # 1 mois de période majorée

        # Calcul normal (sans majoration)
        result_normal = calc.calculer_interets_multi_annees(
            principal=Decimal('1000000'),
            date_debut=date_debut_majore,
            date_fin=date_fin
        )

        # Calcul avec majoration
        result_majore = calc.calculer_avec_majoration(
            principal=Decimal('1000000'),
            date_debut=date_debut_majore,
            date_fin=date_fin,
            date_decision_executoire=date_exec
        )

        # interets_majores ≈ total_normal × 1.5
        expected = (result_normal['total'] * Decimal('1.5')).quantize(Decimal('1'))
        self.assertEqual(result_majore['interets_majores'], expected)


class TestDateExecutoire(TestCase):
    """Tests pour le champ date_executoire"""

    def test_date_executoire_field_exists(self):
        """Vérifier que le champ date_executoire existe"""
        d = Dossier()
        self.assertTrue(hasattr(d, 'date_executoire'))

    def test_date_executoire_nullable(self):
        """Vérifier que date_executoire peut être null"""
        d = Dossier.objects.create(
            reference='TEST_DATE_EXEC',
            type_dossier='recouvrement',
            date_executoire=None
        )
        self.assertIsNone(d.date_executoire)

    def test_date_executoire_set(self):
        """Vérifier qu'on peut définir date_executoire"""
        d = Dossier.objects.create(
            reference='TEST_DATE_EXEC_SET',
            type_dossier='recouvrement',
            date_executoire=date(2024, 3, 15)
        )
        self.assertEqual(d.date_executoire, date(2024, 3, 15))


class TestTypeTitreExecutoire(TestCase):
    """Tests pour le champ titre_executoire_type avec choices"""

    def test_choices_exist(self):
        """Vérifier que TYPE_TITRE_EXECUTOIRE_CHOICES existe"""
        self.assertTrue(hasattr(Dossier, 'TYPE_TITRE_EXECUTOIRE_CHOICES'))

    def test_choices_count(self):
        """Vérifier qu'il y a 6 types de titres"""
        self.assertEqual(len(Dossier.TYPE_TITRE_EXECUTOIRE_CHOICES), 6)

    def test_valid_choices(self):
        """Vérifier les choix valides"""
        valid_types = ['jugement', 'ordonnance', 'acte_notarie', 'pv_conciliation', 'protet', 'autre']
        choices_values = [c[0] for c in Dossier.TYPE_TITRE_EXECUTOIRE_CHOICES]

        for t in valid_types:
            self.assertIn(t, choices_values)

    def test_titre_type_set(self):
        """Vérifier qu'on peut définir un type de titre"""
        d = Dossier.objects.create(
            reference='TEST_TITRE_TYPE',
            type_dossier='recouvrement',
            titre_executoire_type='jugement'
        )
        self.assertEqual(d.titre_executoire_type, 'jugement')
