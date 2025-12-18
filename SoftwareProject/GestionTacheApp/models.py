from django.db import models
from EmployeApp.models import Employe

# Create your models here.
class Tache(models.Model):
    idTache = models.AutoField(primary_key=True)
    description =  models.TextField(max_length=1000)
    date_echeance = models.DateField()
    employee = models.ForeignKey(Employe, on_delete=models.RESTRICT, related_name='taches')
    STATUTS = [
        ('Pending', 'En attente'),
        ('Done', 'Terminée'),
    ]
    statut = models.CharField(max_length=20, choices=STATUTS, default='Pending')
    # Manual priority order per employee
    order = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.description + " pour " + str(self.date_echeance)
    def ajouterTache(self):
        self.save()
    def supprimerTache(self):
        self.delete()
    def modifierTache(self, nouvelle_description, nouvelle_date_echeance):
        self.description = nouvelle_description
        self.date_echeance = nouvelle_date_echeance
        self.save()

    def marquer_terminee(self):
        self.statut = 'Done'
        self.save()

    def marquer_en_attente(self):
        self.statut = 'Pending'
        self.save()
    
    
    class Meta:
        ordering = ['employee', 'order', 'date_echeance']


class TacheCollaboration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('declined', 'Refusée'),
    ]
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='collaborations')
    collaborator = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='task_collaborations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    # Nurse/doctor collaborator's own completion status; independent of the main task status
    COLLAB_STATUTS = [
        ('Pending', 'En attente'),
        ('Done', 'Terminée'),
    ]
    collab_statut = models.CharField(max_length=20, choices=COLLAB_STATUTS, default='Pending')
    invited_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tache', 'collaborator')
        ordering = ['-invited_at']


class TacheNote(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(Employe, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class TacheAttachment(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(Employe, on_delete=models.CASCADE)
    file = models.FileField(upload_to='taches/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
