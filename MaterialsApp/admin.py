from django.contrib import admin

# Register your models here.
from .models import MaterielMedical

@admin.register(MaterielMedical)
class MaterielMedicalAdmin(admin.ModelAdmin):
    list_display = ('IdMaterial', 'Nom', 'Type', 'Reference', 'Etat', 'Quantite', 'PrixAchat', 'DateAcquisition', 'DateExpiration')
    list_filter = ('Type', 'Etat')
    search_fields = ('Nom', 'Reference')
