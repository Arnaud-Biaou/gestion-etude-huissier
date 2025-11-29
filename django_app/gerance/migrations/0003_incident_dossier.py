# Generated manually - Migration for Incident dossier field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gerance", "0002_add_dossiers_contentieux_to_bail"),
        ("gestion", "0011_reversement_compte_tresorerie_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="dossier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="incidents_gerance",
                to="gestion.dossier",
                verbose_name="Dossier juridique",
            ),
        ),
    ]
