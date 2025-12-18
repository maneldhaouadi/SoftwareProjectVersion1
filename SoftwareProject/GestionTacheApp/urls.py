from django.urls import path
from . import views

app_name = 'tache'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('tache/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
    path('tache/<int:pk>/update-collab-status/', views.update_collab_status, name='update_collab_status'),
    path('taches/reorder/', views.reorder_tasks, name='reorder_tasks'),
    # Doctor CRUD for tasks
    path('doctor/taches/', views.doctor_list_taches, name='doctor_list_taches'),
    path('doctor/taches/create/', views.doctor_create_tache, name='doctor_create_tache'),
    path('doctor/taches/<int:pk>/edit/', views.doctor_edit_tache, name='doctor_edit_tache'),
    path('doctor/taches/<int:pk>/delete/', views.doctor_delete_tache, name='doctor_delete_tache'),
    path('doctor/taches/<int:pk>/choose-collaborator/', views.choose_collaborator, name='choose_collaborator'),
    path('doctor/taches/<int:pk>/notes-files/', views.task_notes_files, name='task_notes_files'),
    path('preferences/notifications/', views.notification_preferences, name='notification_preferences'),
    # Collaboration
    path('collab/invitations/', views.collab_invitations, name='collab_invitations'),
    path('collab/invitations/<int:pk>/accept/', views.collab_accept, name='collab_accept'),
    path('collab/invitations/<int:pk>/decline/', views.collab_decline, name='collab_decline'),
    # AI assistance for ordering
    path('doctor/taches/ai-suggest/', views.ai_suggest_order, name='ai_suggest_order'),
    path('doctor/taches/ai-apply/', views.ai_apply_order, name='ai_apply_order'),
]
