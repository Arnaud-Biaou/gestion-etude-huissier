"""
Calculateur de délais conforme aux règles OHADA (Articles 1-13 à 1-15)
Pour la procédure de saisie immobilière (Articles 246 à 335)

Règles de computation des délais :
- Point de départ : Le délai court du jour de l'acte
- Délais en jours : JOURS FRANCS (dies a quo et dies ad quem NON COMPTÉS)
- Délais en mois : Expire le jour du dernier mois portant le même quantième
- Expiration : Le délai expire le dernier jour à minuit
- Prorogation : Si expire un jour non ouvrable → report au premier jour ouvrable suivant
- Délais "avant" : Si expire un jour non ouvrable → doit être fait le jour ouvrable PRÉCÉDENT
"""

from datetime import date, timedelta
from calendar import monthrange


class CalculateurDelaisOHADA:
    """
    Calculateur de délais conforme aux règles OHADA (Articles 1-13 à 1-15)

    Règles :
    - Jours francs : dies a quo et dies ad quem NON COMPTÉS
    - Prorogation si jour non ouvrable
    - Délais en mois : même quantième ou dernier jour du mois
    """

    def __init__(self, pays='BJ'):
        """
        Args:
            pays: Code pays pour les jours fériés (BJ = Bénin)
        """
        self.pays = pays
        # Jours fériés du Bénin (à compléter avec les dates réelles)
        self.jours_feries = self._charger_jours_feries()

    def _charger_jours_feries(self):
        """Charge les jours fériés depuis la base de données ou liste fixe"""
        try:
            from parametres.models import JourFerie
            # Récupérer les jours fériés fixes (avec jour et mois)
            feries_fixes = JourFerie.objects.filter(actif=True, jour_mois__isnull=False, mois__isnull=False)

            # Générer les dates pour l'année en cours et l'année suivante
            dates_feries = set()
            annee_courante = date.today().year

            for ferie in feries_fixes:
                for annee in [annee_courante - 1, annee_courante, annee_courante + 1, annee_courante + 2]:
                    try:
                        dates_feries.add(date(annee, ferie.mois, ferie.jour_mois))
                    except ValueError:
                        # Jour invalide pour ce mois (ex: 31 février)
                        pass

            # Ajouter les jours fériés avec date fixe
            feries_date_fixe = JourFerie.objects.filter(actif=True, date_fixe__isnull=False)
            for ferie in feries_date_fixe:
                dates_feries.add(ferie.date_fixe)

            return dates_feries
        except Exception:
            # Liste par défaut des jours fériés fixes du Bénin
            annees = [date.today().year - 1, date.today().year, date.today().year + 1, date.today().year + 2]
            dates_feries = set()

            for annee in annees:
                dates_feries.update({
                    date(annee, 1, 1),    # Nouvel An
                    date(annee, 1, 10),   # Fête du Vodoun
                    date(annee, 5, 1),    # Fête du Travail
                    date(annee, 8, 1),    # Fête de l'Indépendance
                    date(annee, 8, 15),   # Assomption
                    date(annee, 10, 26),  # Journée des Forces Armées
                    date(annee, 11, 1),   # Toussaint
                    date(annee, 12, 25),  # Noël
                    # Note: Fêtes mobiles (Pâques, Ascension, Pentecôte, Tabaski, Maouloud)
                    # doivent être ajoutées manuellement dans JourFerie
                })

            return dates_feries

    def est_jour_ouvrable(self, d):
        """Vérifie si une date est un jour ouvrable"""
        # Samedi = 5, Dimanche = 6
        if d.weekday() >= 5:
            return False
        if d in self.jours_feries:
            return False
        return True

    def prochain_jour_ouvrable(self, d):
        """Retourne le prochain jour ouvrable (inclut d si ouvrable)"""
        while not self.est_jour_ouvrable(d):
            d = d + timedelta(days=1)
        return d

    def jour_ouvrable_precedent(self, d):
        """Retourne le jour ouvrable précédent (inclut d si ouvrable)"""
        while not self.est_jour_ouvrable(d):
            d = d - timedelta(days=1)
        return d

    def ajouter_jours_francs(self, date_depart, nb_jours, pour_agir=True):
        """
        Ajoute des jours francs à une date

        Args:
            date_depart: Date de départ (dies a quo - non compté)
            nb_jours: Nombre de jours francs
            pour_agir: True = délai pour agir (report au jour suivant)
                       False = délai "avant" (doit être fait jour précédent)

        Returns:
            Date d'expiration (après prorogation si nécessaire)
        """
        # Dies a quo non compté, on commence le lendemain
        # Puis on ajoute nb_jours - 1 (car le dernier jour = dies ad quem non compté)
        # En pratique : date_depart + nb_jours + 1
        date_expiration = date_depart + timedelta(days=nb_jours + 1)

        # Prorogation si jour non ouvrable
        if pour_agir:
            # Délai pour agir : report au jour ouvrable suivant
            date_expiration = self.prochain_jour_ouvrable(date_expiration)
        else:
            # Délai "avant" : doit être fait le jour ouvrable précédent
            date_expiration = self.jour_ouvrable_precedent(date_expiration)

        return date_expiration

    def soustraire_jours_francs(self, date_arrivee, nb_jours):
        """
        Calcule une date X jours francs AVANT une date donnée
        (pour les délais "au plus tard X jours avant")

        Args:
            date_arrivee: Date de référence (ex: date d'adjudication)
            nb_jours: Nombre de jours avant

        Returns:
            Date limite (jour ouvrable précédent si nécessaire)
        """
        # Calcul à rebours : date_arrivee - nb_jours - 1
        date_limite = date_arrivee - timedelta(days=nb_jours + 1)

        # Si jour non ouvrable, prendre le jour ouvrable précédent
        date_limite = self.jour_ouvrable_precedent(date_limite)

        return date_limite

    def ajouter_mois(self, date_depart, nb_mois):
        """
        Ajoute des mois à une date (même quantième ou dernier jour)

        Args:
            date_depart: Date de départ
            nb_mois: Nombre de mois à ajouter

        Returns:
            Date d'expiration
        """
        annee = date_depart.year
        mois = date_depart.month
        jour = date_depart.day

        # Calculer le nouveau mois
        nouveau_mois = mois + nb_mois
        nouvelle_annee = annee + (nouveau_mois - 1) // 12
        nouveau_mois = ((nouveau_mois - 1) % 12) + 1

        # Vérifier si le jour existe dans le nouveau mois
        dernier_jour = monthrange(nouvelle_annee, nouveau_mois)[1]
        if jour > dernier_jour:
            jour = dernier_jour

        date_expiration = date(nouvelle_annee, nouveau_mois, jour)

        # Prorogation si jour non ouvrable
        return self.prochain_jour_ouvrable(date_expiration)

    def calculer_fenetre(self, date_reference, jours_min, jours_max, avant=False):
        """
        Calcule une fenêtre de dates (entre X et Y jours)

        Args:
            date_reference: Date de référence
            jours_min: Nombre de jours minimum
            jours_max: Nombre de jours maximum
            avant: True si c'est "avant" la date de référence

        Returns:
            tuple (date_debut_fenetre, date_fin_fenetre)
        """
        if avant:
            # Fenêtre AVANT la date (ex: publicité avant adjudication)
            date_debut = self.soustraire_jours_francs(date_reference, jours_max)
            date_fin = self.soustraire_jours_francs(date_reference, jours_min)
        else:
            # Fenêtre APRÈS la date
            date_debut = self.ajouter_jours_francs(date_reference, jours_min)
            date_fin = self.ajouter_jours_francs(date_reference, jours_max)

        return (date_debut, date_fin)


class CalendrierSaisieImmobiliere:
    """
    Génère le calendrier complet d'une procédure de saisie immobilière
    selon les Articles 246 à 335 de l'Acte uniforme OHADA
    """

    def __init__(self, date_commandement):
        """
        Args:
            date_commandement: Date de signification du commandement
        """
        self.date_commandement = date_commandement
        self.calculateur = CalculateurDelaisOHADA()
        self.etapes = []

    def calculer_calendrier(self, date_publication=None, date_depot_cahier=None,
                           date_sommation=None, date_audience=None, date_adjudication=None):
        """
        Calcule toutes les dates du calendrier

        Les dates peuvent être fournies si déjà connues, sinon elles sont calculées
        """
        self.etapes = []

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 1 : COMMANDEMENT (point de départ)
        # ═══════════════════════════════════════════════════════════════
        self.etapes.append({
            'numero': 1,
            'nature': 'Commandement de payer aux fins de saisie immobilière',
            'article': 'Art. 254',
            'delai_requis': 'Signification faite le {}'.format(
                self.date_commandement.strftime('%d/%m/%Y')
            ),
            'date_proposee': self.date_commandement,
            'date_butoir': None,
            'type': 'fait',
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 2 : PUBLICATION DU COMMANDEMENT
        # (3 mois max après signification - Art. 259)
        # ═══════════════════════════════════════════════════════════════
        date_butoir_publication = self.calculateur.ajouter_mois(self.date_commandement, 3)

        if date_publication is None:
            # Proposer une date raisonnable (1 mois après)
            date_publication = self.calculateur.ajouter_mois(self.date_commandement, 1)

        self.etapes.append({
            'numero': 2,
            'nature': 'Dénonciation de commandement aux fins de visa et de publication',
            'article': 'Art. 259',
            'delai_requis': 'Trois (03) mois au plus tard après la signification du commandement',
            'date_proposee': date_publication,
            'date_butoir': date_butoir_publication,
            'type': 'butoir',
            'sanction': 'Caducité',
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 3 : DÉPÔT DU CAHIER DES CHARGES
        # (50 jours max après publication - Art. 266)
        # ═══════════════════════════════════════════════════════════════
        date_butoir_depot = self.calculateur.ajouter_jours_francs(date_publication, 50)

        if date_depot_cahier is None:
            # Proposer 40 jours après publication
            date_depot_cahier = self.calculateur.ajouter_jours_francs(date_publication, 40)

        self.etapes.append({
            'numero': 3,
            'nature': 'Dépôt du cahier des charges',
            'article': 'Art. 266',
            'delai_requis': '50 jours au maximum à peine de caducité à compter de la publication du commandement',
            'date_proposee': date_depot_cahier,
            'date_butoir': date_butoir_depot,
            'type': 'butoir',
            'sanction': 'Déchéance',
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 4 : SOMMATION DE PRENDRE CONNAISSANCE
        # (8 jours max après dépôt - Art. 269)
        # ═══════════════════════════════════════════════════════════════
        date_butoir_sommation = self.calculateur.ajouter_jours_francs(date_depot_cahier, 8)

        if date_sommation is None:
            # Proposer 5 jours après dépôt
            date_sommation = self.calculateur.ajouter_jours_francs(date_depot_cahier, 5)

        self.etapes.append({
            'numero': 4,
            'nature': "Sommation d'avoir à prendre connaissance du cahier des charges",
            'article': 'Art. 269',
            'delai_requis': '08 jours au plus tard après dépôt du cahier des charges',
            'date_proposee': date_sommation,
            'date_butoir': date_butoir_sommation,
            'type': 'butoir',
            'sanction': 'Nullité',
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 5 : DIRES ET OBSERVATIONS
        # (5 jours avant audience éventuelle - Art. 270 al.3)
        # ═══════════════════════════════════════════════════════════════

        # D'abord calculer la date d'audience éventuelle
        date_audience_min = self.calculateur.ajouter_jours_francs(date_sommation, 30)

        if date_audience is None:
            # Proposer 35 jours après sommation
            date_audience = self.calculateur.ajouter_jours_francs(date_sommation, 35)

        # Date butoir des dires = 5 jours avant audience (délai "avant")
        date_butoir_dires = self.calculateur.soustraire_jours_francs(date_audience, 5)

        self.etapes.append({
            'numero': 5,
            'nature': 'Dires et Observations',
            'article': 'Art. 270 al.3',
            'delai_requis': "05 jours au plus tard avant l'audience éventuelle",
            'date_proposee': None,  # Pas de date proposée, juste une butoir
            'date_butoir': date_butoir_dires,
            'type': 'avant',
            'sanction': 'Déchéance',
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 6 : AUDIENCE ÉVENTUELLE
        # (min 30 jours après sommation - Art. 270)
        # ═══════════════════════════════════════════════════════════════
        self.etapes.append({
            'numero': 6,
            'nature': 'Audience éventuelle',
            'article': 'Art. 270',
            'delai_requis': 'Ne peut avoir lieu moins de 30 jours après sommation de prendre connaissance du cahier des charges',
            'date_proposee': date_audience,
            'date_butoir': date_audience_min,
            'type': 'minimum',
            'note': 'Pas avant le {}'.format(date_audience_min.strftime('%d/%m/%Y')),
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 7 : PUBLICITÉ EN VUE DE LA VENTE
        # (30 jours au plus tôt et 15 jours au plus tard avant adjudication)
        # ═══════════════════════════════════════════════════════════════

        # Calculer la fenêtre d'adjudication d'abord
        # Art. 268 et 270 al.2 : entre 30e et 60e jour après audience éventuelle
        # ET entre 45e et 90e jour après dépôt cahier des charges

        adj_min_audience = self.calculateur.ajouter_jours_francs(date_audience, 30)
        adj_max_audience = self.calculateur.ajouter_jours_francs(date_audience, 60)
        adj_min_depot = self.calculateur.ajouter_jours_francs(date_depot_cahier, 45)
        adj_max_depot = self.calculateur.ajouter_jours_francs(date_depot_cahier, 90)

        # Fenêtre d'adjudication = intersection des deux contraintes
        adj_min = max(adj_min_audience, adj_min_depot)
        adj_max = min(adj_max_audience, adj_max_depot)

        if date_adjudication is None:
            # Proposer au milieu de la fenêtre
            delta = (adj_max - adj_min).days // 2
            date_adjudication = adj_min + timedelta(days=delta)
            date_adjudication = self.calculateur.prochain_jour_ouvrable(date_adjudication)

        # Fenêtre de publicité
        pub_debut = self.calculateur.soustraire_jours_francs(date_adjudication, 30)
        pub_fin = self.calculateur.soustraire_jours_francs(date_adjudication, 15)

        self.etapes.append({
            'numero': 7,
            'nature': 'Publicité en vue de la vente',
            'article': 'Art. 276 et suivants',
            'delai_requis': "30 jours au plus tôt et 15 jours au plus tard avant l'adjudication",
            'date_proposee': (pub_debut, pub_fin),  # Fenêtre
            'date_butoir': pub_fin,
            'type': 'fenetre',
            'details': [
                'Publication sommaire au journal',
                'Apposition de placards',
                "Dénonciation du procès-verbal d'apposition de placards avec sommation d'avoir à assister à la vente",
            ],
        })

        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 8 : ADJUDICATION
        # (entre 30e et 60e jour après audience, et 45-90 jours après dépôt)
        # ═══════════════════════════════════════════════════════════════
        self.etapes.append({
            'numero': 8,
            'nature': 'Adjudication',
            'article': 'Art. 268 et 270 al.2',
            'delai_requis': "Entre le 30e et le 60e jour après l'audience éventuelle ; et 45 jours au plus tôt et 90 jours au plus tard après le dépôt du cahier des charges",
            'date_proposee': date_adjudication,
            'date_butoir': (adj_min, adj_max),
            'type': 'fenetre',
            'note': 'Pas avant le {} et pas après le {}'.format(
                adj_min.strftime('%d/%m/%Y'),
                adj_max.strftime('%d/%m/%Y')
            ),
        })

        return self.etapes

    def to_dict(self):
        """Retourne le calendrier sous forme de dictionnaire"""
        return {
            'date_commandement': self.date_commandement,
            'etapes': self.etapes,
        }
