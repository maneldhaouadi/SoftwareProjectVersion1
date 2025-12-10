from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from django.http import JsonResponse, HttpResponse
import csv

from .models import MaterielMedical, Fournisseur, Emplacement, HistoriqueMateriel, Alerte, Pret
from .forms import MaterielMedicalForm, FournisseurForm, EmplacementForm, PretForm
from .utils import generer_alertes_automatiques, get_statistiques

# ==================== VUES EXISTANTES SIMPLIFIÉES ====================

def liste_materiels(request):
    type_filter = request.GET.get('type', '')
    etat_filter = request.GET.get('etat', '')
    search_query = request.GET.get('search', '')

    materiels = MaterielMedical.objects.exclude(Etat='HORS_SERVICE')

    if search_query:
        materiels = materiels.filter(Nom__icontains=search_query)
    if type_filter:
        materiels = materiels.filter(Type__icontains=type_filter)
    if etat_filter:
        materiels = materiels.filter(Etat__iexact=etat_filter)

    today = timezone.now().date()
    
    types = MaterielMedical.objects.exclude(Etat='HORS_SERVICE').values_list('Type', flat=True).distinct()
    
    materiels_hors_service = MaterielMedical.objects.filter(Etat='HORS_SERVICE')

    # Générer les alertes automatiques
    generer_alertes_automatiques()
    alertes_non_resolues = Alerte.objects.filter(resolved=False).count()

    context = {
        'materiels': materiels,
        'materiels_hors_service': materiels_hors_service,
        'today': today,
        'types': types,
        'selected_type': type_filter,
        'selected_etat': etat_filter,
        'search_query': search_query,
        'alertes_count': alertes_non_resolues,
    }
    return render(request, 'materiel/elements.html', context)

def ajouter_materiel(request):
    message_erreur = None

    if request.method == 'POST':
        form = MaterielMedicalForm(request.POST)

        if not all(request.POST.get(field) for field in request.POST if field != 'csrfmiddlewaretoken'):
            message_erreur = "Tous les champs du formulaire doivent être remplis."

        if form.is_valid() and message_erreur is None:
            ref_number = form.cleaned_data['reference_number']
            full_reference = f"REF-{ref_number}"

            if MaterielMedical.objects.filter(Reference=full_reference).exists():
                form.add_error('reference_number', 'Cette référence existe déjà.')
            else:
                materiel = form.save()
                
                # Enregistrer dans l'historique (sans utilisateur)
                HistoriqueMateriel.objects.create(
                    materiel=materiel,
                    action='CREATION',
                    details=f"Création du matériel {materiel.Nom}"
                )
                
                messages.success(request, f"Matériel {materiel.Nom} ajouté avec succès!")
                return redirect('liste_materiels')
    else:
        form = MaterielMedicalForm()

    return render(request, 'materiel/form_materiel.html', {
        'form': form,
        'message_erreur': message_erreur
    })

def modifier_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    ancien_etat = materiel.Etat

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['DateAcquisition'] = materiel.DateAcquisition.strftime('%Y-%m-%d') if materiel.DateAcquisition else ''
        post_data['DateExpiration'] = materiel.DateExpiration.strftime('%Y-%m-%d') if materiel.DateExpiration else ''

        form = MaterielMedicalForm(post_data, instance=materiel)
        if form.is_valid():
            ref_number = form.cleaned_data['reference_number']
            full_reference = f"REF-{ref_number}"
            
            if full_reference != materiel.Reference and MaterielMedical.objects.filter(Reference=full_reference).exists():
                form.add_error('reference_number', 'Cette référence existe déjà.')
                return render(request, 'materiel/form_materiel.html', {
                    'form': form,
                    'is_edit': True,
                    'materiel': materiel
                })
            else:
                materiel_modifie = form.save(commit=False)

                # Logique existante pour les états
                if ancien_etat != 'EN_PRET' and materiel_modifie.Etat == 'EN_PRET':
                    materiel_modifie.Quantite = max(materiel_modifie.Quantite - 1, 0)

                elif ancien_etat == 'EN_PRET' and materiel_modifie.Etat == 'EN_SERVICE':
                    materiel_modifie.Quantite = materiel_modifie.QuantiteInitiale

                if not materiel_modifie.QuantiteInitiale:
                    materiel_modifie.QuantiteInitiale = materiel_modifie.Quantite

                materiel_modifie.save()
                
                # Enregistrer dans l'historique (sans utilisateur)
                HistoriqueMateriel.objects.create(
                    materiel=materiel_modifie,
                    action='MODIFICATION',
                    details=f"Modification du matériel {materiel_modifie.Nom}"
                )
                
                messages.success(request, f"Matériel {materiel_modifie.Nom} modifié avec succès!")
                return redirect('liste_materiels')
    else:
        form = MaterielMedicalForm(instance=materiel)
    
    return render(request, 'materiel/form_materiel.html', {
        'form': form,
        'is_edit': True,
        'materiel': materiel
    })

def supprimer_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    if request.method == 'POST':
        # Enregistrer dans l'historique avant suppression
        HistoriqueMateriel.objects.create(
            materiel=materiel,
            action='SUPPRESSION',
            details=f"Suppression du matériel {materiel.Nom}"
        )
        
        materiel.delete()
        messages.success(request, f"Matériel {materiel.Nom} supprimé avec succès!")
        return redirect('liste_materiels')
    return render(request, 'materiel/confirmer_suppression.html', {'materiel': materiel})

# ==================== NOUVELLES FONCTIONNALITÉS SIMPLIFIÉES ====================

def dashboard(request):
    """Tableau de bord avec statistiques"""
    stats = get_statistiques()
    generer_alertes_automatiques()
    
    # Données pour les graphiques
    materiels_par_etat = list(MaterielMedical.objects.values('Etat').annotate(
        count=Count('IdMaterial')
    ))
    
    materiels_par_type = list(MaterielMedical.objects.values('Type').annotate(
        count=Count('IdMaterial')
    ).order_by('-count')[:10])
    
    # Récupérer TOUTES les alertes non résolues des 7 derniers jours
    date_limite = timezone.now() - timedelta(days=7)
    alertes_actives = Alerte.objects.filter(
        resolved=False, 
        date_creation__gte=date_limite
    ).order_by('-priorite', '-date_creation')[:10]
    
    prets_en_cours = Pret.objects.filter(statut='EN_COURS').select_related('materiel')[:10]
    
    # Récupérer les matériels avec statut EN_PRET
    materiels_en_pret = MaterielMedical.objects.filter(Etat='EN_PRET')
    
    # Pour chaque matériel en prêt, ajouter l'information du prêt actuel
    for materiel in materiels_en_pret:
        # Trouver le prêt actif (non retourné) pour ce matériel
        pret_actuel = Pret.objects.filter(
            materiel=materiel,
            statut='EN_COURS'
        ).order_by('-date_pret').first()
        
        # Ajouter l'information du prêt au matériel
        materiel.pret_actuel = pret_actuel
        
        # Calculer si le prêt est en retard
        if pret_actuel and pret_actuel.date_retour_prevue:
            materiel.pret_actuel.est_en_retard = pret_actuel.date_retour_prevue < timezone.now().date()
            if materiel.pret_actuel.est_en_retard:
                materiel.pret_actuel.jours_retard = (timezone.now().date() - pret_actuel.date_retour_prevue).days
    
    context = {
        'stats': stats,
        'materiels_par_etat': materiels_par_etat,
        'materiels_par_type': materiels_par_type,
        'alertes_recentes': alertes_actives,
        'prets_en_cours': prets_en_cours,
        'materiels_en_pret': materiels_en_pret,
    }
    
    # Mettre à jour les stats pour inclure les matériels en prêt
    stats['materiels_pret'] = materiels_en_pret.count()
    
    return render(request, 'materiel/dashboard.html', context)

def alertes(request):
    """Page de gestion des alertes avec filtres"""
    # Récupération des paramètres de filtrage
    type_filter = request.GET.get('type', '')
    statut_filter = request.GET.get('statut', '')
    priorite_filter = request.GET.get('priorite', '')
    search_query = request.GET.get('search', '')
    
    # CRÉATION AUTOMATIQUE DES ALERTES
    from datetime import date, timedelta
    from django.utils import timezone
    
    # 1. Alertes de MAINTENANCE pour les matériels EN_MAINTENANCE → STATUT EN_COURS
    materiels_en_maintenance = MaterielMedical.objects.filter(Etat='EN_MAINTENANCE')
    for materiel in materiels_en_maintenance:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='MAINTENANCE',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='MAINTENANCE',
                priorite='MOYENNE',
                statut='EN_COURS',  # Maintenance = En cours (déjà prise en charge)
                message=f"Maintenance en cours - {materiel.Nom} - Intervention programmée"
            )
    
    # 2. Alertes de PANNE pour les matériels HORS_SERVICE → STATUT ACTIVE (urgent)
    materiels_hors_service = MaterielMedical.objects.filter(Etat='HORS_SERVICE')
    for materiel in materiels_hors_service:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='PANNE',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='PANNE',
                priorite='HAUTE',
                statut='ACTIVE',  # Panne = Active (nécessite intervention urgente)
                message=f"PANNE - {materiel.Nom} - Matériel hors service nécessitant réparation urgente"
            )
    
    # 3. Alertes d'EXPIRATION pour les matériels expirés ou bientôt expirés
    aujourdhui = timezone.now().date()
    
    # Matériels expirés (URGENT) → STATUT ACTIVE
    materiels_expires = MaterielMedical.objects.filter(
        DateExpiration__lt=aujourdhui,
        Etat='EN_SERVICE'
    )
    for materiel in materiels_expires:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='EXPIRE',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='EXPIRE',
                priorite='HAUTE',
                statut='ACTIVE',  # Expiration = Active (action immédiate nécessaire)
                message=f"URGENT - {materiel.Nom} a expiré le {materiel.DateExpiration.strftime('%d/%m/%Y')} - Retirer du service"
            )
    
    # Matériels expirant dans moins de 30 jours (MOYENNE) → STATUT ACTIVE
    date_limite = aujourdhui + timedelta(days=30)
    materiels_bientot_expires = MaterielMedical.objects.filter(
        DateExpiration__range=[aujourdhui, date_limite],
        Etat='EN_SERVICE'
    )
    for materiel in materiels_bientot_expires:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='EXPIRE',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            jours_restants = (materiel.DateExpiration - aujourdhui).days
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='EXPIRE',
                priorite='MOYENNE',
                statut='ACTIVE',  # Expiration proche = Active (planification nécessaire)
                message=f"Expiration proche - {materiel.Nom} expire dans {jours_restants} jour(s) - Planifier le remplacement"
            )
    
    # 4. Alertes de STOCK pour les stocks bas
    # Stocks épuisés (URGENT) → STATUT ACTIVE
    stocks_epuises = MaterielMedical.objects.filter(
        Quantite=0,
        Etat='EN_SERVICE'
    )
    for materiel in stocks_epuises:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='STOCK',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='STOCK',
                priorite='HAUTE',
                statut='ACTIVE',  # Stock épuisé = Active (commande urgente)
                message=f"STOCK ÉPUISÉ - {materiel.Nom} - Commande urgente nécessaire - Risque de rupture"
            )
    
    # Stocks bas (MOYENNE) → STATUT ACTIVE
    stocks_bas = MaterielMedical.objects.filter(
        Quantite__lte=5,  # Moins de 5 unités
        Quantite__gt=0,
        Etat='EN_SERVICE'
    )
    for materiel in stocks_bas:
        alerte_existante = Alerte.objects.filter(
            materiel=materiel,
            type_alerte='STOCK',
            statut__in=['ACTIVE', 'EN_COURS']
        ).exists()
        if not alerte_existante:
            Alerte.objects.create(
                materiel=materiel,
                type_alerte='STOCK',
                priorite='MOYENNE',
                statut='ACTIVE',  # Stock bas = Active (réapprovisionnement nécessaire)
                message=f"Stock bas - {materiel.Nom} - Il reste seulement {materiel.Quantite} unité(s) - Commander rapidement"
            )

    # Filtrage de base - TOUTES les alertes (résolues et non résolues)
    alertes = Alerte.objects.all()
    
    # Application des filtres
    if type_filter:
        alertes = alertes.filter(type_alerte=type_filter)
    if statut_filter:
        alertes = alertes.filter(statut=statut_filter)
    if priorite_filter:
        alertes = alertes.filter(priorite=priorite_filter)
    if search_query:
        alertes = alertes.filter(
            Q(materiel__Nom__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Tri par date de création (les plus récentes en premier)
    alertes = alertes.order_by('-date_creation')
    
    # Calcul des statistiques (incluent toutes les alertes)
    stats = {
        'alertes_actives': Alerte.objects.filter(statut='ACTIVE').count(),
        'alertes_attente': Alerte.objects.filter(statut='EN_COURS').count(),
        'alertes_resolues': Alerte.objects.filter(statut='RESOLUE').count(),
        'alertes_urgentes': Alerte.objects.filter(priorite='HAUTE').exclude(statut='RESOLUE').count(),
    }
    
    # Gestion de la création d'alerte manuelle
    if request.method == 'POST':
        materiel_id = request.POST.get('materiel')
        type_alerte = request.POST.get('type_alerte')
        priorite = request.POST.get('priorite')
        statut = request.POST.get('statut')
        message = request.POST.get('message')
        
        if materiel_id and type_alerte and priorite and statut and message:
            materiel = get_object_or_404(MaterielMedical, pk=materiel_id)
            
            Alerte.objects.create(
                materiel=materiel,
                type_alerte=type_alerte,
                priorite=priorite,
                statut=statut,
                message=message
            )
            messages.success(request, "Alerte créée avec succès!")
            return redirect('alertes')
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
    
    # Liste de tous les matériels pour la modal de création
    materiels = MaterielMedical.objects.all()
    
    context = {
        'alertes': alertes,
        'stats': stats,
        'materiels': materiels,
        'selected_type': type_filter,
        'selected_statut': statut_filter,
        'selected_priorite': priorite_filter,
        'search_query': search_query,
    }
    return render(request, 'materiel/alertes.html', context)


def demarrer_traitement_alerte(request, alerte_id):
    """Passer une alerte de ACTIVE à EN_COURS"""
    if request.method == 'POST':
        alerte = get_object_or_404(Alerte, pk=alerte_id)
        if alerte.statut == 'ACTIVE':
            alerte.statut = 'EN_COURS'
            alerte.save()
            
            # Ajouter un suivi dans l'historique
            HistoriqueMateriel.objects.create(
                materiel=alerte.materiel,
                action='MAINTENANCE',
                details=f"Traitement démarré pour l'alerte: {alerte.message}"
            )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                messages.success(request, "Traitement de l'alerte démarré!")
                return redirect('alertes')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Alerte déjà en cours ou résolue'})
            else:
                messages.error(request, "L'alerte est déjà en cours de traitement ou résolue.")
                return redirect('alertes')
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def resoudre_alerte(request, alerte_id):
    """Résoudre VRAIMENT une alerte - VERSION AVEC SUPPRESSION ET MAINTENANCE"""
    if request.method == 'POST':
        try:
            alerte = get_object_or_404(Alerte, pk=alerte_id)
            
            # ==================== ACTIONS RÉELLES SELON LE TYPE ====================
            message_action = ""
            
            if alerte.type_alerte == 'PANNE':
                # 🔧 VRAIE résolution : Remettre le matériel en MAINTENANCE (au lieu de EN_SERVICE)
                alerte.materiel.Etat = 'EN_MAINTENANCE'  # CHANGEMENT ICI
                alerte.materiel.save()
                message_action = f"Matériel {alerte.materiel.Nom} placé en maintenance"
                
            elif alerte.type_alerte == 'STOCK':
                # 📦 VRAIE résolution : Réapprovisionner le stock
                quantite_avant = alerte.materiel.Quantite
                
                if alerte.materiel.Quantite == 0:
                    alerte.materiel.Quantite = alerte.materiel.QuantiteInitiale or 20
                    message_action = f"Stock de {alerte.materiel.Nom} réapprovisionné à {alerte.materiel.Quantite} unités"
                    
                elif alerte.materiel.Quantite <= 5:
                    stock_souhaite = alerte.materiel.QuantiteInitiale or 20                   
                    quantite_ajoutee = stock_souhaite - alerte.materiel.Quantite
                    alerte.materiel.Quantite = stock_souhaite
                    message_action = f"Stock de {alerte.materiel.Nom} augmenté de {quantite_ajoutee} unités"
                    
                else:
                    message_action = f"Stock de {alerte.materiel.Nom} marqué comme géré"
                
                alerte.materiel.save()
                    
            elif alerte.type_alerte == 'EXPIRE':
                # ⏰ VRAIE résolution : SUPPRIMER le matériel expiré - CHANGEMENT MAJEUR ICI
                materiel_nom = alerte.materiel.Nom
                materiel_id = alerte.materiel.IdMaterial
                
                # Supprimer le matériel de la base de données
                alerte.materiel.delete()
                message_action = f"Matériel {materiel_nom} (ID: {materiel_id}) EXPIRÉ - SUPPRIMÉ DÉFINITIVEMENT"
                
            elif alerte.type_alerte == 'MAINTENANCE':
                # 🔧 VRAIE résolution : Fin de maintenance
                alerte.materiel.Etat = 'EN_SERVICE'
                alerte.materiel.save()
                message_action = f"Maintenance de {alerte.materiel.Nom} terminée - Remis en service"
                
            else:
                message_action = "Alerte résolue manuellement"
            
            # ==================== MISE À JOUR DE L'ALERTE ====================
            # Si c'est une alerte d'expiration, on supprime l'alerte aussi car le matériel n'existe plus
            if alerte.type_alerte == 'EXPIRE':
                alerte.delete()  # Supprimer l'alerte car le matériel est supprimé
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'action': message_action,
                        'materiel_supprime': True,
                        'materiel_id': materiel_id
                    })
                else:
                    messages.success(request, f"✅ Matériel expiré supprimé! {message_action}")
                    return redirect('alertes')
            else:
                # Pour les autres types d'alertes, on les marque comme résolues
                alerte.statut = 'RESOLUE'
                alerte.resolved = True
                alerte.date_resolution = timezone.now()
                alerte.save()
                
                # Historique
                HistoriqueMateriel.objects.create(
                    materiel=alerte.materiel,
                    action='MAINTENANCE',
                    details=f"ALERTE RÉSOLUE: {alerte.message} | ACTION RÉELLE: {message_action}"
                )
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'action': message_action,
                        'nouvel_etat': alerte.materiel.Etat if hasattr(alerte, 'materiel') else None,
                        'nouveau_stock': alerte.materiel.Quantite if alerte.type_alerte == 'STOCK' else None,
                    })
                else:
                    messages.success(request, f"✅ Alerte résolue! {message_action}")
                    return redirect('alertes')
                
        except Exception as e:
            error_message = f"Erreur lors de la résolution: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message})
            else:
                messages.error(request, error_message)
                return redirect('alertes')
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
def supprimer_alerte(request, alerte_id):
    """Supprimer une alerte"""
    if request.method == 'POST':
        try:
            alerte = get_object_or_404(Alerte, pk=alerte_id)
            materiel_nom = alerte.materiel.Nom
            alerte.delete()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                messages.success(request, f"Alerte pour {materiel_nom} supprimée avec succès!")
                return redirect('alertes')
                
        except Exception as e:
            error_message = f"Erreur lors de la suppression: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message})
            else:
                messages.error(request, error_message)
                return redirect('alertes')
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


def export_alertes(request):
    """Export des alertes en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alertes_medigestion.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Matériel', 'Référence', 'Type', 'Priorité', 'Statut', 
        'Message', 'Date Création', 'Date Résolution', 'Résolue'
    ])
    
    alertes = Alerte.objects.all().select_related('materiel')
    
    for alerte in alertes:
        writer.writerow([
            alerte.materiel.Nom,
            alerte.materiel.Reference,
            alerte.get_type_alerte_display(),
            alerte.get_priorite_display(),
            alerte.get_statut_display(),
            alerte.message,
            alerte.date_creation.strftime('%d/%m/%Y %H:%M'),
            alerte.date_resolution.strftime('%d/%m/%Y %H:%M') if alerte.date_resolution else '',
            'Oui' if alerte.resolved else 'Non'
        ])
    
    return response

# Garder les autres vues existantes...
def materiel_detail(request, pk):
    materiel = get_object_or_404(MaterielMedical, IdMaterial=pk)
    historique = HistoriqueMateriel.objects.filter(materiel=materiel).order_by('-date_action')[:20]
    return render(request, 'materiel/detail_materiel.html', {
        'materiel': materiel,
        'historique': historique
    })

def mettre_en_maintenance(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_MAINTENANCE'
    materiel.save()
    
    HistoriqueMateriel.objects.create(
        materiel=materiel,
        action='MAINTENANCE',
        details="Mise en maintenance"
    )
    
    messages.success(request, f"{materiel.Nom} est maintenant en maintenance.")
    return redirect('liste_materiels')

def remettre_en_service(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_SERVICE'
    materiel.save()
    
    HistoriqueMateriel.objects.create(
        materiel=materiel,
        action='MODIFICATION',
        details="Remis en service"
    )
    
    messages.success(request, f"{materiel.Nom} est de nouveau en service.")
    return redirect('liste_materiels')

def reparer_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_MAINTENANCE'
    materiel.save()
    
    HistoriqueMateriel.objects.create(
        materiel=materiel,
        action='MAINTENANCE',
        details="Envoyé en réparation"
    )
    
    messages.success(request, f"{materiel.Nom} est envoyé en réparation.")
    return redirect('liste_materiels')

def retour_pret_old(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    
    if materiel.Etat != 'EN_PRET':
        messages.error(request, f"Le matériel {materiel.Nom} n'est pas en prêt.")
        return redirect('liste_materiels')
    
    try:
        materiel.Quantite += 1
        materiel.Etat = 'EN_SERVICE'
        materiel.save()

        HistoriqueMateriel.objects.create(
            materiel=materiel,
            action='RETOUR',
            details="Retour de prêt"
        )

        messages.success(request, f"{materiel.Nom} est retourné et remis en service. Quantité mise à jour : {materiel.Quantite}.")
        
    except Exception as e:
        messages.error(request, f"Erreur lors du retour de prêt : {str(e)}")
    
    return redirect('liste_materiels')
    
def gestion_prets(request):
    """Vue complète pour la gestion des prêts"""
    today = timezone.now().date()
    
    # Calcul des statistiques
    stats = {
        'prets_actifs': Pret.objects.filter(statut='EN_COURS').count(),
        'prets_retard': Pret.objects.filter(statut='RETARD').count(),
        'prets_termines': Pret.objects.filter(statut='RETOURNE').count(),
        'prets_semaine': Pret.objects.filter(
            date_pret__gte=today - timedelta(days=7)
        ).count(),
    }
    
    # Filtrage des prêts
    prets_actifs = Pret.objects.filter(statut='EN_COURS').select_related('materiel')
    prets_retard = Pret.objects.filter(statut='RETARD').select_related('materiel')
    prets_historique = Pret.objects.filter(statut='RETOURNE').select_related('materiel')
    
    # Matériels disponibles (non prêtés et en service)
    materiels_en_pret = Pret.objects.filter(
        statut__in=['EN_COURS', 'RETARD']
    ).values_list('materiel_id', flat=True)
    
    materiels_disponibles = MaterielMedical.objects.filter(
        Etat='EN_SERVICE'
    ).exclude(IdMaterial__in=materiels_en_pret)
    
    # Gestion du formulaire de nouveau prêt
    if request.method == 'POST':
        form = PretForm(request.POST)
        if form.is_valid():
            pret = form.save(commit=False)
            pret.date_pret = today
            
            # Mettre à jour l'état du matériel
            materiel = pret.materiel
            materiel.Etat = 'EN_PRET'
            materiel.save()
            
            pret.save()
            
            # Historique
            HistoriqueMateriel.objects.create(
                materiel=materiel,
                action='PRET',
                details=f"Prêté à {pret.emprunteur} ({pret.service}) - Retour prévu le {pret.date_retour_prevue}"
            )
            
            messages.success(request, f"Prêt de {pret.materiel.Nom} créé avec succès!")
            return redirect('gestion_prets')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PretForm()
    
    context = {
        'stats': stats,
        'prets_actifs': prets_actifs,
        'prets_retard': prets_retard,
        'prets_historique': prets_historique,
        'materiels_disponibles': materiels_disponibles,
        'form': form,
    }
    return render(request, 'materiel/prets.html', context)

def retourner_pret(request, pret_id):
    """Marquer un prêt comme retourné"""
    if request.method == 'POST':
        pret = get_object_or_404(Pret, id=pret_id)
        pret.date_retour_reelle = timezone.now().date()
        pret.statut = 'RETOURNE'
        
        # Remettre le matériel en service
        materiel = pret.materiel
        materiel.Etat = 'EN_SERVICE'
        materiel.save()
        
        pret.save()
        
        # Historique
        HistoriqueMateriel.objects.create(
            materiel=materiel,
            action='RETOUR',
            details=f"Retour de prêt par {pret.emprunteur}"
        )
        
        messages.success(request, f"Retour de {pret.materiel.Nom} confirmé!")
        return redirect('gestion_prets')
    
    return JsonResponse({'success': False})

def prolonger_pret(request, pret_id):
    """Prolonger la date de retour d'un prêt"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        nouvelle_date_str = data.get('nouvelle_date')
        
        try:
            # Convertir la date
            from datetime import datetime
            nouvelle_date = datetime.strptime(nouvelle_date_str, '%d/%m/%Y').date()
            pret = get_object_or_404(Pret, id=pret_id)
            
            if nouvelle_date <= pret.date_retour_prevue:
                return JsonResponse({
                    'success': False, 
                    'error': 'La nouvelle date doit être postérieure à la date actuelle'
                })
            
            pret.date_retour_prevue = nouvelle_date
            pret.save()
            
            # Historique
            HistoriqueMateriel.objects.create(
                materiel=pret.materiel,
                action='MODIFICATION',
                details=f"Prolongation du prêt - Nouveau retour: {nouvelle_date}"
            )
            
            return JsonResponse({'success': True})
            
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Format de date invalide'})
    
    return JsonResponse({'success': False})

def details_pret(request, pret_id):
    """Détails d'un prêt"""
    pret = get_object_or_404(Pret, id=pret_id)
    return render(request, 'materiel/details_pret.html', {'pret': pret})

def export_prets(request):
    """Export des prêts en CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="prets_medigestion.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Matériel', 'Référence', 'Emprunteur', 'Service', 
        'Date emprunt', 'Date retour prévue', 'Date retour réelle',
        'Statut', 'Notes'
    ])
    
    prets = Pret.objects.all().select_related('materiel')
    
    for pret in prets:
        writer.writerow([
            pret.materiel.Nom,
            pret.materiel.Reference,
            pret.emprunteur,
            pret.service,
            pret.date_pret.strftime('%d/%m/%Y'),
            pret.date_retour_prevue.strftime('%d/%m/%Y'),
            pret.date_retour_reelle.strftime('%d/%m/%Y') if pret.date_retour_reelle else '',
            pret.get_statut_display(),
            pret.notes
        ])
    
    return response