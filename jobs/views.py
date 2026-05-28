from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from .models import Job, Application
from .forms import JobForm, ApplicationForm
from notifications.models import Notification


def job_list(request):
    jobs = Job.objects.filter(estado=Job.Estado.DISPONIBLE)
    q = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    modalidad = request.GET.get('modalidad', '')
    ubicacion = request.GET.get('ubicacion', '')

    if q:
        jobs = jobs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
    if categoria:
        jobs = jobs.filter(categoria=categoria)
    if modalidad:
        jobs = jobs.filter(modalidad=modalidad)
    if ubicacion:
        jobs = jobs.filter(ubicacion__icontains=ubicacion)

    # Get distinct cities for the filter dropdown
    ciudades = (
        Job.objects.filter(estado=Job.Estado.DISPONIBLE)
        .exclude(ubicacion='')
        .values_list('ubicacion', flat=True)
        .distinct()
    )

    return render(request, 'jobs/job_list.html', {
        'jobs': jobs,
        'q': q,
        'categoria': categoria,
        'modalidad': modalidad,
        'ubicacion': ubicacion,
        'categorias': Job.Categoria.choices,
        'modalidades': Job.Modalidad.choices,
        'ciudades': ciudades,
    })


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    user_applied = False
    user_application_pending = False
    if request.user.is_authenticated:
        application = job.postulaciones.filter(usuario=request.user).first()
        if application:
            user_applied = True
            user_application_pending = application.estado == Application.Estado.PENDIENTE
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'user_applied': user_applied,
        'user_application_pending': user_application_pending,
    })


@login_required
def job_create(request):
    if request.user.es_estudiante:
        messages.error(request, 'Los estudiantes no pueden publicar trabajos.')
        return redirect('jobs:job_list')
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.creador = request.user
            job.save()
            messages.success(request, 'Trabajo publicado exitosamente.')
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form, 'titulo_pagina': 'Publicar trabajo'})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trabajo actualizado.')
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/job_form.html', {'form': form, 'titulo_pagina': 'Editar trabajo'})


@login_required
def job_apply(request, pk):
    if not request.user.es_estudiante:
        messages.error(request, 'Solo los estudiantes pueden postularse a trabajos.')
        return redirect('jobs:job_detail', pk=pk)
    job = get_object_or_404(Job, pk=pk, estado=Job.Estado.DISPONIBLE)
    if job.creador == request.user:
        messages.error(request, 'No puedes postularte a tu propio trabajo.')
        return redirect('jobs:job_detail', pk=pk)
    if Application.objects.filter(usuario=request.user, trabajo=job).exists():
        messages.warning(request, 'Ya te postulaste a este trabajo.')
        return redirect('jobs:job_detail', pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.usuario = request.user
            application.trabajo = job
            application.save()
            # Notify employer
            Notification.objects.create(
                usuario=job.creador,
                tipo=Notification.Tipo.POSTULACION,
                mensaje=f'{request.user.get_full_name() or request.user.username} se postuló a "{job.titulo}".',
                link=reverse('jobs:job_applicants', args=[job.pk]),
            )
            messages.success(request, '¡Postulación enviada!')
            return redirect('jobs:job_detail', pk=pk)
    else:
        form = ApplicationForm()
    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


@login_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user)
    aplicaciones = job.postulaciones.select_related('usuario').all()
    return render(request, 'jobs/applicants.html', {'job': job, 'aplicaciones': aplicaciones})


@login_required
def accept_applicant(request, pk, app_id):
    job = get_object_or_404(Job, pk=pk, creador=request.user, estado=Job.Estado.DISPONIBLE)
    application = get_object_or_404(Application, pk=app_id, trabajo=job)
    application.estado = Application.Estado.ACEPTADA
    application.save()
    job.asignado = application.usuario
    job.estado = Job.Estado.EN_PROCESO
    job.save()
    # Rechazar las demás postulaciones
    rejected_qs = job.postulaciones.exclude(pk=app_id)
    rejected_users = list(rejected_qs.values_list('usuario', flat=True))
    rejected_qs.update(estado=Application.Estado.RECHAZADA)
    # Notify accepted student
    Notification.objects.create(
        usuario=application.usuario,
        tipo=Notification.Tipo.ACEPTADO,
        mensaje=f'¡Felicitaciones! Fuiste aceptado para "{job.titulo}".',
        link=reverse('jobs:job_detail', args=[job.pk]),
    )
    # Notify rejected students
    from django.contrib.auth import get_user_model
    User = get_user_model()
    for uid in rejected_users:
        Notification.objects.create(
            usuario_id=uid,
            tipo=Notification.Tipo.RECHAZADO,
            mensaje=f'Tu postulación a "{job.titulo}" no fue seleccionada.',
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
    messages.success(request, f'{application.usuario} ha sido asignado al trabajo.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def job_finish(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user, estado=Job.Estado.EN_PROCESO)
    job.estado = Job.Estado.FINALIZADO
    job.save()
    # Notify assigned student
    if job.asignado:
        Notification.objects.create(
            usuario=job.asignado,
            tipo=Notification.Tipo.FINALIZADO,
            mensaje=f'El trabajo "{job.titulo}" ha sido marcado como finalizado.',
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
    messages.success(request, 'Trabajo marcado como finalizado.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def job_change_status(request, pk):
    if request.method != 'POST':
        return redirect('jobs:job_detail', pk=pk)
    job = get_object_or_404(Job, pk=pk, creador=request.user)
    new_status = request.POST.get('estado')
    valid = {c[0] for c in Job.Estado.choices}
    if new_status not in valid:
        messages.error(request, 'Estado no válido.')
        return redirect('jobs:job_detail', pk=pk)
    job.estado = new_status
    job.save()
    # Notify assigned student when finished
    if new_status == Job.Estado.FINALIZADO and job.asignado:
        Notification.objects.create(
            usuario=job.asignado,
            tipo=Notification.Tipo.FINALIZADO,
            mensaje=f'El trabajo "{job.titulo}" ha sido marcado como finalizado.',
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
    labels = {'disponible': 'Disponible', 'en_proceso': 'En proceso', 'finalizado': 'Finalizado'}
    messages.success(request, f'Estado cambiado a: {labels.get(new_status, new_status)}.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user)
    if job.estado == Job.Estado.EN_PROCESO:
        messages.error(request, 'No puedes eliminar un trabajo que está en proceso.')
        return redirect('jobs:job_detail', pk=pk)
    if request.method == 'POST':
        titulo = job.titulo
        job.delete()
        messages.success(request, f'"{titulo}" fue eliminado.')
        return redirect('jobs:my_jobs')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def cancel_application(request, pk):
    job = get_object_or_404(Job, pk=pk)
    application = get_object_or_404(Application, trabajo=job, usuario=request.user)
    if application.estado != Application.Estado.PENDIENTE:
        messages.error(request, 'Solo puedes cancelar postulaciones pendientes.')
        return redirect('jobs:job_detail', pk=pk)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Postulación cancelada.')
        return redirect('jobs:job_list')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def my_jobs(request):
    user = request.user
    if user.es_estudiante:
        asignados = Job.objects.filter(asignado=user).order_by('-created_at')
        postulados = Job.objects.filter(postulaciones__usuario=user).distinct().order_by('-created_at')
        return render(request, 'jobs/my_jobs.html', {
            'asignados': asignados,
            'postulados': postulados,
            'is_student': True,
        })
    else:
        base_qs = Job.objects.filter(creador=user)
        disponibles = base_qs.filter(estado=Job.Estado.DISPONIBLE).order_by('-created_at')
        en_proceso = base_qs.filter(estado=Job.Estado.EN_PROCESO).order_by('-created_at')
        finalizados = base_qs.filter(estado=Job.Estado.FINALIZADO).order_by('-created_at')
        return render(request, 'jobs/my_jobs.html', {
            'disponibles': disponibles,
            'en_proceso_jobs': en_proceso,
            'finalizados_jobs': finalizados,
            'total_creados': base_qs.count(),
            'is_student': False,
        })
