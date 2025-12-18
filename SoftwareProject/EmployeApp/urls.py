from django.urls import path
from . import views

urlpatterns = [
    path('ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('liste/', views.liste_employes, name='liste_employes'),
]


# from django.urls import path
# from . import views

# app_name = 'employee'

# urlpatterns = [
#     path('login/', views.login_view, name='login'),
#     path('logout/', views.logout_view, name='logout'),
#     path('dashboard/', views.dashboard_redirect, name='dashboard'),
#     path('tache/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
#     path('taches/reorder/', views.reorder_tasks, name='reorder_tasks'),
#     # Doctor CRUD for tasks
#     path('doctor/taches/', views.doctor_list_taches, name='doctor_list_taches'),
#     path('doctor/taches/create/', views.doctor_create_tache, name='doctor_create_tache'),
#     path('doctor/taches/<int:pk>/edit/', views.doctor_edit_tache, name='doctor_edit_tache'),
#     path('doctor/taches/<int:pk>/delete/', views.doctor_delete_tache, name='doctor_delete_tache'),
#     path('preferences/notifications/', views.notification_preferences, name='notification_preferences'),
# ]
