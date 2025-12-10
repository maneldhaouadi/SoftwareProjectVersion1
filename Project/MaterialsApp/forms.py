# forms.py
from django import forms
from .models import MaterielMedical

class MaterielMedicalForm(forms.ModelForm):
    class Meta:
        model = MaterielMedical
        fields = [
            'Nom', 'Type', 'Reference', 'Etat',
            'Quantite', 'PrixAchat', 'DateAcquisition', 'DateExpiration'
        ]
        widgets = {
            'DateAcquisition': forms.DateInput(attrs={'type': 'date'}),
            'DateExpiration': forms.DateInput(attrs={'type': 'date'}),
        }
