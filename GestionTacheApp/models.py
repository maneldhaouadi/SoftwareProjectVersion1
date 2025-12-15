from django.db import models
from EmployeeApp.models import Employee

# Create your models here.
class Tache(models.Model):
    idTache = models.AutoField(primary_key=True)
    description =  models.TextField(max_length=1000)
    date_echeance = models.DateField()
    employee = models.ForeignKey(Employee, on_delete=models.RESTRICT, related_name='taches')
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
