from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('EmployeApp', '0001_initial'),
        ('GestionTacheApp', '0003_task_notes_attachments'),
    ]

    operations = [
        migrations.CreateModel(
            name='TacheCollaboration',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('accepted', 'Acceptée'), ('declined', 'Refusée')], default='pending', max_length=10)),
                ('invited_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('collaborator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_collaborations', to='EmployeApp.employe')),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaborations', to='GestionTacheApp.tache')),
            ],
            options={'ordering': ['-invited_at']},
        ),
        migrations.AlterUniqueTogether(
            name='tachecollaboration',
            unique_together={('tache', 'collaborator')},
        ),
        # Legacy fields collaborator/collaboration_status may exist; safe to ignore removal
    ]
