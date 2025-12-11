from django.db import models
from django.utils import timezone
from datetime import timedelta

class Fournisseur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Emplacement(models.Model):
    batiment = models.CharField(max_length=50)
    etage = models.CharField(max_length=10, blank=True)
    salle = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.batiment} - {self.etage} - {self.salle}"

class EtatMateriel(models.TextChoices):
    EN_SERVICE = 'EN_SERVICE', 'EN_SERVICE'
    EN_MAINTENANCE = 'EN_MAINTENANCE', 'EN_MAINTENANCE'
    HORS_SERVICE = 'HORS_SERVICE', 'HORS_SERVICE'
    EN_PRET = 'EN_PRET', 'EN_PRET'

class MaterielMedical(models.Model):
    IdMaterial = models.AutoField(primary_key=True)
    Nom = models.CharField(max_length=100)
    Type = models.CharField(max_length=50)
    Reference = models.CharField(max_length=50)
    Etat = models.CharField(
        max_length=20,
        choices=EtatMateriel.choices,
        default=EtatMateriel.EN_SERVICE
    )
    Quantite = models.PositiveIntegerField()
    PrixAchat = models.DecimalField(max_digits=10, decimal_places=2)
    DateAcquisition = models.DateField()
    DateExpiration = models.DateField()
    QuantiteInitiale = models.PositiveIntegerField(null=True, blank=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True)
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.Nom} ({self.Etat})"

    def save(self, *args, **kwargs):
        if not self.QuantiteInitiale:
            self.QuantiteInitiale = self.Quantite
        super().save(*args, **kwargs)

    @property
    def est_bientot_expire(self):
        return self.DateExpiration <= timezone.now().date() + timedelta(days=30)

    @property
    def est_expire(self):
        return self.DateExpiration < timezone.now().date()

class HistoriqueMateriel(models.Model):
    ACTION_CHOICES = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('SUPPRESSION', 'Suppression'),
        ('MAINTENANCE', 'Maintenance'),
        ('PRET', 'Mise en prêt'),
        ('RETOUR', 'Retour de prêt'),
    ]
    
    materiel = models.ForeignKey(MaterielMedical, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    # On enlève le champ utilisateur et IP

    def __str__(self):
        return f"{self.materiel} - {self.action}"

class Alerte(models.Model):
    TYPE_ALERTE_CHOICES = [
        ('MAINTENANCE', 'Maintenance requise'),
        ('STOCK', 'Stock bas'),
        ('EXPIRE', 'Expiration'),
        ('PANNE', 'Panne'),
        ('AUTRE', 'Autre'),
    ]
    PRIORITE_CHOICES = [
        ('HAUTE', 'Haute'),
        ('MOYENNE', 'Moyenne'),
        ('BASSE', 'Basse'),
    ]
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EN_COURS', 'En cours de traitement'),
        ('RESOLUE', 'Résolue'),
    ]
    
    materiel = models.ForeignKey(MaterielMedical, on_delete=models.CASCADE)
    type_alerte = models.CharField(max_length=20, choices=TYPE_ALERTE_CHOICES)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='MOYENNE')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='ACTIVE')
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.type_alerte} - {self.materiel.Nom}"
class Pret(models.Model):
    materiel = models.ForeignKey(MaterielMedical, on_delete=models.CASCADE)
    emprunteur = models.CharField(max_length=100)
    service = models.CharField(max_length=100)
    date_pret = models.DateField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    date_retour_reelle = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=[
        ('EN_COURS', 'En cours'),
        ('RETOURNE', 'Retourné'),
        ('RETARD', 'En retard'),
    ], default='EN_COURS')

    @property
    def jours_restants(self):
        if self.statut != 'EN_COURS' or self.date_retour_reelle:
            return 0
        today = timezone.now().date()
        if self.date_retour_prevue >= today:
            return (self.date_retour_prevue - today).days
        return 0
    
    @property
    def jours_retard(self):
        if self.statut != 'EN_COURS' or self.date_retour_reelle:
            return 0
        today = timezone.now().date()
        if self.date_retour_prevue < today:
            return (today - self.date_retour_prevue).days
        return 0
    
    @property
    def duree_pret(self):
        if self.date_retour_reelle and self.date_pret:
            return (self.date_retour_reelle - self.date_pret).days
        return 0
    
    @property
    def date_emprunt(self):
        return self.date_pret
    
    def save(self, *args, **kwargs):
        # Mise à jour automatique du statut
        if self.date_retour_reelle:
            self.statut = 'RETOURNE'
        elif self.jours_retard > 0:
            self.statut = 'RETARD'
        else:
            self.statut = 'EN_COURS'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.materiel.Nom} - {self.emprunteur}"

    # Supprimer la deuxième définition de est_en_retard
