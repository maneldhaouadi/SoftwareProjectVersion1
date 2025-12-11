from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .models import MaterielMedical, Fournisseur, Emplacement, Pret

class MaterielMedicalForm(forms.ModelForm):
    reference_number = forms.IntegerField(
        label="Numéro de référence",
        min_value=1,
        help_text="Saisissez uniquement des chiffres (ex: 12345)",
        widget=forms.NumberInput(attrs={
            'placeholder': '12345',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = MaterielMedical
        fields = [
            'Nom', 'Type', 'Etat', 'Quantite', 
            'PrixAchat', 'DateAcquisition', 'DateExpiration',
            'fournisseur', 'emplacement'
        ]
        widgets = {
            'Nom': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom du matériel'
            }),
            'Type': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Type de matériel'
            }),
            'Etat': forms.Select(attrs={
                'class': 'form-control'
            }),
            'Quantite': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Quantité', 
                'min': '1'
            }),
            'PrixAchat': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Prix d\'achat (€)', 
                'step': '0.01', 
                'min': '0'
            }),
            'DateAcquisition': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'readonly': True
            }),
            'DateExpiration': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'readonly': True
            }),
            'fournisseur': forms.Select(attrs={
                'class': 'form-control'
            }),
            'emplacement': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        error_messages = {
            'Nom': {'required': 'Ce champ doit être rempli'},
            'Type': {'required': 'Ce champ doit être rempli'},
            'Etat': {'required': 'Ce champ doit être rempli'},
            'Quantite': {'required': 'Ce champ doit être rempli'},
            'PrixAchat': {'required': 'Ce champ doit être rempli'},
            'DateAcquisition': {'required': 'Ce champ doit être rempli'},
            'DateExpiration': {'required': 'Ce champ doit être rempli'},
        }

    def clean_DateAcquisition(self):
        date_acquisition = self.cleaned_data.get('DateAcquisition')
        if date_acquisition and date_acquisition > date.today():
            raise ValidationError("La date d'acquisition ne peut pas être supérieure à la date d'aujourd'hui.")
        return date_acquisition
    
    def clean_DateExpiration(self):
        date_expiration = self.cleaned_data.get('DateExpiration')
        if date_expiration and date_expiration < date.today():
            raise ValidationError("La date d'expiration ne peut pas être dans le passé.")
        return date_expiration

    def clean_reference_number(self):
        ref_number = self.cleaned_data.get('reference_number')
        if ref_number is not None:
            full_reference = f"REF-{ref_number}"
            
            # Vérifier si la référence existe déjà pour un autre matériel
            if self.instance and self.instance.pk:
                if MaterielMedical.objects.filter(Reference=full_reference).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Cette référence existe déjà.')
            else:
                if MaterielMedical.objects.filter(Reference=full_reference).exists():
                    raise ValidationError('Cette référence existe déjà.')
        
        return ref_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remplir les choix des fournisseurs et emplacements
        self.fields['fournisseur'].queryset = Fournisseur.objects.all().order_by('nom')
        self.fields['emplacement'].queryset = Emplacement.objects.all().order_by('batiment', 'etage', 'salle')
        
        if self.instance and self.instance.pk:
            ref_value = self.instance.Reference
            if ref_value and ref_value.startswith('REF-'):
                try:
                    number_part = ref_value.replace('REF-', '')
                    self.fields['reference_number'].initial = int(number_part)
                except ValueError:
                    pass
            
            # S'assurer que les dates sont initialisées même si non présentes dans les données
            if not self.data:  # Si pas de données POST (mode affichage initial)
                if self.instance.DateAcquisition:
                    self.fields['DateAcquisition'].initial = self.instance.DateAcquisition
                if self.instance.DateExpiration:
                    self.fields['DateExpiration'].initial = self.instance.DateExpiration
            
            # Rendre les champs de date en lecture seule en mode modification
            self.fields['DateAcquisition'].widget.attrs['readonly'] = True
            self.fields['DateExpiration'].widget.attrs['readonly'] = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        ref_number = self.cleaned_data.get('reference_number')
        
        if ref_number is not None:
            instance.Reference = f"REF-{ref_number}"
        
        if commit:
            instance.save()
        return instance

class PretForm(forms.ModelForm):
    SERVICE_CHOICES = [
        ('', 'Sélectionnez un service'),
        ('URGENCES', 'Urgences'),
        ('CARDIOLOGIE', 'Cardiologie'),
        ('RADIOLOGIE', 'Radiologie'),
        ('CHIRURGIE', 'Chirurgie'),
        ('PEDIATRIE', 'Pédiatrie'),
        ('AUTRE', 'Autre'),
    ]
    
    service = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Pret
        fields = ['materiel', 'emprunteur', 'service', 'date_retour_prevue', 'notes']
        widgets = {
            'materiel': forms.Select(attrs={
                'class': 'form-control'
            }),
            'emprunteur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'emprunteur'
            }),
            'date_retour_prevue': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes optionnelles'
            }),
        }
        labels = {
            'materiel': 'Matériel à prêter',
            'emprunteur': 'Nom de l\'emprunteur',
            'service': 'Service/Département',
            'date_retour_prevue': 'Date de retour prévue',
            'notes': 'Notes (optionnel)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les matériels disponibles (en service)
        self.fields['materiel'].queryset = MaterielMedical.objects.filter(
            Etat='EN_SERVICE'
        ).order_by('Nom')

    def clean_date_retour_prevue(self):
        date_retour = self.cleaned_data.get('date_retour_prevue')
        if date_retour and date_retour < date.today():
            raise ValidationError("La date de retour ne peut pas être dans le passé.")
        return date_retour
    
class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'telephone', 'email', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du fournisseur'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Personne à contacter'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'adresse@email.com'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
        }
        labels = {
            'nom': 'Nom du fournisseur',
            'contact': 'Personne à contacter',
            'telephone': 'Téléphone',
            'email': 'Adresse email',
            'adresse': 'Adresse'
        }

class EmplacementForm(forms.ModelForm):
    class Meta:
        model = Emplacement
        fields = ['batiment', 'etage', 'salle', 'description']
        widgets = {
            'batiment': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du bâtiment'
            }),
            'etage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Étage (optionnel)'
            }),
            'salle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro/Nom de salle'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (optionnel)'
            }),
        }
        labels = {
            'batiment': 'Bâtiment',
            'etage': 'Étage',
            'salle': 'Salle',
            'description': 'Description'
        }