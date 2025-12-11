from django.urls import path
from . import views

urlpatterns = [
    path('ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('liste/', views.liste_employes, name='liste_employes'),
]
