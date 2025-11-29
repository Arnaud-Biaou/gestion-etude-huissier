# Generated manually for dossier reference configuration
# Adds configurable fields for Dossier.generer_reference()

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Ajoute 2 champs configurables pour la generation des references de dossiers:
    - dossier_numero_cabinet: Prefixe numerique (ex: 175)
    - dossier_initiales_huissier: Suffixe initiales (ex: MAB)

    Ces champs remplacent les valeurs hardcodees dans Dossier.generer_reference()
    """

    dependencies = [
        ("parametres", "0004_add_hr_parameters_and_ipts_bareme"),
    ]

    operations = [
        migrations.AddField(
            model_name="configurationetude",
            name="dossier_numero_cabinet",
            field=models.PositiveIntegerField(
                default=175,
                verbose_name="Numéro de cabinet",
                help_text="Préfixe numérique pour les références de dossiers (ex: 175)",
            ),
        ),
        migrations.AddField(
            model_name="configurationetude",
            name="dossier_initiales_huissier",
            field=models.CharField(
                max_length=10,
                default="MAB",
                verbose_name="Initiales de l'huissier",
                help_text="Suffixe pour les références de dossiers (ex: MAB)",
            ),
        ),
    ]
