from django.urls import path
from . import views

urlpatterns = [
    path('liste/', views.RendezVousListView.as_view(), name='liste_rdv'),
    path('ajouter/', views.RendezVousCreateView.as_view(), name='ajouter_rdv'),
    path('modifier/<int:pk>/', views.RendezVousUpdateView.as_view(), name='update_rdv'),
    path('annuler/<int:rdv_id>/', views.annuler_rdv, name='annuler_rdv'),
    path('historique/', views.RendezVousHistoriqueListView.as_view(), name='historique_rdv'),
    path('historiqueMedecin/<int:medecin_id>/', views.historique_medecin, name='historique_medecin'),


]
