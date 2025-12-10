from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_employes, name='liste_employes'),
    path('ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('modifier/<int:id>/', views.modifier_employe, name='modifier_employe'),
    path('supprimer/<int:id>/', views.supprimer_employe, name='supprimer_employe'),
    path('detail/<int:id>/', views.detail_employe, name='detail_employe'),
    path('export-pdf/', views.export_pdf_employes, name='export_pdf_employes'),
    path('export-excel/', views.export_excel_employes, name='export_excel_employes'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]