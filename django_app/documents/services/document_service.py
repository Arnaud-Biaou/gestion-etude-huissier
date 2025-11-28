"""
Service principal de gestion des documents
Génération, stockage, partage et audit
"""
import os
import uuid
import hashlib
import mimetypes
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q

from ..models import (
    Document, DossierVirtuel, ModeleDocument, GenerationDocument,
    AuditDocument, PartageDocument, NumeroActe, ConfigurationDocuments,
    VersionDocument
)
from .pdf_generator import PDFGenerator


class DocumentService:
    """Service principal pour la gestion des documents"""

    def __init__(self, utilisateur=None):
        self.utilisateur = utilisateur
        self.config = ConfigurationDocuments.get_instance()
        self.pdf_generator = self._init_pdf_generator()

    def _init_pdf_generator(self):
        """Initialise le générateur PDF avec la configuration"""
        config = {
            'nom_etude': self.config.nom_etude or 'ÉTUDE D\'HUISSIER DE JUSTICE',
            'adresse_etude': self.config.adresse_etude or '',
            'telephone_etude': self.config.telephone_etude or '',
            'email_etude': self.config.email_etude or '',
            'ifu_etude': self.config.ifu_etude or '',
            'rccm_etude': self.config.rccm_etude or '',
            'nom_huissier': self.config.nom_huissier or '',
            'qualite_huissier': self.config.qualite_huissier or 'Huissier de Justice',
        }
        return PDFGenerator(config)

    # ==========================================
    # GESTION DES DOSSIERS VIRTUELS
    # ==========================================

    def creer_structure_dossier_juridique(self, dossier_juridique):
        """
        Crée la structure de dossiers standard pour un dossier juridique

        Structure:
        - [Reference]/
          - 01_Actes/
          - 02_Decisions_Titres/
          - 03_Pieces_Client/
          - 04_Correspondances/
          - 05_Facturation/
          - 06_Divers/
        """
        # Dossier racine du dossier juridique
        racine = DossierVirtuel.objects.create(
            nom=dossier_juridique.reference,
            type_dossier='dossier_juridique',
            dossier_juridique=dossier_juridique,
            est_systeme=True,
            cree_par=self.utilisateur
        )

        # Sous-dossiers standards
        sous_dossiers = [
            ('01_Actes', 'actes', 'file-text', '#1a365d'),
            ('02_Decisions_Titres', 'decisions', 'gavel', '#c6a962'),
            ('03_Pieces_Client', 'pieces', 'folder-open', '#2f855a'),
            ('04_Correspondances', 'correspondances', 'mail', '#3182ce'),
            ('05_Facturation', 'facturation', 'receipt', '#c05621'),
            ('06_Divers', 'divers', 'file', '#718096'),
        ]

        for nom, type_dossier, icone, couleur in sous_dossiers:
            DossierVirtuel.objects.create(
                nom=nom,
                type_dossier=type_dossier,
                parent=racine,
                dossier_juridique=dossier_juridique,
                icone=icone,
                couleur=couleur,
                est_systeme=True,
                cree_par=self.utilisateur
            )

        return racine

    def obtenir_dossier_pour_type_document(self, dossier_juridique, type_document):
        """
        Retourne le dossier virtuel approprié pour un type de document

        Mapping:
        - acte_* -> 01_Actes
        - decision_*, titre_*, jugement, ordonnance -> 02_Decisions_Titres
        - piece_*, contrat, attestation -> 03_Pieces_Client
        - lettre_*, courrier, email -> 04_Correspondances
        - facture, devis, recu, note_* -> 05_Facturation
        - autres -> 06_Divers
        """
        type_to_folder = {
            'acte_commandement': 'actes',
            'acte_signification': 'actes',
            'acte_pv_saisie': 'actes',
            'acte_pv_constat': 'actes',
            'acte_denonciation': 'actes',
            'acte_autre': 'actes',
            'decision_justice': 'decisions',
            'titre_executoire': 'decisions',
            'jugement': 'decisions',
            'ordonnance': 'decisions',
            'facture': 'facturation',
            'devis': 'facturation',
            'recu': 'facturation',
            'note_honoraires': 'facturation',
            'decompte': 'facturation',
            'lettre_mise_demeure': 'correspondances',
            'lettre_relance': 'correspondances',
            'courrier': 'correspondances',
            'email': 'correspondances',
            'piece_identite': 'pieces',
            'contrat': 'pieces',
            'attestation': 'pieces',
        }

        type_dossier = type_to_folder.get(type_document, 'divers')

        dossier = DossierVirtuel.objects.filter(
            dossier_juridique=dossier_juridique,
            type_dossier=type_dossier
        ).first()

        return dossier

    # ==========================================
    # GÉNÉRATION DE DOCUMENTS
    # ==========================================

    @transaction.atomic
    def generer_fiche_dossier(self, dossier_juridique):
        """Génère et stocke la fiche du dossier"""
        start_time = timezone.now()

        # Créer l'enregistrement de génération
        generation = GenerationDocument.objects.create(
            dossier_juridique=dossier_juridique,
            variables={'type': 'fiche_dossier'},
            statut='en_cours',
            cree_par=self.utilisateur
        )

        try:
            # Générer le PDF
            pdf_bytes = self.pdf_generator.generer_fiche_dossier(dossier_juridique)

            # Créer le document
            nom_fichier = f"Fiche_{dossier_juridique.reference}_{datetime.now().strftime('%Y%m%d')}.pdf"

            # Trouver ou créer le dossier de destination
            dossier_dest = self.obtenir_dossier_pour_type_document(
                dossier_juridique, 'fiche_dossier'
            )
            if not dossier_dest:
                # Créer la structure si elle n'existe pas
                racine = self.creer_structure_dossier_juridique(dossier_juridique)
                dossier_dest = DossierVirtuel.objects.filter(
                    dossier_juridique=dossier_juridique,
                    type_dossier='divers'
                ).first()

            document = Document.objects.create(
                nom=nom_fichier,
                nom_original=nom_fichier,
                type_document='fiche_dossier',
                description=f"Fiche du dossier {dossier_juridique.reference}",
                dossier=dossier_dest,
                dossier_juridique=dossier_juridique,
                taille=len(pdf_bytes),
                mime_type='application/pdf',
                extension='.pdf',
                statut='genere',
                est_genere=True,
                cree_par=self.utilisateur
            )

            # Sauvegarder le fichier
            document.fichier.save(nom_fichier, ContentFile(pdf_bytes))
            document.calculer_hash()
            document.save()

            # Mettre à jour la génération
            generation.document_genere = document
            generation.statut = 'termine'
            generation.date_generation = timezone.now()
            generation.duree_generation = (timezone.now() - start_time).total_seconds()
            generation.save()

            # Audit
            self._audit(document, 'generation', {
                'type': 'fiche_dossier',
                'dossier_reference': dossier_juridique.reference
            })

            return document

        except Exception as e:
            generation.statut = 'erreur'
            generation.message_erreur = str(e)
            generation.save()
            raise

    @transaction.atomic
    def generer_acte(self, dossier_juridique, type_acte, acte_data, modele=None):
        """Génère un acte de procédure"""
        start_time = timezone.now()

        # Obtenir le modèle si non fourni
        if modele is None:
            modele = ModeleDocument.objects.filter(
                type_modele='acte',
                code=type_acte,
                actif=True
            ).first()

        # Générer le numéro d'acte
        numero_acte = NumeroActe.prochain_numero()
        acte_data['numero_acte'] = numero_acte
        acte_data['date_acte'] = acte_data.get('date_acte', datetime.now())

        # Créer l'enregistrement de génération
        generation = GenerationDocument.objects.create(
            modele=modele,
            dossier_juridique=dossier_juridique,
            variables=acte_data,
            statut='en_cours',
            cree_par=self.utilisateur
        )

        try:
            # Générer le PDF
            pdf_bytes = self.pdf_generator.generer_acte_procedure(acte_data, modele)

            # Créer le document
            titre_acte = acte_data.get('titre', type_acte).replace(' ', '_')
            nom_fichier = f"Acte_{numero_acte.replace('/', '-')}_{titre_acte}.pdf"

            # Trouver le dossier de destination
            dossier_dest = self.obtenir_dossier_pour_type_document(
                dossier_juridique, f'acte_{type_acte}'
            )

            document = Document.objects.create(
                nom=nom_fichier,
                nom_original=nom_fichier,
                type_document=f'acte_{type_acte}' if type_acte in ['commandement', 'signification', 'pv_saisie', 'pv_constat', 'denonciation'] else 'acte_autre',
                description=f"Acte N° {numero_acte} - {acte_data.get('titre', type_acte)}",
                dossier=dossier_dest,
                dossier_juridique=dossier_juridique,
                taille=len(pdf_bytes),
                mime_type='application/pdf',
                extension='.pdf',
                statut='genere',
                est_genere=True,
                metadata={'numero_acte': numero_acte, 'type_acte': type_acte},
                cree_par=self.utilisateur
            )

            document.fichier.save(nom_fichier, ContentFile(pdf_bytes))
            document.calculer_hash()
            document.save()

            # Mettre à jour la génération
            generation.document_genere = document
            generation.statut = 'termine'
            generation.date_generation = timezone.now()
            generation.duree_generation = (timezone.now() - start_time).total_seconds()
            generation.save()

            # Audit
            self._audit(document, 'generation', {
                'type': 'acte',
                'numero_acte': numero_acte,
                'type_acte': type_acte
            })

            return document

        except Exception as e:
            generation.statut = 'erreur'
            generation.message_erreur = str(e)
            generation.save()
            raise

    @transaction.atomic
    def generer_facture_pdf(self, facture):
        """Génère le PDF d'une facture"""
        start_time = timezone.now()

        generation = GenerationDocument.objects.create(
            facture=facture,
            dossier_juridique=facture.dossier if hasattr(facture, 'dossier') else None,
            variables={'facture_numero': facture.numero},
            statut='en_cours',
            cree_par=self.utilisateur
        )

        try:
            pdf_bytes = self.pdf_generator.generer_facture(facture)

            nom_fichier = f"Facture_{facture.numero}_{datetime.now().strftime('%Y%m%d')}.pdf"

            # Trouver le dossier de destination
            dossier_dest = None
            if hasattr(facture, 'dossier') and facture.dossier:
                dossier_dest = self.obtenir_dossier_pour_type_document(
                    facture.dossier, 'facture'
                )

            document = Document.objects.create(
                nom=nom_fichier,
                nom_original=nom_fichier,
                type_document='facture',
                description=f"Facture {facture.numero} - {facture.client}",
                dossier=dossier_dest,
                dossier_juridique=facture.dossier if hasattr(facture, 'dossier') else None,
                taille=len(pdf_bytes),
                mime_type='application/pdf',
                extension='.pdf',
                statut='genere',
                est_genere=True,
                metadata={'facture_numero': facture.numero},
                cree_par=self.utilisateur
            )

            document.fichier.save(nom_fichier, ContentFile(pdf_bytes))
            document.calculer_hash()
            document.save()

            generation.document_genere = document
            generation.statut = 'termine'
            generation.date_generation = timezone.now()
            generation.duree_generation = (timezone.now() - start_time).total_seconds()
            generation.save()

            self._audit(document, 'generation', {
                'type': 'facture',
                'facture_numero': facture.numero
            })

            return document

        except Exception as e:
            generation.statut = 'erreur'
            generation.message_erreur = str(e)
            generation.save()
            raise

    @transaction.atomic
    def generer_decompte(self, calcul_data, dossier_juridique=None):
        """Génère un décompte de recouvrement"""
        start_time = timezone.now()

        generation = GenerationDocument.objects.create(
            dossier_juridique=dossier_juridique,
            variables=calcul_data,
            statut='en_cours',
            cree_par=self.utilisateur
        )

        try:
            pdf_bytes = self.pdf_generator.generer_decompte_recouvrement(
                calcul_data, dossier_juridique
            )

            ref = dossier_juridique.reference if dossier_juridique else 'SANS_REF'
            nom_fichier = f"Decompte_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            dossier_dest = None
            if dossier_juridique:
                dossier_dest = self.obtenir_dossier_pour_type_document(
                    dossier_juridique, 'decompte'
                )

            document = Document.objects.create(
                nom=nom_fichier,
                nom_original=nom_fichier,
                type_document='decompte',
                description=f"Décompte de recouvrement OHADA - {ref}",
                dossier=dossier_dest,
                dossier_juridique=dossier_juridique,
                taille=len(pdf_bytes),
                mime_type='application/pdf',
                extension='.pdf',
                statut='genere',
                est_genere=True,
                metadata=calcul_data,
                cree_par=self.utilisateur
            )

            document.fichier.save(nom_fichier, ContentFile(pdf_bytes))
            document.calculer_hash()
            document.save()

            generation.document_genere = document
            generation.statut = 'termine'
            generation.date_generation = timezone.now()
            generation.duree_generation = (timezone.now() - start_time).total_seconds()
            generation.save()

            self._audit(document, 'generation', {
                'type': 'decompte',
                'montant_total': calcul_data.get('total_general', 0)
            })

            return document

        except Exception as e:
            generation.statut = 'erreur'
            generation.message_erreur = str(e)
            generation.save()
            raise

    @transaction.atomic
    def generer_lettre(self, lettre_data, dossier_juridique=None, modele=None):
        """Génère une lettre (mise en demeure, relance, etc.)"""
        start_time = timezone.now()

        if modele is None and lettre_data.get('type_lettre'):
            modele = ModeleDocument.objects.filter(
                type_modele='courrier',
                code=lettre_data['type_lettre'],
                actif=True
            ).first()

        generation = GenerationDocument.objects.create(
            modele=modele,
            dossier_juridique=dossier_juridique,
            variables=lettre_data,
            statut='en_cours',
            cree_par=self.utilisateur
        )

        try:
            pdf_bytes = self.pdf_generator.generer_lettre(lettre_data, modele)

            type_lettre = lettre_data.get('type_lettre', 'courrier')
            ref = dossier_juridique.reference if dossier_juridique else 'SANS_REF'
            nom_fichier = f"{type_lettre}_{ref}_{datetime.now().strftime('%Y%m%d')}.pdf"

            dossier_dest = None
            if dossier_juridique:
                dossier_dest = self.obtenir_dossier_pour_type_document(
                    dossier_juridique, f'lettre_{type_lettre}'
                )

            type_doc = 'lettre_mise_demeure' if type_lettre == 'mise_demeure' else (
                'lettre_relance' if type_lettre == 'relance' else 'courrier'
            )

            document = Document.objects.create(
                nom=nom_fichier,
                nom_original=nom_fichier,
                type_document=type_doc,
                description=f"{lettre_data.get('objet', type_lettre)} - {ref}",
                dossier=dossier_dest,
                dossier_juridique=dossier_juridique,
                taille=len(pdf_bytes),
                mime_type='application/pdf',
                extension='.pdf',
                statut='genere',
                est_genere=True,
                metadata=lettre_data,
                cree_par=self.utilisateur
            )

            document.fichier.save(nom_fichier, ContentFile(pdf_bytes))
            document.calculer_hash()
            document.save()

            generation.document_genere = document
            generation.statut = 'termine'
            generation.date_generation = timezone.now()
            generation.duree_generation = (timezone.now() - start_time).total_seconds()
            generation.save()

            self._audit(document, 'generation', {
                'type': type_lettre,
                'destinataire': lettre_data.get('destinataire', {}).get('nom', '')
            })

            return document

        except Exception as e:
            generation.statut = 'erreur'
            generation.message_erreur = str(e)
            generation.save()
            raise

    # ==========================================
    # GESTION DES FICHIERS
    # ==========================================

    def upload_document(self, fichier, type_document='autre', dossier_juridique=None, dossier=None, description=''):
        """
        Upload un document

        Args:
            fichier: Fichier uploadé (InMemoryUploadedFile ou TemporaryUploadedFile)
            type_document: Type de document
            dossier_juridique: Dossier juridique associé (optionnel)
            dossier: Dossier virtuel de destination (optionnel)
            description: Description du document

        Returns:
            Document créé
        """
        # Vérifier la taille
        if fichier.size > self.config.limite_upload_mo * 1024 * 1024:
            raise ValueError(f"Fichier trop volumineux (max {self.config.limite_upload_mo} Mo)")

        # Vérifier l'extension
        extension = os.path.splitext(fichier.name)[1].lower()
        if self.config.types_autorises and extension not in self.config.types_autorises:
            raise ValueError(f"Type de fichier non autorisé: {extension}")

        # Déterminer le dossier de destination
        if dossier is None and dossier_juridique:
            dossier = self.obtenir_dossier_pour_type_document(
                dossier_juridique, type_document
            )

        # Créer le document
        mime_type, _ = mimetypes.guess_type(fichier.name)

        document = Document.objects.create(
            nom=fichier.name,
            nom_original=fichier.name,
            type_document=type_document,
            description=description,
            fichier=fichier,
            dossier=dossier,
            dossier_juridique=dossier_juridique,
            taille=fichier.size,
            mime_type=mime_type or 'application/octet-stream',
            extension=extension,
            statut='genere',
            cree_par=self.utilisateur
        )

        document.calculer_hash()
        document.save()

        self._audit(document, 'creation', {
            'nom_original': fichier.name,
            'taille': fichier.size
        })

        return document

    def telecharger_document(self, document):
        """Enregistre un téléchargement dans l'audit"""
        self._audit(document, 'telechargement')
        return document.fichier

    def supprimer_document(self, document, definitif=False):
        """
        Supprime un document (corbeille ou définitif)

        Args:
            document: Document à supprimer
            definitif: Si True, suppression définitive

        Returns:
            True si succès
        """
        if definitif:
            self._audit(document, 'suppression', {'definitif': True})
            document.fichier.delete()
            document.delete()
        else:
            document.statut = 'supprime'
            document.date_suppression = timezone.now()
            document.save()
            self._audit(document, 'suppression', {'definitif': False})

        return True

    def restaurer_document(self, document):
        """Restaure un document de la corbeille"""
        if document.statut != 'supprime':
            raise ValueError("Le document n'est pas dans la corbeille")

        document.statut = 'genere'
        document.date_suppression = None
        document.save()

        self._audit(document, 'restauration')

        return document

    def deplacer_document(self, document, nouveau_dossier):
        """Déplace un document vers un autre dossier"""
        ancien_dossier = document.dossier
        document.dossier = nouveau_dossier
        document.save()

        self._audit(document, 'deplacement', {
            'ancien_dossier': str(ancien_dossier) if ancien_dossier else None,
            'nouveau_dossier': str(nouveau_dossier)
        })

        return document

    def copier_document(self, document, dossier_destination):
        """Copie un document vers un autre dossier"""
        nouveau_doc = Document.objects.create(
            nom=f"Copie de {document.nom}",
            nom_original=document.nom_original,
            type_document=document.type_document,
            description=document.description,
            dossier=dossier_destination,
            dossier_juridique=document.dossier_juridique,
            taille=document.taille,
            mime_type=document.mime_type,
            extension=document.extension,
            hash_md5=document.hash_md5,
            hash_sha256=document.hash_sha256,
            cree_par=self.utilisateur
        )

        # Copier le fichier
        if document.fichier:
            nouveau_doc.fichier.save(
                document.fichier.name.split('/')[-1],
                document.fichier
            )

        self._audit(nouveau_doc, 'copie', {
            'document_source': str(document.id)
        })

        return nouveau_doc

    def creer_version(self, document, nouveau_fichier, commentaire=''):
        """Crée une nouvelle version du document"""
        # Sauvegarder l'ancienne version
        VersionDocument.objects.create(
            document=document,
            numero_version=document.version,
            fichier=document.fichier,
            taille=document.taille,
            hash_md5=document.hash_md5,
            commentaire=commentaire,
            auteur=self.utilisateur
        )

        # Mettre à jour le document
        document.fichier = nouveau_fichier
        document.version += 1
        document.taille = nouveau_fichier.size
        document.modifie_par = self.utilisateur
        document.save()
        document.calculer_hash()
        document.save()

        self._audit(document, 'modification', {
            'nouvelle_version': document.version,
            'commentaire': commentaire
        })

        return document

    # ==========================================
    # PARTAGE
    # ==========================================

    def creer_partage(self, document=None, dossier=None, type_partage='lecture',
                      mot_de_passe=None, duree_jours=None, destinataire_email=None,
                      destinataire_nom=None):
        """
        Crée un lien de partage pour un document ou dossier

        Args:
            document: Document à partager (optionnel)
            dossier: Dossier à partager (optionnel)
            type_partage: 'lecture', 'telechargement', 'modification'
            mot_de_passe: Mot de passe de protection (optionnel)
            duree_jours: Durée de validité en jours
            destinataire_email: Email du destinataire
            destinataire_nom: Nom du destinataire

        Returns:
            PartageDocument créé
        """
        if not document and not dossier:
            raise ValueError("Vous devez spécifier un document ou un dossier")

        if duree_jours is None:
            duree_jours = self.config.duree_partage_defaut

        partage = PartageDocument(
            document=document,
            dossier=dossier,
            type_partage=type_partage,
            date_expiration=timezone.now() + timedelta(days=duree_jours) if duree_jours else None,
            destinataire_email=destinataire_email or '',
            destinataire_nom=destinataire_nom or '',
            cree_par=self.utilisateur
        )

        if mot_de_passe:
            partage.mot_de_passe_hash = hashlib.sha256(mot_de_passe.encode()).hexdigest()

        partage.save()

        if document:
            self._audit(document, 'partage', {
                'token': partage.token,
                'type_partage': type_partage,
                'destinataire': destinataire_email
            })

        return partage

    def revoquer_partage(self, partage):
        """Révoque un partage"""
        partage.actif = False
        partage.save()

        if partage.document:
            self._audit(partage.document, 'partage', {
                'action': 'revocation',
                'token': partage.token
            })

        return True

    # ==========================================
    # RECHERCHE
    # ==========================================

    def rechercher_documents(self, query=None, type_document=None, dossier_juridique=None,
                             date_debut=None, date_fin=None, statut=None, limit=50):
        """
        Recherche des documents selon différents critères

        Args:
            query: Recherche textuelle (nom, description, contenu OCR)
            type_document: Type de document
            dossier_juridique: Filtrer par dossier juridique
            date_debut: Date de création minimum
            date_fin: Date de création maximum
            statut: Statut du document
            limit: Nombre maximum de résultats

        Returns:
            QuerySet de documents
        """
        qs = Document.objects.exclude(statut='supprime')

        if query:
            qs = qs.filter(
                Q(nom__icontains=query) |
                Q(description__icontains=query) |
                Q(contenu_texte__icontains=query)
            )

        if type_document:
            qs = qs.filter(type_document=type_document)

        if dossier_juridique:
            qs = qs.filter(dossier_juridique=dossier_juridique)

        if date_debut:
            qs = qs.filter(date_creation__gte=date_debut)

        if date_fin:
            qs = qs.filter(date_creation__lte=date_fin)

        if statut:
            qs = qs.filter(statut=statut)

        return qs.order_by('-date_creation')[:limit]

    # ==========================================
    # STATISTIQUES
    # ==========================================

    def obtenir_statistiques(self, dossier_juridique=None):
        """
        Calcule les statistiques des documents

        Returns:
            Dict avec les statistiques
        """
        from django.db.models import Count, Sum

        qs = Document.objects.exclude(statut='supprime')

        if dossier_juridique:
            qs = qs.filter(dossier_juridique=dossier_juridique)

        stats = {
            'total_documents': qs.count(),
            'espace_utilise': qs.aggregate(total=Sum('taille'))['total'] or 0,
            'par_type': list(qs.values('type_document').annotate(
                count=Count('id'),
                taille=Sum('taille')
            ).order_by('-count')),
            'documents_recents': qs.order_by('-date_creation')[:10].values(
                'id', 'nom', 'type_document', 'date_creation'
            ),
            'documents_partages': PartageDocument.objects.filter(
                actif=True
            ).count() if not dossier_juridique else PartageDocument.objects.filter(
                document__dossier_juridique=dossier_juridique,
                actif=True
            ).count(),
        }

        # Espace par type de fichier
        stats['espace_par_extension'] = list(qs.values('extension').annotate(
            count=Count('id'),
            taille=Sum('taille')
        ).order_by('-taille')[:10])

        return stats

    # ==========================================
    # AUDIT
    # ==========================================

    def _audit(self, document, action, details=None):
        """Enregistre une action dans le journal d'audit"""
        if not self.config.audit_actif:
            return

        AuditDocument.objects.create(
            document=document,
            action=action,
            details=details or {},
            utilisateur=self.utilisateur
        )

    def obtenir_historique(self, document):
        """Retourne l'historique d'audit d'un document"""
        return AuditDocument.objects.filter(document=document).order_by('-date')

    # ==========================================
    # NETTOYAGE
    # ==========================================

    def vider_corbeille(self, jours_retention=None):
        """
        Supprime définitivement les documents de la corbeille

        Args:
            jours_retention: Nombre de jours avant suppression (par défaut: config)

        Returns:
            Nombre de documents supprimés
        """
        if jours_retention is None:
            jours_retention = self.config.duree_retention_corbeille

        date_limite = timezone.now() - timedelta(days=jours_retention)

        documents = Document.objects.filter(
            statut='supprime',
            date_suppression__lt=date_limite
        )

        count = documents.count()

        for doc in documents:
            doc.fichier.delete()
            doc.delete()

        return count

    def nettoyer_audit(self, jours_retention=None):
        """Supprime les anciens enregistrements d'audit"""
        if jours_retention is None:
            jours_retention = self.config.duree_retention_audit

        date_limite = timezone.now() - timedelta(days=jours_retention)

        deleted, _ = AuditDocument.objects.filter(date__lt=date_limite).delete()

        return deleted
