from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GestionTacheApp', '0005_merge_two_0004'),
    ]

    operations = [
        migrations.AddField(
            model_name='tachecollaboration',
            name='collab_statut',
            field=models.CharField(choices=[('Pending', 'En attente'), ('Done', 'Terminée')], default='Pending', max_length=20),
        ),
    ]
