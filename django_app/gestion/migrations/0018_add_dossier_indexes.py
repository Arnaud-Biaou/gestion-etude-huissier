# Generated manually for Dossier performance optimization
# Adds database indexes on frequently filtered/sorted fields

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration pour ajouter des indexes sur le modele Dossier.

    Champs indexes:
    - statut: filtre tres frequent (dashboard, listes)
    - type_dossier: filtre frequent (statistiques, filtres)
    - phase: filtre frequent (amiable/force)
    - date_ouverture: tri et filtre frequent
    - date_creation: tri par defaut du modele

    Note: Les ForeignKey (creancier, affecte_a, cree_par) ont deja
    des indexes automatiques crees par Django.
    """

    dependencies = [
        ("gestion", "0017_import_tables_update"),
    ]

    operations = [
        # Index sur le champ 'statut' - tres frequent dans dashboard
        migrations.AddIndex(
            model_name="dossier",
            index=models.Index(
                fields=["statut"],
                name="gestion_dos_statut_idx",
            ),
        ),

        # Index sur le champ 'type_dossier' - frequent dans filtres et stats
        migrations.AddIndex(
            model_name="dossier",
            index=models.Index(
                fields=["type_dossier"],
                name="gestion_dos_type_idx",
            ),
        ),

        # Index sur le champ 'phase' - filtre amiable/force
        migrations.AddIndex(
            model_name="dossier",
            index=models.Index(
                fields=["phase"],
                name="gestion_dos_phase_idx",
            ),
        ),

        # Index sur le champ 'date_ouverture' - tri et filtre par date
        migrations.AddIndex(
            model_name="dossier",
            index=models.Index(
                fields=["date_ouverture"],
                name="gestion_dos_date_ouv_idx",
            ),
        ),

        # Index sur le champ 'date_creation' - ordering par defaut
        migrations.AddIndex(
            model_name="dossier",
            index=models.Index(
                fields=["date_creation"],
                name="gestion_dos_date_cre_idx",
            ),
        ),
    ]
