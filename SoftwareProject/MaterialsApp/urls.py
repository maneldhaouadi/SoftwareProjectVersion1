from django.urls import path
from . import views

urlpatterns = [
    # URLs existantes
    path('materiel/', views.liste_materiels, name='liste_materiels'),
    path('ajouter/', views.ajouter_materiel, name='ajouter_materiel'),
    path('materiel/<int:pk>/modifier/', views.modifier_materiel, name='modifier_materiel'),
    path('supprimer/<int:pk>/', views.supprimer_materiel, name='supprimer_materiel'),
    path('detail/<int:pk>/', views.materiel_detail, name='materiel_detail'),
    path('materiel/<int:pk>/maintenance/', views.mettre_en_maintenance, name='mettre_en_maintenance'),
    path('materiel/<int:pk>/remettre_service/', views.remettre_en_service, name='remettre_en_service'),
    path('materiel/<int:pk>/reparer/', views.reparer_materiel, name='reparer_materiel'),
    path('materiel/<int:pk>/retour_pret/', views.retour_pret_old, name='retour_pret'),
    
    # Nouvelles URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alertes/', views.alertes, name='alertes'),
    path('alertes/<int:alerte_id>/resoudre/', views.resoudre_alerte, name='resoudre_alerte'),
    path('alertes/<int:alerte_id>/supprimer/', views.supprimer_alerte, name='supprimer_alerte'),
    path('alertes/export/', views.export_alertes, name='export_alertes'),
    # URLs pour la gestion des prêts
    path('prets/', views.gestion_prets, name='gestion_prets'),
    path('prets/<int:pret_id>/retourner/', views.retourner_pret, name='retourner_pret'),
    path('prets/<int:pret_id>/prolonger/', views.prolonger_pret, name='prolonger_pret'),
    path('prets/<int:pret_id>/', views.details_pret, name='details_pret'),
    path('prets/export/', views.export_prets, name='export_prets'),
]
