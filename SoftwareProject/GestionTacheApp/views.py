from django.shortcuts import render, redirect
from django.contrib import messages
from EmployeApp.models import Employe
from GestionTacheApp.models import Tache, TacheNote, TacheAttachment, TacheCollaboration
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.utils.dateparse import parse_date
from django import forms
from django.db import models as dj_models
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime, timedelta
from django.conf import settings
import json
from pathlib import Path
from django.utils import timezone


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

    def __init__(self, *args, **kwargs):
        # Keep signature for compatibility; nothing extra for collaborators here.
        kwargs.pop('current_emp', None)
        super().__init__(*args, **kwargs)


class CollaboratorForm(forms.Form):
    collaborators = forms.ModelMultipleChoiceField(
        queryset=Employe.objects.none(), required=False, label='Collaborateurs (Médecins/Infirmières)',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8})
    )

    def __init__(self, *args, **kwargs):
        current_emp = kwargs.pop('current_emp', None)
        super().__init__(*args, **kwargs)
        qs = Employe.objects.filter(role__in=['medecin', 'infirmiere'])
        if current_emp is not None:
            qs = qs.exclude(pk=current_emp.pk)
        self.fields['collaborators'].queryset = qs.order_by('nom', 'prenom')


def doctor_list_taches(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
        return HttpResponseForbidden('Accès refusé')

    queryset = Tache.objects.filter(
        Q(employee=emp) | Q(collaborations__collaborator=emp, collaborations__status='accepted')
    ).distinct().order_by('order', 'date_echeance')
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
    if emp.notification_enabled:
        now = datetime.now().date()
        max_date = now + timedelta(hours=emp.notification_interval_hours)
        upcoming_taches = queryset.filter(statut='Pending', date_echeance__lte=max_date).order_by('date_echeance')

    # Precompute collaborators for display and attach to objects for easy template access
    collabs = TacheCollaboration.objects.filter(tache__in=queryset).select_related('tache', 'collaborator')
    accepted_map = {}
    pending_count = {}
    for c in collabs:
        tid = c.tache_id
        if c.status == 'accepted':
            accepted_map.setdefault(tid, []).append(c.collaborator)
        elif c.status == 'pending':
            pending_count[tid] = pending_count.get(tid, 0) + 1
    # Attach to each task
    for t in queryset:
        setattr(t, 'accepted_collaborators', accepted_map.get(t.idTache, []))
        setattr(t, 'pending_collab_count', pending_count.get(t.idTache, 0))

    return render(request, 'tache/doctor_tache_list.html', {
        'employee': emp,
        'taches': queryset,
        'filter_statut': statut or '',
        'filter_date_from': date_from or '',
        'filter_date_to': date_to or '',
        'upcoming_taches': upcoming_taches,
        'today': datetime.now().date(),
    # attached per-task attributes used in templates
    })


class NotificationPreferencesForm(forms.Form):
    notification_enabled = forms.BooleanField(required=False, label="Activer les notifications")
    notification_interval_hours = forms.IntegerField(min_value=1, label="Intervalle (heures)")


def notification_preferences(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    try:
        emp = Employe.objects.get(pk=emp_id)
    except Employe.DoesNotExist:
        return redirect('tache:login')

    if emp.role not in ('medecin', 'infirmiere'):
        return HttpResponseForbidden('Accès refusé')

    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST)
        if form.is_valid():
            emp.notification_enabled = form.cleaned_data['notification_enabled']
            emp.notification_interval_hours = form.cleaned_data['notification_interval_hours']
            emp.save()
            return HttpResponseRedirect(reverse('tache:dashboard'))
    else:
        form = NotificationPreferencesForm(initial={
            'notification_enabled': emp.notification_enabled,
            'notification_interval_hours': emp.notification_interval_hours,
        })

    return render(request, 'tache/notification_preferences.html', {'employee': emp, 'form': form})


def doctor_create_tache(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
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
            return redirect('tache:doctor_list_taches')
        employee_hidden = True
    else:
        form = TacheForm(initial={'employee': emp.pk})
        form.fields['employee'].widget = forms.HiddenInput()
        employee_hidden = True

    return render(request, 'tache/doctor_tache_form.html', {'form': form, 'employee': emp, 'employee_hidden': employee_hidden})


def doctor_edit_tache(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
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
            return redirect('tache:doctor_list_taches')
        employee_hidden = True
    else:
        form = TacheForm(instance=t)
        form.fields['employee'].widget = forms.HiddenInput()
        employee_hidden = True

    return render(request, 'tache/doctor_tache_form.html', {'form': form, 'employee': emp, 'tache': t, 'employee_hidden': employee_hidden})


@require_POST
def doctor_delete_tache(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
        return HttpResponseForbidden('Accès refusé')

    try:
        t = Tache.objects.get(pk=pk, employee=emp)
    except Tache.DoesNotExist:
        return HttpResponseForbidden('Tâche introuvable')

    t.delete()
    return redirect('tache:doctor_list_taches')


def choose_collaborator(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
        return HttpResponseForbidden('Accès refusé')

    try:
        t = Tache.objects.get(pk=pk, employee=emp)
    except Tache.DoesNotExist:
        return HttpResponseForbidden('Tâche introuvable')

    if request.method == 'POST':
        form = CollaboratorForm(request.POST, current_emp=emp)
        if form.is_valid():
            selected = form.cleaned_data['collaborators']
            existing_ids = set(TacheCollaboration.objects.filter(tache=t).values_list('collaborator_id', flat=True))
            to_create = [c for c in selected if c.id not in existing_ids]
            for c in to_create:
                TacheCollaboration.objects.create(tache=t, collaborator=c, status='pending')
            messages.success(request, 'Invitations envoyées.')
            return redirect('tache:doctor_list_taches')
    else:
        form = CollaboratorForm(current_emp=emp)

    return render(request, 'tache/choose_collaborator.html', {'form': form, 'tache': t, 'employee': emp})


class NoteForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), max_length=2000, label='Ajouter une note')


class AttachmentForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), label='Ajouter un fichier')


def task_notes_files(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)

    # access if owner or accepted collaborator
    try:
        t = Tache.objects.get(pk=pk)
    except Tache.DoesNotExist:
        return HttpResponseForbidden('Tâche introuvable')
    is_accepted_collab = TacheCollaboration.objects.filter(tache=t, collaborator=emp, status='accepted').exists()
    if not (t.employee_id == emp.id or is_accepted_collab):
        return HttpResponseForbidden('Accès refusé')

    note_form = NoteForm()
    attachment_form = AttachmentForm()

    if request.method == 'POST':
        if 'add_note' in request.POST:
            note_form = NoteForm(request.POST)
            if note_form.is_valid():
                TacheNote.objects.create(tache=t, author=emp, content=note_form.cleaned_data['content'])
                return redirect('tache:task_notes_files', pk=pk)
        elif 'add_file' in request.POST:
            attachment_form = AttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid() and request.FILES.get('file'):
                f = request.FILES['file']
                TacheAttachment.objects.create(
                    tache=t, uploaded_by=emp, file=f, original_name=f.name
                )
                return redirect('tache:task_notes_files', pk=pk)

    notes = t.notes.select_related('author').all()
    files = t.attachments.all()
    return render(request, 'tache/task_notes_files.html', {
        'employee': emp,
        'tache': t,
        'notes': notes,
        'files': files,
        'note_form': note_form,
        'attachment_form': attachment_form,
    })


def ai_suggest_order(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
        return HttpResponseForbidden('Accès refusé')

    tasks = list(Tache.objects.filter(employee=emp).order_by('order', 'date_echeance'))
    if not tasks:
        return render(request, 'tache/ai_suggest_order.html', {
            'employee': emp, 'current_tasks': [], 'suggested_tasks': [], 'suggest_ids_json': '[]',
            'used_ai': False, 'error': None,
        })

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    used_ai = False
    error = None
    suggested_ids = []

    # Build textual prompt using id, description, and due date
    items = [f"task{t.idTache}:{t.description} (due {t.date_echeance.isoformat()})" for t in tasks]
    content = (
        "order these tasks based on the highest priority (give only the task numbers separated by commas): "
        + ", ".join(items)
    )

    try:
        from google import genai
        if not api_key:
            error = "GEMINI_API_KEY non défini dans l'environnement."
        else:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content,
            )
            text = getattr(response, 'text', '') or ''
            # Write to result.txt at project root
            out_path = Path(settings.BASE_DIR) / 'result.txt'
            out_path.write_text(text, encoding='utf-8')
            # Parse task ids from response: prefer 'task<id>' tokens, fallback to plain numbers
            import re
            task_tokens = re.findall(r"task\s*(\d+)", text, flags=re.IGNORECASE)
            if task_tokens:
                found = [int(x) for x in task_tokens]
            else:
                found = [int(x) for x in re.findall(r"\b(\d+)\b", text)]
            valid_ids = {t.idTache for t in tasks}
            ordered_unique = []
            seen = set()
            for n in found:
                if n in valid_ids and n not in seen:
                    ordered_unique.append(n)
                    seen.add(n)
            suggested_ids = ordered_unique
            used_ai = bool(suggested_ids)
    except ImportError:
        error = "Module google-genai non installé. Installez-le avec: pip install google-genai"
    except Exception as e:
        error = f"Échec de l'appel AI: {e}"

    id_to_task = {t.idTache: t for t in tasks}
    suggested_tasks = [id_to_task[i] for i in suggested_ids if i in id_to_task]
    return render(request, 'tache/ai_suggest_order.html', {
        'employee': emp,
        'current_tasks': tasks,
        'suggested_tasks': suggested_tasks,
        'suggest_ids_json': json.dumps(suggested_ids),
        'used_ai': used_ai,
        'error': error,
    })


@require_POST
def ai_apply_order(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role != 'medecin':
        return HttpResponseForbidden('Accès refusé')

    try:
        suggested = json.loads(request.POST.get('order', '[]'))
        if not isinstance(suggested, list):
            suggested = []
    except Exception:
        suggested = []

    tasks = list(Tache.objects.filter(employee=emp))
    id_to_task = {t.idTache: t for t in tasks}
    # Apply new order: suggested first in given sequence, then the rest
    new_seq = [tid for tid in suggested if tid in id_to_task]
    remaining = [tid for tid in id_to_task.keys() if tid not in set(new_seq)]
    final = new_seq + remaining
    for idx, tid in enumerate(final, start=1):
        t = id_to_task[tid]
        t.order = idx
        t.save()

    messages.success(request, 'Nouvel ordre appliqué.')
    return redirect('tache:doctor_list_taches')


def collab_invitations(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role not in ('medecin', 'infirmiere'):
        return HttpResponseForbidden('Accès refusé')
    pending = TacheCollaboration.objects.filter(collaborator=emp, status='pending').select_related('tache', 'tache__employee')
    accepted = TacheCollaboration.objects.filter(collaborator=emp, status='accepted').select_related('tache', 'tache__employee')
    return render(request, 'tache/collab_invitations.html', {
        'employee': emp,
        'pending': pending,
        'accepted': accepted,
    })


@require_POST
def collab_accept(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role not in ('medecin', 'infirmiere'):
        return HttpResponseForbidden('Accès refusé')
    try:
        collab = TacheCollaboration.objects.get(pk=pk, collaborator=emp, status='pending')
    except TacheCollaboration.DoesNotExist:
        return HttpResponseForbidden('Invitation introuvable')
    from django.utils import timezone
    collab.status = 'accepted'
    collab.responded_at = timezone.now()
    collab.save()
    return redirect('tache:collab_invitations')


@require_POST
def collab_decline(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    emp = Employe.objects.get(pk=emp_id)
    if emp.role not in ('medecin', 'infirmiere'):
        return HttpResponseForbidden('Accès refusé')
    try:
        collab = TacheCollaboration.objects.get(pk=pk, collaborator=emp, status='pending')
    except TacheCollaboration.DoesNotExist:
        return HttpResponseForbidden('Invitation introuvable')
    from django.utils import timezone
    collab.status = 'declined'
    collab.responded_at = timezone.now()
    collab.save()
    return redirect('tache:collab_invitations')


def login_view(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')
        try:
            emp = Employe.objects.get(login=login, mot_de_passe=password)
        except Employe.DoesNotExist:
            messages.error(request, 'Identifiants invalides')
            return render(request, 'tache/login.html')

        request.session['employee_id'] = emp.pk
        return redirect('tache:dashboard')

    return render(request, 'tache/login.html')


def logout_view(request):
    request.session.pop('employee_id', None)
    return redirect('/')


def dashboard_redirect(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    try:
        emp = Employe.objects.get(pk=emp_id)
    except Employe.DoesNotExist:
        return redirect('tache:login')

    role = emp.role
    if role == 'medecin':
        return redirect('tache:doctor_list_taches')
    if role == 'infirmiere':
        queryset = Tache.objects.filter(
            Q(employee=emp) | Q(collaborations__collaborator=emp, collaborations__status='accepted')
        ).distinct().order_by('order', 'date_echeance')
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
        if emp.notification_enabled:
            now = datetime.now().date()
            max_date = now + timedelta(hours=emp.notification_interval_hours)
            upcoming_taches = queryset.filter(statut='Pending', date_echeance__lte=max_date).order_by('date_echeance')

        # Attach collaborator info for template: find current user's collab status per task
        collabs = TacheCollaboration.objects.filter(tache__in=queryset, collaborator=emp).select_related('tache')
        collab_status_by_task = {c.tache_id: c.collab_statut for c in collabs}
        for t in queryset:
            setattr(t, 'my_collab_statut', collab_status_by_task.get(t.idTache, 'Pending'))

        return render(request, 'tache/dashboard_infirmier.html', {
            'employee': emp,
            'taches': queryset,
            'filter_statut': statut or '',
            'filter_date_from': date_from or '',
            'filter_date_to': date_to or '',
            'upcoming_taches': upcoming_taches,
            'today': datetime.now().date(),
        })
    if role == 'Gestionnaire de Materiel':
        return render(request, 'tache/dashboard_gestionnaire.html', {'employee': emp})
    return render(request, 'tache/dashboard_generic.html', {'employee': emp})


@require_POST
def update_task_status(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    try:
        emp = Employe.objects.get(pk=emp_id)
    except Employe.DoesNotExist:
        return redirect('tache:login')

    try:
        t = Tache.objects.get(pk=pk)
    except Tache.DoesNotExist:
        return HttpResponseForbidden('Tâche introuvable')

    if t.employee.pk != emp.pk:
        return HttpResponseForbidden('Vous n\'êtes pas autorisé à modifier cette tâche')

    new_status = request.POST.get('statut')
    if new_status not in ('Pending', 'Done'):
        return HttpResponseForbidden('Statut invalide')

    t.statut = new_status
    t.save()

    return redirect(request.META.get('HTTP_REFERER', '/tache/dashboard/'))


@require_POST
def update_collab_status(request, pk):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    try:
        emp = Employe.objects.get(pk=emp_id)
    except Employe.DoesNotExist:
        return redirect('tache:login')

    # Only collaborators with accepted status can update their personal status
    try:
        t = Tache.objects.get(pk=pk)
    except Tache.DoesNotExist:
        return HttpResponseForbidden('Tâche introuvable')

    try:
        collab = TacheCollaboration.objects.get(tache=t, collaborator=emp, status='accepted')
    except TacheCollaboration.DoesNotExist:
        return HttpResponseForbidden('Vous n\'êtes pas autorisé à modifier cette tâche')

    new_status = request.POST.get('statut')
    if new_status not in ('Pending', 'Done'):
        return HttpResponseForbidden('Statut invalide')

    collab.collab_statut = new_status
    collab.responded_at = timezone.now()
    collab.save()

    return redirect(request.META.get('HTTP_REFERER', '/tache/dashboard/'))


@require_POST
def reorder_tasks(request):
    emp_id = request.session.get('employee_id')
    if not emp_id:
        return redirect('tache:login')
    try:
        emp = Employe.objects.get(pk=emp_id)
    except Employe.DoesNotExist:
        return redirect('tache:login')

    if emp.role not in ('medecin', 'infirmiere'):
        return HttpResponseForbidden('Accès refusé')

    try:
        import json
        payload = json.loads(request.body.decode('utf-8'))
        new_order = payload.get('order', [])
    except Exception:
        return HttpResponseForbidden('Payload invalide')

    taches = Tache.objects.filter(employee=emp, idTache__in=new_order)
    if taches.count() != len(new_order):
        return HttpResponseForbidden('Tâches invalides')

    order_map = {tid: idx + 1 for idx, tid in enumerate(new_order)}
    for t in taches:
        t.order = order_map.get(t.idTache, t.order)
        t.save()

    remaining = Tache.objects.filter(employee=emp).exclude(idTache__in=new_order).order_by('order', 'date_echeance')
    last_index = len(new_order)
    for offset, t in enumerate(remaining, start=1):
        if t.order <= last_index:
            t.order = last_index + offset
            t.save()

    from django.http import JsonResponse
    return JsonResponse({'status': 'ok'})




# from django.shortcuts import render
# # Create your views here.
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from EmployeApp.models import Employe
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
# 		return redirect('tache:login')
# 	emp = Employe.objects.get(pk=emp_id)
# 	if emp.role != 'medecin':
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
