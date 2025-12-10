from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Employee
from GestionTacheApp.models import Tache
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.utils.dateparse import parse_date
from django import forms
from django.db import models as dj_models
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime, timedelta
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from GestionTacheApp.models import TacheDocument, TacheNote


class TacheForm(forms.ModelForm):
	class Meta:
		model = Tache
		fields = ('description', 'date_echeance', 'employee', 'statut', 'notify_interval_hours')
		widgets = {
			'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
			'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'employee': forms.Select(attrs={'class': 'form-select'}),
			'statut': forms.Select(attrs={'class': 'form-select'}),
			'notify_interval_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
		}


def doctor_list_taches(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	queryset = Tache.objects.filter(employee=emp).order_by('order', 'date_echeance')
	shared_queryset = Tache.objects.filter(collaborators__pk=emp.pk).exclude(employee=emp).order_by('date_echeance')
	statut = request.GET.get('statut')
	date_from = request.GET.get('date_from')
	date_to = request.GET.get('date_to')
	if statut in ('Pending', 'Done'):
		queryset = queryset.filter(statut=statut)
	if date_from:
		dfrom = parse_date(date_from)
		if dfrom:
			queryset = queryset.filter(date_echeance__gte=dfrom)
	if date_to:
		dto = parse_date(date_to)
		if dto:
			queryset = queryset.filter(date_echeance__lte=dto)



	# compute upcoming tasks for notifications (per-task interval)
	upcoming_taches = []
	if emp.notification_enabled:
		now = datetime.now().date()
		# Since date_echeance is a DateField, we'll include tasks whose date <= now + interval_days
		# Convert each task's hours to days range by flooring division by 24? We'll compute per task with hours and compare to date.
		# Simpler: filter Pending, then include if date_echeance <= now + ceil(hours/24) days
		from math import ceil
		candidates = queryset.filter(statut='Pending')
		upcoming_taches = [t for t in candidates if t.date_echeance <= (now + timedelta(days=ceil(t.notify_interval_hours/24)))]

	return render(request, 'employee/doctor_tache_list.html', {
		'employee': emp,
		'taches': queryset,
		'shared_taches': shared_queryset,
		'filter_statut': statut or '',
		'filter_date_from': date_from or '',
		'filter_date_to': date_to or '',
		'upcoming_taches': upcoming_taches,
		'today': datetime.now().date(),
	})


class NotificationPreferencesForm(forms.Form):
	notification_enabled = forms.BooleanField(required=False, label="Activer les notifications")
	notification_interval_hours = forms.IntegerField(min_value=1, label="Intervalle (heures)")


def notification_preferences(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	if emp.role not in ('Medecin', 'Infirmier'):
		return HttpResponseForbidden('Accès refusé')

	if request.method == 'POST':
		form = NotificationPreferencesForm(request.POST)
		if form.is_valid():
			emp.notification_enabled = form.cleaned_data['notification_enabled']
			emp.notification_interval_hours = form.cleaned_data['notification_interval_hours']
			emp.save()
			return HttpResponseRedirect(reverse('employee:dashboard'))
	else:
		form = NotificationPreferencesForm(initial={
			'notification_enabled': emp.notification_enabled,
			'notification_interval_hours': emp.notification_interval_hours,
		})

	return render(request, 'employee/notification_preferences.html', {'employee': emp, 'form': form})


def doctor_create_tache(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	if request.method == 'POST':
		form = TacheForm(request.POST)
		form.fields['employee'].widget = forms.HiddenInput()
		if form.is_valid():
			t = form.save(commit=False)
			t.employee = emp
			# assign next order for this employee
			max_order = Tache.objects.filter(employee=emp).aggregate(dj_models.Max('order')).get('order__max') or 0
			t.order = max_order + 1
			t.save()
			return redirect('employee:doctor_list_taches')
		employee_hidden = True
	else:
		form = TacheForm(initial={'employee': emp.pk})
		form.fields['employee'].widget = forms.HiddenInput()
		employee_hidden = True

	return render(request, 'employee/doctor_tache_form.html', {'form': form, 'employee': emp, 'employee_hidden': employee_hidden})


def doctor_edit_tache(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	try:
		t = Tache.objects.get(pk=pk, employee=emp)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if request.method == 'POST':
		form = TacheForm(request.POST, instance=t)
		form.fields['employee'].widget = forms.HiddenInput()
		if form.is_valid():
			t = form.save(commit=False)
			t.employee = emp
			t.save()
			return redirect('employee:doctor_list_taches')
		employee_hidden = True
	else:
		form = TacheForm(instance=t)
		form.fields['employee'].widget = forms.HiddenInput()
		employee_hidden = True

	return render(request, 'employee/doctor_tache_form.html', {'form': form, 'employee': emp, 'tache': t, 'employee_hidden': employee_hidden})


@require_POST
def doctor_delete_tache(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	try:
		t = Tache.objects.get(pk=pk, employee=emp)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	t.delete()
	return redirect('employee:doctor_list_taches')


def login_view(request):
	"""Simple login against Employee.login and Employee.MotDePasse.
	Note: This is a minimal example for the exercise. For production, use Django's auth system.
	"""
	if request.method == 'POST':
		login = request.POST.get('login')
		password = request.POST.get('password')
		try:
			emp = Employee.objects.get(login=login, MotDePasse=password)
		except Employee.DoesNotExist:
			messages.error(request, 'Identifiants invalides')
			return render(request, 'employee/login.html')

		request.session['employee_id'] = emp.pk
		return redirect('employee:dashboard')

	return render(request, 'employee/login.html')


def logout_view(request):
	request.session.pop('employee_id', None)
	return redirect('/')


def dashboard_redirect(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	role = emp.role
	if role == 'Medecin':
		return redirect('employee:doctor_list_taches')
	if role == 'Infirmier':
		queryset = Tache.objects.filter(employee=emp).order_by('order', 'date_echeance')
		shared_queryset = Tache.objects.filter(collaborators__pk=emp.pk).exclude(employee=emp).order_by('date_echeance')
		statut = request.GET.get('statut')
		date_from = request.GET.get('date_from')
		date_to = request.GET.get('date_to')
		if statut in ('Pending', 'Done'):
			queryset = queryset.filter(statut=statut)
		if date_from:
			dfrom = parse_date(date_from)
			if dfrom:
				queryset = queryset.filter(date_echeance__gte=dfrom)
		if date_to:
			dto = parse_date(date_to)
			if dto:
				queryset = queryset.filter(date_echeance__lte=dto)


		# compute upcoming tasks for notifications for infirmier (per-task interval)
		upcoming_taches = []
		if emp.notification_enabled:
			now = datetime.now().date()
			from math import ceil
			candidates = queryset.filter(statut='Pending')
			upcoming_taches = [t for t in candidates if t.date_echeance <= (now + timedelta(days=ceil(t.notify_interval_hours/24)))]

		return render(request, 'employee/dashboard_infirmier.html', {
			'employee': emp,
			'taches': queryset,
			'shared_taches': shared_queryset,
			'filter_statut': statut or '',
			'filter_date_from': date_from or '',
			'filter_date_to': date_to or '',
			'upcoming_taches': upcoming_taches,
			'today': datetime.now().date(),
		})
	if role == 'Gestionnaire de Materiel':
		return render(request, 'employee/dashboard_gestionnaire.html', {'employee': emp})
	return render(request, 'employee/dashboard_generic.html', {'employee': emp})


@require_POST
def update_task_status(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	try:
		t = Tache.objects.get(pk=pk)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	# Owner or collaborator may change status
	if t.employee.pk != emp.pk and not t.collaborators.filter(pk=emp.pk).exists():
		return HttpResponseForbidden('Vous n\'êtes pas autorisé à modifier cette tâche')

	new_status = request.POST.get('statut')
	if new_status not in ('Pending', 'Done'):
		return HttpResponseForbidden('Statut invalide')

	t.statut = new_status
	t.save()

	return redirect(request.META.get('HTTP_REFERER', '/employee/dashboard/'))


class TaskNotificationForm(forms.ModelForm):
	class Meta:
		model = Tache
		fields = ('notify_interval_hours',)
		widgets = {
			'notify_interval_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
		}


def edit_task_notification(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	if emp.role not in ('Medecin', 'Infirmier'):
		return HttpResponseForbidden('Accès refusé')

	try:
		t = Tache.objects.get(pk=pk, employee=emp)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if request.method == 'POST':
		form = TaskNotificationForm(request.POST, instance=t)
		if form.is_valid():
			form.save()
			# redirect back to the page the user came from
			return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'employee:dashboard')
	else:
		form = TaskNotificationForm(instance=t)

	return render(request, 'employee/task_notification_form.html', {
		'employee': emp,
		'form': form,
		'tache': t,
		'next': request.GET.get('next', ''),
	})


class CollaboratorsForm(forms.Form):
	# Use a ModelMultipleChoiceField with a filtered queryset (Medecin/Infirmier only)
	collaborators = forms.ModelMultipleChoiceField(
		queryset=Employee.objects.none(),
		required=False,
		widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8})
	)

	def __init__(self, *args, **kwargs):
		emp = kwargs.pop('current_employee', None)
		super().__init__(*args, **kwargs)
		# Allow only Medecin and Infirmier
		self.fields['collaborators'].queryset = Employee.objects.filter(role__in=['Medecin', 'Infirmier']).exclude(pk=getattr(emp, 'pk', None))


def edit_task_collaborators(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	if emp.role not in ('Medecin', 'Infirmier'):
		return HttpResponseForbidden('Accès refusé')

	try:
		t = Tache.objects.get(pk=pk, employee=emp)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if request.method == 'POST':
		form = CollaboratorsForm(request.POST, current_employee=emp)
		if form.is_valid():
			selected = form.cleaned_data['collaborators']
			allowed_roles = {'Medecin', 'Infirmier'}
			selected = [c for c in selected if c.role in allowed_roles]
			t.collaborators.set(selected)
			t.save()
			return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'employee:doctor_list_taches')
	else:
		form = CollaboratorsForm(current_employee=emp, initial={
			'collaborators': t.collaborators.all()
		})

	# Prepare grouped lists: medecins and infirmiers (excluding current employee)
	medecins = Employee.objects.filter(role='Medecin').exclude(pk=emp.pk)
	infirmiers = Employee.objects.filter(role='Infirmier').exclude(pk=emp.pk)
	selected_ids = set(t.collaborators.values_list('pk', flat=True))

	return render(request, 'employee/task_collaborators_form.html', {
		'employee': emp,
		'form': form,
		'tache': t,
		'next': request.GET.get('next', ''),
		'medecins': medecins,
		'infirmiers': infirmiers,
		'selected_ids': selected_ids,
	})


@require_POST
def reorder_tasks(request):
	"""Accept JSON payload: { order: [tache_id1, tache_id2, ...] } and set order starting at 1.
	Applies only to tasks of current employee. Returns 403 for wrong role or mismatched tasks.
	"""
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	# Only Medecin and Infirmier manage their own ordering
	if emp.role not in ('Medecin', 'Infirmier'):
		return HttpResponseForbidden('Accès refusé')

	try:
		import json
		payload = json.loads(request.body.decode('utf-8'))
		new_order = payload.get('order', [])
	except Exception:
		return HttpResponseForbidden('Payload invalide')

	# Validate IDs belong to current employee
	taches = Tache.objects.filter(employee=emp, idTache__in=new_order)
	if taches.count() != len(new_order):
		return HttpResponseForbidden('Tâches invalides')

	# Update order starting at 1, keep any taches not listed at the end
	order_map = {tid: idx+1 for idx, tid in enumerate(new_order)}
	for t in taches:
		t.order = order_map.get(t.idTache, t.order)
		t.save()

	# For tasks not in payload, append after the last index preserving current order
	remaining = Tache.objects.filter(employee=emp).exclude(idTache__in=new_order).order_by('order', 'date_echeance')
	last_index = len(new_order)
	for offset, t in enumerate(remaining, start=1):
		# only reassign if its order is <= last_index to keep stable ordering after listed ones
		if t.order <= last_index:
			t.order = last_index + offset
			t.save()

	from django.http import JsonResponse
	return JsonResponse({'status': 'ok'})


def _can_access_task(emp: Employee, t: Tache) -> bool:
	return t.employee_id == emp.pk or t.collaborators.filter(pk=emp.pk).exists()


def task_detail(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	try:
		t = Tache.objects.get(pk=pk)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if not _can_access_task(emp, t):
		return HttpResponseForbidden('Accès refusé')

	documents = t.documents.all().order_by('-created_at')
	notes = t.notes.all().order_by('-created_at')

	return render(request, 'employee/task_detail.html', {
		'employee': emp,
		'tache': t,
		'documents': documents,
		'notes': notes,
	})


@require_POST
def upload_task_document(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	try:
		t = Tache.objects.get(pk=pk)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if not _can_access_task(emp, t):
		return HttpResponseForbidden('Accès refusé')

	f = request.FILES.get('file')
	if not f:
		messages.error(request, 'Aucun fichier envoyé')
		return redirect('employee:task_detail', pk=pk)

	doc = TacheDocument.objects.create(tache=t, file=f, uploader=emp)
	messages.success(request, 'Document ajouté')
	return redirect('employee:task_detail', pk=pk)


@require_POST
def add_task_note(request, pk):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	try:
		emp = Employee.objects.get(pk=emp_id)
	except Employee.DoesNotExist:
		return redirect('employee:login')

	try:
		t = Tache.objects.get(pk=pk)
	except Tache.DoesNotExist:
		return HttpResponseForbidden('Tâche introuvable')

	if not _can_access_task(emp, t):
		return HttpResponseForbidden('Accès refusé')

	content = request.POST.get('content', '').strip()
	if not content:
		messages.error(request, 'La note est vide')
		return redirect('employee:task_detail', pk=pk)

	TacheNote.objects.create(tache=t, content=content, author=emp)
	messages.success(request, 'Note ajoutée')
	return redirect('employee:task_detail', pk=pk)

