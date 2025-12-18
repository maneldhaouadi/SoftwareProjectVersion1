from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('EmployeApp', '0001_initial'),
        ('GestionTacheApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tache',
            name='collaborator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collaborations', to='EmployeApp.employe'),
        ),
        migrations.AddField(
            model_name='tache',
            name='collaboration_status',
            field=models.CharField(choices=[('none', 'Aucun'), ('pending', 'En attente'), ('accepted', 'Acceptée'), ('declined', 'Refusée')], default='none', max_length=10),
        ),
    ]
