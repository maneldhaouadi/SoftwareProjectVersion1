from django.utils import timezone
from datetime import timedelta
from .models import Alerte, MaterielMedical, Pret

def generer_alertes_automatiques():
    """Génère les alertes automatiques"""
    today = timezone.now().date()
    
    # Supprimer uniquement les alertes automatiques non résolues
    # Utilisez les types qui existent dans votre modèle
    Alerte.objects.filter(
        resolved=False, 
        type_alerte__in=['EXPIRE', 'STOCK', 'RETARD', 'MAINTENANCE', 'PANNE']
    ).delete()
    
    # 1. Alertes pour expiration proche (30 jours)
    date_limite_expiration = today + timedelta(days=1)
    materiels_expiration = MaterielMedical.objects.filter(
        DateExpiration__lte=date_limite_expiration,
        DateExpiration__gte=today
    ).exclude(Etat='HORS_SERVICE')
    
    for materiel in materiels_expiration:
        jours_restants = (materiel.DateExpiration - today).days
        priorite = 'HAUTE' if jours_restants <= 7 else 'MOYENNE' if jours_restants <= 15 else 'BASSE'
        
        Alerte.objects.create(
            materiel=materiel,
            type_alerte='EXPIRE',
            message=f"⏰ {materiel.Nom} expire dans {jours_restants} jour(s) ({materiel.DateExpiration})",
            priorite=priorite
        )
    
    # 2. Alertes pour stock faible
    materiels_stock_faible = MaterielMedical.objects.filter(
        Quantite__lte=5,
        Quantite__gt=0,
        Etat='EN_SERVICE'
    )
    
    for materiel in materiels_stock_faible:
        priorite = 'HAUTE' if materiel.Quantite <= 2 else 'MOYENNE' if materiel.Quantite <= 5 else 'BASSE'
        
        Alerte.objects.create(
            materiel=materiel,
            type_alerte='STOCK',
            message=f"📦 Stock faible: {materiel.Nom} - {materiel.Quantite} unité(s) restante(s)",
            priorite=priorite
        )
    
    # 3. Alertes pour stocks épuisés
    materiels_stock_epuise = MaterielMedical.objects.filter(
        Quantite=0,
        Etat='EN_SERVICE'
    )
    
    for materiel in materiels_stock_epuise:
        Alerte.objects.create(
            materiel=materiel,
            type_alerte='STOCK',
            message=f"🚨 Stock épuisé: {materiel.Nom} - Réapprovisionnement urgent!",
            priorite='HAUTE'
        )
    
    # 4. Alertes pour prêts en retard
    prets_en_retard = Pret.objects.filter(
        date_retour_prevue__lt=today,
        statut='EN_COURS'
    )
    
    for pret in prets_en_retard:
        jours_retard = (today - pret.date_retour_prevue).days
        priorite = 'HAUTE' if jours_retard > 7 else 'MOYENNE'
        
        # Utilisez 'RETARD' si vous l'avez ajouté, sinon utilisez 'AUTRE'
        Alerte.objects.create(
            materiel=pret.materiel,
            type_alerte='RETARD',  # ou 'AUTRE' si vous ne voulez pas modifier le modèle
            message=f"⚠️ Prêt en retard: {pret.materiel.Nom} par {pret.emprunteur} ({jours_retard} jour(s) de retard)",
            priorite=priorite
        )
    
    # 5. Alertes pour matériels en maintenance
    materiels_en_maintenance = MaterielMedical.objects.filter(
        Etat='EN_MAINTENANCE'
    )
    
    for materiel in materiels_en_maintenance:
        Alerte.objects.create(
            materiel=materiel,
            type_alerte='MAINTENANCE',
            message=f"🔧 Matériel en maintenance: {materiel.Nom} nécessite un suivi",
            priorite='MOYENNE'
        )
    
    # 6. Optionnel : Alertes pour matériels hors service (si vous le souhaitez)
    materiels_hors_service = MaterielMedical.objects.filter(
        Etat='HORS_SERVICE'
    )
    
    for materiel in materiels_hors_service:
        Alerte.objects.create(
            materiel=materiel,
            type_alerte='PANNE',  # ou 'AUTRE'
            message=f"🛑 Matériel hors service: {materiel.Nom} doit être réparé ou remplacé",
            priorite='MOYENNE'
        )
    
    return f"Généré {Alerte.objects.filter(resolved=False).count()} alertes"
def get_statistiques():
    """Retourne les statistiques pour le dashboard"""
    today = timezone.now().date()
    
    stats = {
        'total_materiels': MaterielMedical.objects.count(),
        'materiels_service': MaterielMedical.objects.filter(Etat='EN_SERVICE').count(),
        'materiels_maintenance': MaterielMedical.objects.filter(Etat='EN_MAINTENANCE').count(),
        'materiels_pret': MaterielMedical.objects.filter(Etat='EN_PRET').count(),
        'materiels_hors_service': MaterielMedical.objects.filter(Etat='HORS_SERVICE').count(),
        'alertes_actives': Alerte.objects.filter(resolved=False).count(),
        'prets_en_cours': Pret.objects.filter(statut='EN_COURS').count(),
        'prets_en_retard': Pret.objects.filter(statut='EN_COURS', date_retour_prevue__lt=today).count(),
        'materiels_expires': MaterielMedical.objects.filter(DateExpiration__lt=today).count(),
        'materiels_bientot_expires': MaterielMedical.objects.filter(
            DateExpiration__lte=today + timedelta(days=30),
            DateExpiration__gte=today
        ).count(),
    }
    
    # Coût total
    from django.db.models import Sum
    cout_total = MaterielMedical.objects.aggregate(total=Sum('PrixAchat'))
    stats['cout_total'] = cout_total['total'] or 0
    
    return stats