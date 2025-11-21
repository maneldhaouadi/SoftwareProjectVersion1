from django import forms
from .models import RendezVous
from PatientApp.models import Patient
from EmployeApp.models import Employe

class RendezVousForm(forms.ModelForm):
    # Liste déroulante pour les patients
    patient_id = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        label="Patient",
        empty_label="Sélectionner un patient",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Liste déroulante pour les médecins (filtrée par role)
    medecin_id = forms.ModelChoiceField(
        queryset=Employe.objects.filter(role='medecin'),  # utiliser la valeur exacte 'medecin'
        label="Médecin",
        empty_label="Sélectionner un médecin",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = RendezVous
        fields = ['patient_id', 'medecin_id', 'date_rdv', 'heure_rdv']
        widgets = {
            'date_rdv': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_rdv': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'medecin_id': 'Médecin',
            'date_rdv': 'Date du rendez-vous',
            'heure_rdv': 'Heure du rendez-vous',
            'statut': 'Statut du rendez-vous',
        }
