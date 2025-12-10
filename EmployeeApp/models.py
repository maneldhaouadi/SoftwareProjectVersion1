from django.db import models
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError



def verify_email(email): 
    if email.split("@")[1] != "employee.tn":
        raise ValidationError("Email domain is not allowed")

# Create your models here.
class Employee(models.Model):
    nom =   models.CharField(
            max_length=50,
            validators=[RegexValidator(regex=r'^[a-zA-Z\s,]+$', message="nom ne peut contenir que des lettres, des espaces et des virgules.")]
    )
    prenom = models.CharField(
            max_length=50,
            validators=[RegexValidator(regex=r'^[a-zA-Z\s,]+$', message="prenom ne peut contenir que des lettres, des espaces et des virgules.")]
    )
    service = models.CharField(max_length=100)
    role = [
        ('Medecin', 'Medecin'),
        ('Infirmier', 'Infirmier'),
        ('Gestionnaire de Materiel', 'Gestionnaire de Materiel'),
    ]
    role = models.CharField(max_length=50, choices=role)
    dateEmbauche = models.DateField()
    login = models.CharField(max_length=100, primary_key=True)
    email = models.EmailField(max_length=100, validators=[verify_email])
    MotDePasse = models.CharField(max_length=100)
    telephone = models.CharField(max_length=8, validators=[RegexValidator(regex=r'^\d{8}$', message="Le numéro de téléphone doit contenir 8 chiffres.")])
    # Notification preferences for Medecin / Infirmier
    notification_enabled = models.BooleanField(default=True)
    # Interval in hours: notify about tasks due within the next N hours
    notification_interval_hours = models.PositiveIntegerField(default=24)


    def __str__(self):
        return self.nom + "-" + self.prenom + " - " + self.service + " - " + self.role

    def ajouter_employee(self):
        self.save()

    def supprimer_employee(self):
        self.delete()

    def update_employee(self, new_nom, new_prenom, new_service, new_role, new_dateEmbauche, new_login, new_email, new_MotDePasse, new_telephone):
        self.nom = new_nom
        self.prenom = new_prenom
        self.service = new_service
        self.role = new_role
        self.dateEmbauche = new_dateEmbauche
        self.login = new_login
        self.email = new_email
        self.MotDePasse = new_MotDePasse
        self.telephone = new_telephone
        self.save()