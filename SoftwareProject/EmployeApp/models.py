from django.db import models

class Employe(models.Model):
    ROLE_CHOICES = [
        ('medecin', 'Médecin'),
        ('infirmiere', 'Infirmière'),
        ('administrateur', 'Administrateur'),
    ]

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    login = models.CharField(max_length=50, unique=True)
    mot_de_passe = models.CharField(max_length=128)  # tu peux hasher avec make_password
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    date_embauche = models.DateField()
    service = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.role})"
