# Generated manually for import tables update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gestion", "0016_sessionimport_dossierimporttemp"),
    ]

    operations = [
        # ═══════════════════════════════════════════════════════════════
        # SessionImport: Mise à jour des choix source_type
        # ═══════════════════════════════════════════════════════════════
        migrations.AlterField(
            model_name="sessionimport",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("sql_file", "Fichier SQL"),
                    ("csv", "Fichier CSV"),
                    ("excel", "Fichier Excel"),
                ],
                default="csv",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="sessionimport",
            name="progression",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="sessionimport",
            name="rapport_json",
            field=models.TextField(blank=True),
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Renommage des champs
        # ═══════════════════════════════════════════════════════════════
        migrations.RenameField(
            model_name="dossierimporttemp",
            old_name="donnees_brutes",
            new_name="donnees_brutes_json",
        ),
        migrations.AlterField(
            model_name="dossierimporttemp",
            name="donnees_brutes_json",
            field=models.TextField(blank=True, help_text="Toutes les colonnes en JSON"),
        ),
        migrations.RenameField(
            model_name="dossierimporttemp",
            old_name="date_ouverture",
            new_name="date_ouverture_parsee",
        ),
        migrations.RenameField(
            model_name="dossierimporttemp",
            old_name="message_erreur",
            new_name="message_validation",
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Nouveaux champs pour le demandeur
        # ═══════════════════════════════════════════════════════════════
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_texte_brut",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_est_personne_morale",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_raison_sociale",
            field=models.CharField(blank=True, max_length=300),
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Nouveaux champs pour le défendeur
        # ═══════════════════════════════════════════════════════════════
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_texte_brut",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_est_personne_morale",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_raison_sociale",
            field=models.CharField(blank=True, max_length=300),
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Suppression des ForeignKeys
        # ═══════════════════════════════════════════════════════════════
        migrations.RemoveField(
            model_name="dossierimporttemp",
            name="demandeur_existant",
        ),
        migrations.RemoveField(
            model_name="dossierimporttemp",
            name="defendeur_existant",
        ),
        migrations.RemoveField(
            model_name="dossierimporttemp",
            name="dossier_existant",
        ),
        migrations.RemoveField(
            model_name="dossierimporttemp",
            name="dossier_cree",
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Nouveaux champs pour les correspondances
        # ═══════════════════════════════════════════════════════════════
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_existant_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_existant_nom",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="demandeur_score_similarite",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_existant_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_existant_nom",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="defendeur_score_similarite",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="dossier_existant_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="dossier_existant_ref",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="dossierimporttemp",
            name="dossier_cree_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),

        # ═══════════════════════════════════════════════════════════════
        # DossierImportTemp: Mise à jour des choix de statut
        # ═══════════════════════════════════════════════════════════════
        migrations.AlterField(
            model_name="dossierimporttemp",
            name="statut",
            field=models.CharField(
                choices=[
                    ("en_attente", "En attente de validation"),
                    ("valide", "Validé pour import"),
                    ("importe", "Importé avec succès"),
                    ("doublon", "Doublon détecté"),
                    ("erreur", "Erreur"),
                    ("ignore", "Ignoré manuellement"),
                ],
                default="en_attente",
                max_length=20,
            ),
        ),
    ]
