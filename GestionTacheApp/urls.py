from django.urls import path
from . import views

# Keep the same namespace as before so templates using 'employee:...' still work
app_name = 'employee'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('tache/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
    # If you have a reorder view, uncomment the next line
    # path('taches/reorder/', views.reorder_tasks, name='reorder_tasks'),

    # Doctor CRUD for tasks
    path('doctor/taches/', views.doctor_list_taches, name='doctor_list_taches'),
    path('doctor/taches/create/', views.doctor_create_tache, name='doctor_create_tache'),
    path('doctor/taches/<int:pk>/edit/', views.doctor_edit_tache, name='doctor_edit_tache'),
    path('doctor/taches/<int:pk>/delete/', views.doctor_delete_tache, name='doctor_delete_tache'),
    path('preferences/notifications/', views.notification_preferences, name='notification_preferences'),
]
