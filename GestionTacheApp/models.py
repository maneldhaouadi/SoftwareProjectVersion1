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
    # Per-task notification interval in hours
    notify_interval_hours = models.PositiveIntegerField(default=24)
    # Collaboration: additional employees participating in this task
    collaborators = models.ManyToManyField(Employee, related_name='collab_taches', blank=True)
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


class TacheDocument(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='tache_documents/')
    uploader = models.ForeignKey(Employee, on_delete=models.RESTRICT, related_name='uploaded_task_documents')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for #{self.tache_id} by {self.uploader_id} at {self.created_at}"


class TacheNote(models.Model):
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    author = models.ForeignKey(Employee, on_delete=models.RESTRICT, related_name='task_notes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for #{self.tache_id} by {self.author_id} at {self.created_at}"
