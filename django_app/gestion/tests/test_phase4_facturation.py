"""
Tests unitaires pour PHASE 4 - Facturation E-MECeF
- GroupeTaxation (A/B)
- ActeDossier
- VentilationLigneFacture
- LigneFacture calculs
- Facture TVA/TPS
- AIB Entreprise/Particulier
- Cascade calculs
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from gestion.models import (
    Dossier, Utilisateur, ActeDossier,
    Creancier, GroupeTaxation, LigneFacture,
    VentilationLigneFacture, Facture, CreanceAIB
)


class TestPhase4Setup(TestCase):
    """Setup initial pour tous les tests Phase 4"""

    @classmethod
    def setUpTestData(cls):
        """Créer données communes"""
        cls.user = Utilisateur.objects.create(
            username='huissier_test',
            email='huissier@test.bj',
            nom='Test',
            prenom='Huissier'
        )
        cls.user.set_password('test1234')
        cls.user.save()

        # GroupeTaxation créés par migration
        cls.groupe_a = GroupeTaxation.objects.get(code='A')
        cls.groupe_b = GroupeTaxation.objects.get(code='B')

        cls.creancier = Creancier.objects.create(
            code='CRED-TEST-001',
            nom='Creancier Test SARL',
            type_creancier='entreprise'
        )


class TestGroupeTaxation(TestPhase4Setup):
    """Tests du référentiel GroupeTaxation (E-MECeF)"""

    def test_groupe_a_existe(self):
        """GroupeTaxation A existe avec taux 0%"""
        self.assertEqual(self.groupe_a.code, 'A')
        self.assertEqual(self.groupe_a.taux_tva, Decimal('0.00'))
        self.assertFalse(self.groupe_a.taxable)

    def test_groupe_b_existe(self):
        """GroupeTaxation B existe avec taux 18%"""
        self.assertEqual(self.groupe_b.code, 'B')
        self.assertEqual(self.groupe_b.taux_tva, Decimal('18.00'))
        self.assertTrue(self.groupe_b.taxable)

    def test_groupe_a_str(self):
        """Test __str__ GroupeTaxation A"""
        self.assertIn('A', str(self.groupe_a))


class TestActeDossier(TestPhase4Setup):
    """Tests création ActeDossier"""

    def setUp(self):
        self.dossier = Dossier.objects.create(
            reference='DOS-TEST-001',
            type_dossier='recouvrement',
            montant_creance=Decimal('100000'),
            cree_par=self.user
        )

    def test_creer_acte_dossier(self):
        """Créer un ActeDossier"""
        acte = ActeDossier.objects.create(
            dossier=self.dossier,
            numero_acte='EXE-2025-001',
            date_acte=timezone.now().date(),
            type_acte='signification',
            nombre_feuillets=20,
            cree_par=self.user
        )
        self.assertEqual(acte.numero_acte, 'EXE-2025-001')
        self.assertEqual(acte.nombre_feuillets, 20)

    def test_acte_calcul_timbres(self):
        """Nombre feuillets pour calcul timbres (1.200 FCFA/feuillet)"""
        acte = ActeDossier.objects.create(
            dossier=self.dossier,
            numero_acte='EXE-2025-002',
            date_acte=timezone.now().date(),
            nombre_feuillets=15,
            cree_par=self.user
        )
        montant_timbres = acte.get_montant_timbres()
        self.assertEqual(montant_timbres, 18000)

    def test_acte_generer_numero(self):
        """Générer numéro d'acte unique"""
        numero = ActeDossier.generer_numero()
        self.assertTrue(numero.startswith('EXE-'))

    def test_acte_str(self):
        """Test __str__ ActeDossier"""
        acte = ActeDossier.objects.create(
            dossier=self.dossier,
            numero_acte='EXE-2025-003',
            date_acte=timezone.now().date(),
            cree_par=self.user
        )
        self.assertIn('EXE-2025-003', str(acte))


class TestVentilationLigneFacture(TestPhase4Setup):
    """Tests ventilation Groupe A vs B"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-001',
            client='Client Test',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )
        self.ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification',
            ordre=1
        )

    def test_ventilation_timbre_groupe_a(self):
        """Ventilation Timbre - Groupe A (0% TVA)"""
        vent = VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='timbre',
            groupe_taxation=self.groupe_a,
            description='Timbres (20 feuillets)',
            montant_ht=Decimal('24000'),
            ordre=1
        )
        self.assertEqual(vent.montant_tva, Decimal('0'))
        self.assertEqual(vent.montant_ttc, Decimal('24000'))

    def test_ventilation_enregistrement_groupe_a(self):
        """Ventilation Enregistrement - Groupe A (0% TVA)"""
        vent = VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='enregistrement',
            groupe_taxation=self.groupe_a,
            description='Enregistrement de l\'acte',
            montant_ht=Decimal('2500'),
            ordre=2
        )
        self.assertEqual(vent.montant_tva, Decimal('0'))
        self.assertEqual(vent.montant_ttc, Decimal('2500'))

    def test_ventilation_honoraires_groupe_b(self):
        """Ventilation Honoraires - Groupe B (18% TVA)"""
        vent = VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='honoraires',
            groupe_taxation=self.groupe_b,
            description='Honoraires signification',
            montant_ht=Decimal('35000'),
            ordre=3
        )
        # TVA = 18% × 35000 = 6300
        self.assertEqual(vent.montant_tva, Decimal('6300'))
        self.assertEqual(vent.montant_ttc, Decimal('41300'))

    def test_ventilation_frais_greffe_groupe_a(self):
        """Ventilation Frais greffe - Groupe A (0% TVA)"""
        vent = VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='frais_greffe',
            groupe_taxation=self.groupe_a,
            description='Frais de greffe',
            montant_ht=Decimal('5000'),
            ordre=4
        )
        self.assertEqual(vent.montant_tva, Decimal('0'))
        self.assertEqual(vent.montant_ttc, Decimal('5000'))

    def test_ventilation_str(self):
        """Test __str__ VentilationLigneFacture"""
        vent = VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='honoraires',
            groupe_taxation=self.groupe_b,
            description='Honoraires',
            montant_ht=Decimal('10000'),
            ordre=1
        )
        self.assertIn('Honoraires', str(vent))


class TestLigneFactureCalculs(TestPhase4Setup):
    """Tests calculs LigneFacture avec ventilations mixtes"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-002',
            client='Client Test',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )
        self.ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification complète',
            ordre=1
        )

    def test_ligne_ventilations_mixtes(self):
        """Ligne avec ventilations Groupe A + B"""

        # Timbres (Groupe A) = 24000
        VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='timbre',
            groupe_taxation=self.groupe_a,
            description='Timbres (20×1.200)',
            montant_ht=Decimal('24000'),
            ordre=1
        )

        # Enregistrement (Groupe A) = 2500
        VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='enregistrement',
            groupe_taxation=self.groupe_a,
            description='Enregistrement',
            montant_ht=Decimal('2500'),
            ordre=2
        )

        # Honoraires (Groupe B) = 35000
        VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='honoraires',
            groupe_taxation=self.groupe_b,
            description='Honoraires signification',
            montant_ht=Decimal('35000'),
            ordre=3
        )

        # Frais greffe (Groupe A) = 5000
        VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='frais_greffe',
            groupe_taxation=self.groupe_a,
            description='Frais greffe',
            montant_ht=Decimal('5000'),
            ordre=4
        )

        # Recalculer
        self.ligne.refresh_from_db()

        # Vérifications
        # Groupe A = 24000 + 2500 + 5000 = 31500
        self.assertEqual(self.ligne.montant_ht_groupe_a, Decimal('31500'))
        # Groupe B = 35000
        self.assertEqual(self.ligne.montant_ht_groupe_b, Decimal('35000'))
        # Total HT = 66500
        self.assertEqual(self.ligne.montant_total_ht, Decimal('66500'))
        # TVA = 18% × 35000 = 6300
        self.assertEqual(self.ligne.montant_tva_groupe_b, Decimal('6300'))
        # Total TTC = 72800
        self.assertEqual(self.ligne.montant_total_ttc, Decimal('72800'))

    def test_ligne_str(self):
        """Test __str__ LigneFacture"""
        self.assertIn('Signification', str(self.ligne))

    def test_ligne_total_property(self):
        """Test propriété total (compatibilité)"""
        VentilationLigneFacture.objects.create(
            ligne_facture=self.ligne,
            nature='honoraires',
            groupe_taxation=self.groupe_b,
            description='Honoraires',
            montant_ht=Decimal('10000'),
            ordre=1
        )
        self.ligne.refresh_from_db()
        self.assertEqual(self.ligne.total, self.ligne.montant_total_ttc)


class TestFactureRegimeTVA(TestPhase4Setup):
    """Tests Facture en régime TVA (18% sur Groupe B)"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-003',
            client='Client Entreprise TVA',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )

    def test_facture_tva_calcul_correct(self):
        """Facture TVA : TVA = 18% sur Groupe B uniquement"""

        ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification',
            ordre=1
        )

        # Groupe A = 26500
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='timbre', groupe_taxation=self.groupe_a,
            description='Timbres', montant_ht=Decimal('24000'), ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='enregistrement', groupe_taxation=self.groupe_a,
            description='Enregistrement', montant_ht=Decimal('2500'), ordre=2
        )

        # Groupe B = 35000
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=3
        )

        # Refresh
        self.facture.refresh_from_db()

        # Vérifications
        self.assertEqual(self.facture.montant_ht_groupe_a, Decimal('26500'))
        self.assertEqual(self.facture.montant_ht_groupe_b, Decimal('35000'))
        self.assertEqual(self.facture.montant_total_ht, Decimal('61500'))
        # TVA = 18% × 35000 = 6300
        self.assertEqual(self.facture.montant_tva_tps, Decimal('6300'))
        self.assertEqual(self.facture.montant_total_ttc, Decimal('67800'))

    def test_facture_regime_tva_default(self):
        """Régime fiscal par défaut = TVA"""
        f = Facture(numero='TEST', client='Test', montant_ht=0, montant_tva=0, montant_ttc=0)
        self.assertEqual(f.regime_fiscal, 'TVA')


class TestFactureRegimeTPS(TestPhase4Setup):
    """Tests Facture en régime TPS (3% sur total)"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-004',
            client='Client TPS',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TPS',
            prelevable_aib=True
        )

    def test_facture_tps_3_pourcent_total(self):
        """Facture TPS : TPS = 3% sur TOTAL HT (A + B)"""

        ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification',
            ordre=1
        )

        # Groupe A = 24000
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='timbre', groupe_taxation=self.groupe_a,
            description='Timbres', montant_ht=Decimal('24000'), ordre=1
        )

        # Groupe B = 35000
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=2
        )

        # Refresh
        self.facture.refresh_from_db()

        # Total HT = 59000
        self.assertEqual(self.facture.montant_total_ht, Decimal('59000'))

        # TPS = 3% × 59000 = 1770
        self.assertEqual(self.facture.montant_tva_tps, Decimal('1770'))

        # Total TTC = 60770
        self.assertEqual(self.facture.montant_total_ttc, Decimal('60770'))


class TestCreanceAIBEntreprise(TestPhase4Setup):
    """Tests AIB pour entreprise (prelevable_aib=True)"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-005',
            client='Entreprise Test',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )

    def test_aib_3_pourcent_groupe_b(self):
        """AIB = 3% sur Groupe B uniquement (entreprise)"""

        ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification',
            ordre=1
        )

        # Groupe A : 26500 (pas d'AIB)
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='timbre', groupe_taxation=self.groupe_a,
            description='Timbres', montant_ht=Decimal('24000'), ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='enregistrement', groupe_taxation=self.groupe_a,
            description='Enregistrement', montant_ht=Decimal('2500'), ordre=2
        )

        # Groupe B : 35000 (base AIB)
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=3
        )

        # Refresh et créer CreanceAIB
        self.facture.refresh_from_db()
        creance = CreanceAIB.creer_depuis_facture(self.facture)

        # AIB base = Groupe B = 35000
        self.assertEqual(creance.montant_base_aib, Decimal('35000'))
        # AIB = 3% × 35000 = 1050
        self.assertEqual(creance.montant_aib, Decimal('1050'))
        self.assertEqual(creance.client_type, 'entreprise')


class TestCreanceAIBParticulier(TestPhase4Setup):
    """Tests AIB = 0 pour particulier (prelevable_aib=False)"""

    def setUp(self):
        self.facture = Facture.objects.create(
            numero='FAC-2025-006',
            client='Particulier Test',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=False  # Particulier
        )

    def test_aib_zero_particulier(self):
        """AIB = 0 si client particulier"""

        ligne = LigneFacture.objects.create(
            facture=self.facture,
            numero_ligne=1,
            description='Signification',
            ordre=1
        )

        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=1
        )

        # Refresh et créer CreanceAIB
        self.facture.refresh_from_db()
        creance = CreanceAIB.creer_depuis_facture(self.facture)

        # AIB = 0 car particulier
        self.assertEqual(creance.montant_aib, Decimal('0'))
        self.assertEqual(creance.client_type, 'particulier')
        self.assertEqual(creance.statut, 'annule')


class TestCreanceAIBComparaison(TestPhase4Setup):
    """Tests AIB identique TVA vs TPS (base = Groupe B)"""

    def test_aib_identique_tva_vs_tps(self):
        """AIB = Groupe B que ce soit régime TVA ou TPS"""

        # Facture TVA
        fact_tva = Facture.objects.create(
            numero='FAC-2025-007',
            client='Entreprise TVA',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )

        ligne_tva = LigneFacture.objects.create(
            facture=fact_tva, numero_ligne=1, description='Signification', ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne_tva, nature='timbre', groupe_taxation=self.groupe_a,
            description='Timbres', montant_ht=Decimal('24000'), ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne_tva, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=2
        )

        fact_tva.refresh_from_db()
        creance_tva = CreanceAIB.creer_depuis_facture(fact_tva)

        # Facture TPS (mêmes montants)
        fact_tps = Facture.objects.create(
            numero='FAC-2025-008',
            client='Entreprise TPS',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TPS',
            prelevable_aib=True
        )

        ligne_tps = LigneFacture.objects.create(
            facture=fact_tps, numero_ligne=1, description='Signification', ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne_tps, nature='timbre', groupe_taxation=self.groupe_a,
            description='Timbres', montant_ht=Decimal('24000'), ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne_tps, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires', montant_ht=Decimal('35000'), ordre=2
        )

        fact_tps.refresh_from_db()
        creance_tps = CreanceAIB.creer_depuis_facture(fact_tps)

        # AIB identique (base = Groupe B = 35000)
        self.assertEqual(creance_tva.montant_aib, creance_tps.montant_aib)
        self.assertEqual(creance_tva.montant_aib, Decimal('1050'))


class TestCreanceAIBMethodes(TestPhase4Setup):
    """Tests méthodes CreanceAIB"""

    def test_creance_str(self):
        """Test __str__ CreanceAIB"""
        facture = Facture.objects.create(
            numero='FAC-2025-009',
            client='Test',
            montant_ht=Decimal('35000'),
            montant_tva=Decimal('6300'),
            montant_ttc=Decimal('41300'),
            montant_ht_groupe_b=Decimal('35000'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )
        creance = CreanceAIB.creer_depuis_facture(facture)
        self.assertIn('FAC-2025-009', str(creance))
        self.assertIn('entreprise', str(creance))


class TestFactureMethodes(TestPhase4Setup):
    """Tests méthodes Facture"""

    def test_facture_str(self):
        """Test __str__ Facture"""
        facture = Facture.objects.create(
            numero='FAC-2025-010',
            client='Client ABC',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0')
        )
        self.assertIn('FAC-2025-010', str(facture))
        self.assertIn('Client ABC', str(facture))

    def test_facture_prelevable_aib_default(self):
        """prelevable_aib = True par défaut"""
        f = Facture(numero='TEST', client='Test', montant_ht=0, montant_tva=0, montant_ttc=0)
        self.assertTrue(f.prelevable_aib)


class TestIntegrationComplete(TestPhase4Setup):
    """Tests intégration complète du workflow"""

    def test_workflow_signification_complete(self):
        """Workflow complet : Dossier → Acte → Facture → Ventilations → AIB"""

        # 1. Créer dossier
        dossier = Dossier.objects.create(
            reference='DOS-INTEG-001',
            type_dossier='recouvrement',
            montant_creance=Decimal('5000000'),
            cree_par=self.user
        )

        # 2. Créer acte
        acte = ActeDossier.objects.create(
            dossier=dossier,
            numero_acte='EXE-INTEG-001',
            date_acte=timezone.now().date(),
            type_acte='signification',
            nombre_feuillets=20,
            cree_par=self.user
        )

        # 3. Créer facture
        facture = Facture.objects.create(
            numero='FAC-INTEG-001',
            dossier=dossier,
            client='Client Intégration',
            montant_ht=Decimal('0'),
            montant_tva=Decimal('0'),
            montant_ttc=Decimal('0'),
            regime_fiscal='TVA',
            prelevable_aib=True
        )

        # 4. Créer ligne avec lien acte
        ligne = LigneFacture.objects.create(
            facture=facture,
            acte_dossier=acte,
            numero_ligne=1,
            description=f'Signification {acte.numero_acte}',
            ordre=1
        )

        # 5. Ventilations
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='timbre', groupe_taxation=self.groupe_a,
            description=f'Timbres ({acte.nombre_feuillets}×1.200)',
            montant_ht=Decimal(acte.get_montant_timbres()), ordre=1
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='enregistrement', groupe_taxation=self.groupe_a,
            description='Enregistrement', montant_ht=Decimal('2500'), ordre=2
        )
        VentilationLigneFacture.objects.create(
            ligne_facture=ligne, nature='honoraires', groupe_taxation=self.groupe_b,
            description='Honoraires signification', montant_ht=Decimal('35000'), ordre=3
        )

        # 6. Vérifier calculs
        facture.refresh_from_db()

        # Groupe A = 24000 + 2500 = 26500
        self.assertEqual(facture.montant_ht_groupe_a, Decimal('26500'))
        # Groupe B = 35000
        self.assertEqual(facture.montant_ht_groupe_b, Decimal('35000'))
        # TVA = 18% × 35000 = 6300
        self.assertEqual(facture.montant_tva_tps, Decimal('6300'))

        # 7. Créer et vérifier AIB
        creance = CreanceAIB.creer_depuis_facture(facture)
        # AIB = 3% × 35000 = 1050
        self.assertEqual(creance.montant_aib, Decimal('1050'))
