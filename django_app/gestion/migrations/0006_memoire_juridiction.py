# Generated migration to add juridiction field to Memoire

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0002_juridiction_hierarchie'),
        ('gestion', '0005_permission_role_adresseipautorisee_adresseipbloquee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='memoire',
            name='juridiction',
            field=models.ForeignKey(
                blank=True,
                help_text='Juridiction pour generation des signatures Requisition/Executoire',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='memoires',
                to='parametres.juridiction',
                verbose_name='Juridiction requerante'
            ),
        ),
    ]
