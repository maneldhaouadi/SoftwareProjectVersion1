from django.contrib import admin
from .models import Employe

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'role', 'login', 'email', 'dateEmbauche')
    search_fields = ('nom', 'prenom', 'login', 'email')
    list_filter = ('role', 'dateEmbauche')