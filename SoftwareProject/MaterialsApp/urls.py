from django.urls import path
from . import views

urlpatterns = [
# Avant
# path('elements.html', views.elements, name='elements'),

# Après
    path('materiel/', views.liste_materiels, name='liste_materiels'),
    path('ajouter/', views.ajouter_materiel, name='ajouter_materiel'),
    path('materiel/<int:pk>/modifier/', views.modifier_materiel, name='modifier_materiel'),
    path('supprimer/<int:pk>/', views.supprimer_materiel, name='supprimer_materiel'),
    path('detail/<int:pk>/', views.materiel_detail, name='materiel_detail'),
    path('materiel/<int:pk>/maintenance/', views.mettre_en_maintenance, name='mettre_en_maintenance'),
path('materiel/<int:pk>/remettre_service/', views.remettre_en_service, name='remettre_en_service'),
path('materiel/<int:pk>/reparer/', views.reparer_materiel, name='reparer_materiel'),
path('materiel/<int:pk>/retour_pret/', views.retour_pret, name='retour_pret'),

]
