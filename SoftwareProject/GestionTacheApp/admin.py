from django.contrib import admin
from .models import Tache

# Site branding
admin.site.site_header = "Gestion des Tâches Admin"
admin.site.site_title = "Dashboard de Gestion des Tâches"
admin.site.index_title = "Bienvenue dans le panneau d'administration de Gestion des Tâches"


@admin.action(description="Marquer la(les) tâche(s) comme terminée(s)")
def mark_as_done(modeladmin, request, queryset):
    queryset.update(statut='Done')


@admin.action(description="Remettre la(les) tâche(s) en attente")
def mark_as_pending(modeladmin, request, queryset):
    queryset.update(statut='Pending')


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ('idTache', 'short_description', 'employee', 'date_echeance', 'statut')
    list_filter = ('statut', 'date_echeance', 'employee')
    search_fields = ('description', 'employee__nom', 'employee__prenom')
    readonly_fields = ('idTache',)
    date_hierarchy = 'date_echeance'
    actions = (mark_as_done, mark_as_pending)

    fieldsets = (
        (None, {
            'fields': ('idTache', 'description', 'employee', 'date_echeance', 'statut')
        }),
    )

    def short_description(self, obj):
        return (obj.description[:60] + '...') if len(obj.description) > 60 else obj.description
    short_description.short_description = 'Description'

