from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('EmployeApp', '0001_initial'),
        ('GestionTacheApp', '0002_tache_collab_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='TacheNote',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EmployeApp.employe')),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='GestionTacheApp.tache')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='TacheAttachment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='taches/%Y/%m/%d/')),
                ('original_name', models.CharField(max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='GestionTacheApp.tache')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EmployeApp.employe')),
            ],
            options={'ordering': ['-uploaded_at']},
        ),
    ]
