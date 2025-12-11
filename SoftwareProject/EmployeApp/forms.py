from django import forms
from .models import Employe

class EmployeForm(forms.ModelForm):
    mot_de_passe = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Employe
        fields = [
            'nom', 'prenom', 'role', 'login', 'mot_de_passe',
            'email', 'telephone', 'date_embauche', 'service'
        ]
        widgets = {
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
