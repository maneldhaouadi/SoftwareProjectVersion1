from django.urls import path
from . import views

urlpatterns = [
    path('ajouter/', views.ajouter_patient, name='ajouter_patient'),
    path('liste/', views.liste_patients, name='liste_patients'),
]
