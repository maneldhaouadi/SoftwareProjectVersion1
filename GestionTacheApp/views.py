from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.utils.dateparse import parse_date
from django import forms
from django.db import models as dj_models
from django.urls import reverse
from datetime import datetime, timedelta

from EmployeeApp.models import Employee
from .models import Tache


class TacheForm(forms.ModelForm):
	class Meta:
		model = Tache
		fields = ('description', 'date_echeance', 'employee', 'statut')
		widgets = {
			'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
			'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'employee': forms.Select(attrs={'class': 'form-select'}),
			'statut': forms.Select(attrs={'class': 'form-select'}),
		}


def doctor_list_taches(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	queryset = Tache.objects.filter(employee=emp).order_by('order', 'date_echeance')
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

	upcoming_taches = []
	if getattr(emp, 'notification_enabled', False):
		now = datetime.now().date()
		interval_days = getattr(emp, 'notification_interval_days', 0) or 0
		if interval_days > 0:
			end = now + timedelta(days=interval_days)
			upcoming_taches = list(Tache.objects.filter(employee=emp, date_echeance__range=(now, end), statut='Pending').order_by('date_echeance'))

	return render(request, 'employee/doctor_tache_list.html', {
		'employee': emp,
		'taches': queryset,
		'upcoming_taches': upcoming_taches,
	})


class NotificationPreferencesForm(forms.Form):
	notification_enabled = forms.BooleanField(required=False)
	notification_interval_days = forms.IntegerField(required=False, min_value=0, max_value=365)


def notification_preferences(request):
	emp_id = request.session.get('employee_id')
	if not emp_id:
		return redirect('employee:login')
	emp = Employee.objects.get(pk=emp_id)
	if emp.role != 'Medecin':
		return HttpResponseForbidden('Accès refusé')

	if request.method == 'POST':
		form = NotificationPreferencesForm(request.POST)
		if form.is_valid():
			emp.notification_enabled = form.cleaned_data.get('notification_enabled') or False
			interval = form.cleaned_data.get('notification_interval_days')
			emp.notification_interval_days = interval if interval is not None else 0
			emp.save()
			messages.success(request, 'Préférences mises à jour.')
			return redirect('employee:doctor_list_taches')
	else:
		form = NotificationPreferencesForm(initial={
			'notification_enabled': getattr(emp, 'notification_enabled', False),
			'notification_interval_days': getattr(emp, 'notification_interval_days', 0),
		})

	return render(request, 'employee/notification_preferences.html', {
		'employee': emp,
		'form': form,
	})


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
	if request.method == 'POST':
		login = request.POST.get('login')
		password = request.POST.get('password')
		try:
			emp = Employee.objects.get(login=login, mot_de_passe=password)
		except Employee.DoesNotExist:
			messages.error(request, 'Identifiants invalides')
			return render(request, 'employee/login.html')
		request.session['employee_id'] = emp.pk
		return redirect('employee:dashboard')
	return render(request, 'employee/login.html')


def logout_view(request):
	request.session.pop('employee_id', None)
	return redirect('employee:login')


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
		return render(request, 'employee/infirmier_tache_list.html', {'employee': emp, 'taches': queryset})

	return redirect('employee:doctor_list_taches')


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

	if t.employee.pk != emp.pk:
		return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cette tâche")

	new_status = request.POST.get('statut')
	if new_status not in ('Pending', 'Done'):
		return HttpResponseForbidden('Statut invalide')

	t.statut = new_status
	t.save()

	return redirect(request.META.get('HTTP_REFERER', '/employee/dashboard/'))
