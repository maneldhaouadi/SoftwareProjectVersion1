from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
	list_display = ('nom', 'prenom', 'service', 'role', 'dateEmbauche', 'email', 'telephone')
	search_fields = ('nom', 'prenom', 'service', 'email')
	list_filter = ('service', 'role')

