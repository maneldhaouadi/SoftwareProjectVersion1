from django.shortcuts import render, redirect
from .forms import EmployeForm
from django.contrib import messages
from .models import Employe

def ajouter_employe(request):
    if request.method == 'POST':
        form = EmployeForm(request.POST)
        if form.is_valid():
            # Hasher le mot de passe si tu veux
            employe = form.save(commit=False)
            # from django.contrib.auth.hashers import make_password
            # employe.mot_de_passe = make_password(form.cleaned_data['mot_de_passe'])
            employe.save()
            messages.success(request, "Employé ajouté avec succès !")
            return redirect('liste_employes')
    else:
        form = EmployeForm()
    return render(request, 'Employe/ajouter_employe.html', {'form': form})




def liste_employes(request):
    employes = Employe.objects.all()
    return render(request, 'Employe/liste_employes.html', {'employes': employes})



# from django.shortcuts import render, redirect
# from django.contrib import messages
# from .models import Employee
# from GestionTacheApp.models import Tache
# from django.views.decorators.http import require_POST
# from django.http import HttpResponseForbidden
# from django.utils.dateparse import parse_date
# from django import forms
# from django.db import models as dj_models
# from django.urls import reverse
# from django.http import HttpResponseRedirect
# from datetime import datetime, timedelta


# class TacheForm(forms.ModelForm):
# 	class Meta:
# 		model = Tache
# 		fields = ('description', 'date_echeance', 'employee', 'statut')
# 		widgets = {
# 			'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
# 			'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
# 			'employee': forms.Select(attrs={'class': 'form-select'}),
# 			'statut': forms.Select(attrs={'class': 'form-select'}),
# 		}


# def doctor_list_taches(request):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	emp = Employee.objects.get(pk=emp_id)
# 	if emp.role != 'Medecin':
# 		return HttpResponseForbidden('Accès refusé')

# 	queryset = Tache.objects.filter(employee=emp).order_by('order', 'date_echeance')
# 	statut = request.GET.get('statut')
# 	date_from = request.GET.get('date_from')
# 	date_to = request.GET.get('date_to')
# 	if statut in ('Pending', 'Done'):
# 		queryset = queryset.filter(statut=statut)
# 	if date_from:
# 		dfrom = parse_date(date_from)
# 		if dfrom:
# 			queryset = queryset.filter(date_echeance__gte=dfrom)
# 	if date_to:
# 		dto = parse_date(date_to)
# 		if dto:
# 			queryset = queryset.filter(date_echeance__lte=dto)


# 	# compute upcoming tasks for notifications
# 	upcoming_taches = []
# 	if emp.notification_enabled:
# 		now = datetime.now().date()
# 		max_date = now + timedelta(hours=emp.notification_interval_hours)
# 		# Tache.date_echeance is a date field, so compare dates
# 		upcoming_taches = queryset.filter(statut='Pending', date_echeance__lte=max_date).order_by('date_echeance')

# 	return render(request, 'employee/doctor_tache_list.html', {
# 		'employee': emp,
# 		'taches': queryset,
# 		'filter_statut': statut or '',
# 		'filter_date_from': date_from or '',
# 		'filter_date_to': date_to or '',
# 		'upcoming_taches': upcoming_taches,
# 		'today': datetime.now().date(),
# 	})


# class NotificationPreferencesForm(forms.Form):
# 	notification_enabled = forms.BooleanField(required=False, label="Activer les notifications")
# 	notification_interval_hours = forms.IntegerField(min_value=1, label="Intervalle (heures)")


# def notification_preferences(request):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	try:
# 		emp = Employee.objects.get(pk=emp_id)
# 	except Employee.DoesNotExist:
# 		return redirect('employee:login')

# 	if emp.role not in ('Medecin', 'Infirmier'):
# 		return HttpResponseForbidden('Accès refusé')

# 	if request.method == 'POST':
# 		form = NotificationPreferencesForm(request.POST)
# 		if form.is_valid():
# 			emp.notification_enabled = form.cleaned_data['notification_enabled']
# 			emp.notification_interval_hours = form.cleaned_data['notification_interval_hours']
# 			emp.save()
# 			return HttpResponseRedirect(reverse('employee:dashboard'))
# 	else:
# 		form = NotificationPreferencesForm(initial={
# 			'notification_enabled': emp.notification_enabled,
# 			'notification_interval_hours': emp.notification_interval_hours,
# 		})

# 	return render(request, 'employee/notification_preferences.html', {'employee': emp, 'form': form})


# def doctor_create_tache(request):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	emp = Employee.objects.get(pk=emp_id)
# 	if emp.role != 'Medecin':
# 		return HttpResponseForbidden('Accès refusé')

# 	if request.method == 'POST':
# 		form = TacheForm(request.POST)
# 		form.fields['employee'].widget = forms.HiddenInput()
# 		if form.is_valid():
# 			t = form.save(commit=False)
# 			t.employee = emp
# 			# assign next order for this employee
# 			max_order = Tache.objects.filter(employee=emp).aggregate(dj_models.Max('order')).get('order__max') or 0
# 			t.order = max_order + 1
# 			t.save()
# 			return redirect('employee:doctor_list_taches')
# 		employee_hidden = True
# 	else:
# 		form = TacheForm(initial={'employee': emp.pk})
# 		form.fields['employee'].widget = forms.HiddenInput()
# 		employee_hidden = True

# 	return render(request, 'employee/doctor_tache_form.html', {'form': form, 'employee': emp, 'employee_hidden': employee_hidden})


# def doctor_edit_tache(request, pk):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	emp = Employee.objects.get(pk=emp_id)
# 	if emp.role != 'Medecin':
# 		return HttpResponseForbidden('Accès refusé')

# 	try:
# 		t = Tache.objects.get(pk=pk, employee=emp)
# 	except Tache.DoesNotExist:
# 		return HttpResponseForbidden('Tâche introuvable')

# 	if request.method == 'POST':
# 		form = TacheForm(request.POST, instance=t)
# 		form.fields['employee'].widget = forms.HiddenInput()
# 		if form.is_valid():
# 			t = form.save(commit=False)
# 			t.employee = emp
# 			t.save()
# 			return redirect('employee:doctor_list_taches')
# 		employee_hidden = True
# 	else:
# 		form = TacheForm(instance=t)
# 		form.fields['employee'].widget = forms.HiddenInput()
# 		employee_hidden = True

# 	return render(request, 'employee/doctor_tache_form.html', {'form': form, 'employee': emp, 'tache': t, 'employee_hidden': employee_hidden})


# @require_POST
# def doctor_delete_tache(request, pk):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	emp = Employee.objects.get(pk=emp_id)
# 	if emp.role != 'Medecin':
# 		return HttpResponseForbidden('Accès refusé')

# 	try:
# 		t = Tache.objects.get(pk=pk, employee=emp)
# 	except Tache.DoesNotExist:
# 		return HttpResponseForbidden('Tâche introuvable')

# 	t.delete()
# 	return redirect('employee:doctor_list_taches')


# def login_view(request):
# 	"""Simple login against Employee.login and Employee.MotDePasse.
# 	Note: This is a minimal example for the exercise. For production, use Django's auth system.
# 	"""
# 	if request.method == 'POST':
# 		login = request.POST.get('login')
# 		password = request.POST.get('password')
# 		try:
# 			emp = Employee.objects.get(login=login, MotDePasse=password)
# 		except Employee.DoesNotExist:
# 			messages.error(request, 'Identifiants invalides')
# 			return render(request, 'employee/login.html')

# 		request.session['employee_id'] = emp.pk
# 		return redirect('employee:dashboard')

# 	return render(request, 'employee/login.html')


# def logout_view(request):
# 	request.session.pop('employee_id', None)
# 	return redirect('/')


# def dashboard_redirect(request):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	try:
# 		emp = Employee.objects.get(pk=emp_id)
# 	except Employee.DoesNotExist:
# 		return redirect('employee:login')

# 	role = emp.role
# 	if role == 'Medecin':
# 		return redirect('employee:doctor_list_taches')
# 	if role == 'Infirmier':
# 		queryset = Tache.objects.filter(employee=emp).order_by('order', 'date_echeance')
# 		statut = request.GET.get('statut')
# 		date_from = request.GET.get('date_from')
# 		date_to = request.GET.get('date_to')
# 		if statut in ('Pending', 'Done'):
# 			queryset = queryset.filter(statut=statut)
# 		if date_from:
# 			dfrom = parse_date(date_from)
# 			if dfrom:
# 				queryset = queryset.filter(date_echeance__gte=dfrom)
# 		if date_to:
# 			dto = parse_date(date_to)
# 			if dto:
# 				queryset = queryset.filter(date_echeance__lte=dto)


# 		# compute upcoming tasks for notifications for infirmier
# 		upcoming_taches = []
# 		if emp.notification_enabled:
# 			now = datetime.now().date()
# 			max_date = now + timedelta(hours=emp.notification_interval_hours)
# 			upcoming_taches = queryset.filter(statut='Pending', date_echeance__lte=max_date).order_by('date_echeance')

# 		return render(request, 'employee/dashboard_infirmier.html', {
# 			'employee': emp,
# 			'taches': queryset,
# 			'filter_statut': statut or '',
# 			'filter_date_from': date_from or '',
# 			'filter_date_to': date_to or '',
# 			'upcoming_taches': upcoming_taches,
# 			'today': datetime.now().date(),
# 		})
# 	if role == 'Gestionnaire de Materiel':
# 		return render(request, 'employee/dashboard_gestionnaire.html', {'employee': emp})
# 	return render(request, 'employee/dashboard_generic.html', {'employee': emp})


# @require_POST
# def update_task_status(request, pk):
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	try:
# 		emp = Employee.objects.get(pk=emp_id)
# 	except Employee.DoesNotExist:
# 		return redirect('employee:login')

# 	try:
# 		t = Tache.objects.get(pk=pk)
# 	except Tache.DoesNotExist:
# 		return HttpResponseForbidden('Tâche introuvable')

# 	if t.employee.pk != emp.pk:
# 		return HttpResponseForbidden('Vous n\'êtes pas autorisé à modifier cette tâche')

# 	new_status = request.POST.get('statut')
# 	if new_status not in ('Pending', 'Done'):
# 		return HttpResponseForbidden('Statut invalide')

# 	t.statut = new_status
# 	t.save()

# 	return redirect(request.META.get('HTTP_REFERER', '/employee/dashboard/'))


# @require_POST
# def reorder_tasks(request):
# 	"""Accept JSON payload: { order: [tache_id1, tache_id2, ...] } and set order starting at 1.
# 	Applies only to tasks of current employee. Returns 403 for wrong role or mismatched tasks.
# 	"""
# 	emp_id = request.session.get('employee_id')
# 	if not emp_id:
# 		return redirect('employee:login')
# 	try:
# 		emp = Employee.objects.get(pk=emp_id)
# 	except Employee.DoesNotExist:
# 		return redirect('employee:login')

# 	# Only Medecin and Infirmier manage their own ordering
# 	if emp.role not in ('Medecin', 'Infirmier'):
# 		return HttpResponseForbidden('Accès refusé')

# 	try:
# 		import json
# 		payload = json.loads(request.body.decode('utf-8'))
# 		new_order = payload.get('order', [])
# 	except Exception:
# 		return HttpResponseForbidden('Payload invalide')

# 	# Validate IDs belong to current employee
# 	taches = Tache.objects.filter(employee=emp, idTache__in=new_order)
# 	if taches.count() != len(new_order):
# 		return HttpResponseForbidden('Tâches invalides')

# 	# Update order starting at 1, keep any taches not listed at the end
# 	order_map = {tid: idx+1 for idx, tid in enumerate(new_order)}
# 	for t in taches:
# 		t.order = order_map.get(t.idTache, t.order)
# 		t.save()

# 	# For tasks not in payload, append after the last index preserving current order
# 	remaining = Tache.objects.filter(employee=emp).exclude(idTache__in=new_order).order_by('order', 'date_echeance')
# 	last_index = len(new_order)
# 	for offset, t in enumerate(remaining, start=1):
# 		# only reassign if its order is <= last_index to keep stable ordering after listed ones
# 		if t.order <= last_index:
# 			t.order = last_index + offset
# 			t.save()

# 	from django.http import JsonResponse
# 	return JsonResponse({'status': 'ok'})

