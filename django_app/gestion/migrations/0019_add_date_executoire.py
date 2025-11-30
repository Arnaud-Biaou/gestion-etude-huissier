# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0018_add_dossier_indexes'),
    ]

    operations = [
        # Modifier titre_executoire_type pour utiliser des choices
        migrations.AlterField(
            model_name='dossier',
            name='titre_executoire_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('jugement', 'Décision juridictionnelle'),
                    ('ordonnance', 'Ordonnance'),
                    ('acte_notarie', 'Acte notarié'),
                    ('pv_conciliation', 'PV de conciliation'),
                    ('protet', 'Protêt'),
                    ('autre', 'Autre'),
                ],
                max_length=20,
                verbose_name='Type de titre exécutoire',
            ),
        ),
        # Ajouter le champ date_executoire
        migrations.AddField(
            model_name='dossier',
            name='date_executoire',
            field=models.DateField(
                blank=True,
                help_text="Date à laquelle le titre devient exécutoire (après délai d'appel, signification, etc.)",
                null=True,
                verbose_name="Date d'exécutorité",
            ),
        ),
    ]
