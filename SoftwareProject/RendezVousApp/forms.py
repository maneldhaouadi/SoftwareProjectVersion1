from django import forms
from .models import RendezVous

class RendezVousForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = ['patient_id', 'medecin_id', 'date_rdv', 'heure_rdv','statut']
        widgets = {
            'date_rdv': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_rdv': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'patient_id': 'Patient',
            'medecin_id': 'Médecin',
            'date_rdv': 'Date du rendez-vous',
            'heure_rdv': 'Heure du rendez-vous',
            'statut': 'Statut du rendez-vous',
        }
