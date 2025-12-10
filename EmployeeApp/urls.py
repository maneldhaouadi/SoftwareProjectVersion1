from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('tache/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
    path('taches/reorder/', views.reorder_tasks, name='reorder_tasks'),
    # Doctor CRUD for tasks
    path('doctor/taches/', views.doctor_list_taches, name='doctor_list_taches'),
    path('doctor/taches/create/', views.doctor_create_tache, name='doctor_create_tache'),
    path('doctor/taches/<int:pk>/edit/', views.doctor_edit_tache, name='doctor_edit_tache'),
    path('doctor/taches/<int:pk>/delete/', views.doctor_delete_tache, name='doctor_delete_tache'),
    path('taches/<int:pk>/notification/', views.edit_task_notification, name='edit_task_notification'),
    path('taches/<int:pk>/collaborators/', views.edit_task_collaborators, name='edit_task_collaborators'),
    path('tache/<int:pk>/', views.task_detail, name='task_detail'),
    path('tache/<int:pk>/upload/', views.upload_task_document, name='upload_task_document'),
    path('tache/<int:pk>/note/', views.add_task_note, name='add_task_note'),
    path('preferences/notifications/', views.notification_preferences, name='notification_preferences'),
]
