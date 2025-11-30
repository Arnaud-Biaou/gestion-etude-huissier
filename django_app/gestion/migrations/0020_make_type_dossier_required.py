# Generated manually

from django.db import migrations, models


def fill_empty_type_dossier(apps, schema_editor):
    """Remplit les type_dossier vides avec 'recouvrement'"""
    Dossier = apps.get_model('gestion', 'Dossier')
    Dossier.objects.filter(type_dossier='').update(type_dossier='recouvrement')
    Dossier.objects.filter(type_dossier__isnull=True).update(type_dossier='recouvrement')


def reverse_fill(apps, schema_editor):
    """Opération inverse (ne fait rien, on ne peut pas savoir quels étaient vides)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0019_add_date_executoire'),
    ]

    operations = [
        # 1. D'abord remplir les valeurs vides
        migrations.RunPython(fill_empty_type_dossier, reverse_fill),

        # 2. Ensuite modifier le champ pour le rendre obligatoire avec default
        migrations.AlterField(
            model_name='dossier',
            name='type_dossier',
            field=models.CharField(
                choices=[
                    ('recouvrement', 'Recouvrement'),
                    ('expulsion', 'Expulsion'),
                    ('constat', 'Constat'),
                    ('signification', 'Signification'),
                    ('saisie', 'Saisie'),
                    ('autre', 'Autre'),
                ],
                default='recouvrement',
                max_length=20,
                verbose_name='Type de dossier',
            ),
        ),
    ]
