from django.urls import path
from . import views

urlpatterns = [
    path('liste/', views.RendezVousListView.as_view(), name='liste_rdv'),
    path('ajouter/', views.RendezVousCreateView.as_view(), name='ajouter_rdv'),
    path('modifier/<int:pk>/', views.RendezVousUpdateView.as_view(), name='update_rdv'), 
]
