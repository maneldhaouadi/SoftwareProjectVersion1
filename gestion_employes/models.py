# gestion_employes/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password

class Employe(models.Model):
    ROLE_CHOICES = [
        ('MEDECIN', 'Médecin'),
        ('INFIRMIER', 'Infirmier'),
        ('ADMIN', 'Administratif'),
        ('TECHNICIEN', 'Technicien'),
        ('AUTRE', 'Autre'),
    ]

    ETAT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('CONGE', 'En congé'),
        ('SUSPENSION', 'Suspendu'),
    ]




    nom = models.CharField("Nom", max_length=100)
    prenom = models.CharField("Prénom", max_length=100)
    role = models.CharField("Rôle", max_length=20, choices=ROLE_CHOICES, default='AUTRE')
    login = models.CharField("Login", max_length=50, unique=True)
    motDePasse = models.CharField("Mot de passe", max_length=256)
    email = models.EmailField("Email", unique=True)

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Format: '+999999999'.")
    telephone = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    dateEmbauche = models.DateField("Date d'embauche")

    photo = models.ImageField("Photo", upload_to='employes/photos/', blank=True, null=True)
    etat = models.CharField("État", max_length=20, choices=ETAT_CHOICES, default='ACTIF')

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.get_role_display()}"

    # MÉTHODES OBLIGATOIRES POUR LA CONNEXION
    def set_password(self, raw_password):
        self.motDePasse = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.motDePasse)

    # Protection automatique : si quelqu’un sauve un mot de passe en clair → on le hashe
    def save(self, *args, **kwargs):
        if self.motDePasse and '$' not in self.motDePasse:
            self.set_password(self.motDePasse)
        super().save(*args, **kwargs)