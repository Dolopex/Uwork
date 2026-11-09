from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Job, Application
from .forms import JobForm, ApplicationForm
from notifications.models import Notification


def job_list(request):
    # Solo se listan los trabajos aprobados por moderación y que no han
    # vencido (P1-4): un trabajo con fecha límite pasada deja de ser una
    # oferta abierta.
    jobs = Job.objects.filter(
        estado=Job.Estado.DISPONIBLE,
    ).exclude(fecha_limite__lt=timezone.localdate())

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
    # Un trabajo pendiente de moderación o rechazado no es público: solo lo
    # ve su autor (y el personal de moderación).
    if not job.visible and job.creador_id != getattr(request.user, 'pk', None):
        if not (request.user.is_authenticated and request.user.is_staff):
            messages.error(request, 'Esta publicación no está disponible.')
            return redirect('jobs:job_list')
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
            # §6.5.4 — moderación previa a publicar: el trabajo no se hace
            # público hasta que un moderador lo aprueba (Términos §6).
            job.estado = Job.Estado.PENDIENTE_REVISION
            job.save()
            messages.success(
                request,
                'Trabajo enviado a revisión. Se publicará cuando un '
                'moderador lo apruebe.')
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
            job = form.save(commit=False)
            # Editar una publicación la devuelve a revisión: el contenido
            # modificado es contenido nuevo y no puede quedar publicado sin
            # que un moderador lo vea.
            if job.estado in (Job.Estado.DISPONIBLE, Job.Estado.RECHAZADO):
                job.estado = Job.Estado.PENDIENTE_REVISION
                job.motivo_rechazo = ''
            job.save()
            messages.success(
                request,
                'Trabajo actualizado y enviado a revisión. Volverá a estar '
                'visible cuando un moderador lo apruebe.')
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
    # P1-4 — la fecha límite deja de ser decorativa.
    if job.es_vencido:
        messages.error(request, 'Este trabajo ya cerró sus postulaciones.')
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
@require_POST
def accept_applicant(request, pk, app_id):
    """Acepta un postulante.

    POST obligatorio (P0-1 del audit): con GET, un `<img src>` dentro de un
    correo bastaba para aceptar a un postulante sin la consentimiento del
    empleador y sin token CSRF.
    """
    job = get_object_or_404(Job, pk=pk, creador=request.user, estado=Job.Estado.DISPONIBLE)
    if job.es_vencido:
        messages.error(request, 'Este trabajo ya cerró sus postulaciones.')
        return redirect('jobs:job_detail', pk=pk)
    application = get_object_or_404(Application, pk=app_id, trabajo=job)
    if application.estado != Application.Estado.PENDIENTE:
        messages.info(request, 'Esa postulación ya había sido procesada.')
        return redirect('jobs:job_applicants', pk=pk)
    application.estado = Application.Estado.ACEPTADA
    application.save(update_fields=['estado'])
    job.asignado = application.usuario
    job.estado = Job.Estado.EN_PROCESO
    job.save(update_fields=['asignado', 'estado'])
    # Rechazar las demás postulaciones
    rejected_qs = job.postulaciones.exclude(pk=app_id).exclude(
        estado=Application.Estado.ACEPTADA)
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
@require_POST
def job_finish(request, pk):
    """Marca el trabajo como finalizado.

    POST obligatorio: con GET, un `<img src>` en un correo finalizaba el
    trabajo sin que el empleador hubiera tomado la decisión.
    """
    job = get_object_or_404(Job, pk=pk, creador=request.user, estado=Job.Estado.EN_PROCESO)
    job.estado = Job.Estado.FINALIZADO
    job.save(update_fields=['estado'])
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
@require_POST
def job_change_status(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user)
    new_status = request.POST.get('estado')
    if new_status not in {c[0] for c in Job.Estado.choices}:
        messages.error(request, 'Estado no válido.')
        return redirect('jobs:job_detail', pk=pk)
    if new_status == job.estado:
        return redirect('jobs:job_detail', pk=pk)
    # Máquina de estados: no se puede reabrir un trabajo finalizado (eso
    # invalidaría las reseñas ya dadas) ni saltarse la revisión previa.
    if not job.puede_transicionar_a(new_status):
        messages.error(
            request,
            'No se puede cambiar el estado de "{}" a "{}".'.format(
                job.get_estado_display(),
                dict(Job.Estado.choices).get(new_status, new_status)))
        return redirect('jobs:job_detail', pk=pk)
    job.estado = new_status
    job.save(update_fields=['estado'])
    # Notify assigned student when finished
    if new_status == Job.Estado.FINALIZADO and job.asignado:
        Notification.objects.create(
            usuario=job.asignado,
            tipo=Notification.Tipo.FINALIZADO,
            mensaje=f'El trabajo "{job.titulo}" ha sido marcado como finalizado.',
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
    messages.success(request, f'Estado cambiado a: {job.get_estado_display()}.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
@require_POST
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
@require_POST
def cancel_application(request, pk):
    job = get_object_or_404(Job, pk=pk)
    application = get_object_or_404(Application, trabajo=job, usuario=request.user)
    if application.estado != Application.Estado.PENDIENTE:
        messages.error(request, 'Solo puedes cancelar postulaciones pendientes.')
        return redirect('jobs:job_detail', pk=pk)
    application.delete()
    messages.success(request, 'Postulación cancelada.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def my_jobs(request):
    """Panel de "mis trabajos".

    Para el estudiante son *sus postulaciones* con el estado de cada una
    (pendiente / aceptada / rechazada): antes la vista mostraba los
    trabajos a los que se postuló, sin decir si su postulación quedó
    aceptada o rechazada.
    """
    user = request.user
    if user.es_estudiante:
        asignados = Job.objects.filter(asignado=user).order_by('-created_at')
        mis_postulaciones = (
            Application.objects.filter(usuario=user)
            .select_related('trabajo', 'trabajo__creador')
            .order_by('-created_at')
        )
        return render(request, 'jobs/my_jobs.html', {
            'asignados': asignados,
            'mis_postulaciones': mis_postulaciones,
            # P1 — `asignados.filter.count` en la plantilla no filtraba nada
            # y además disparaba un COUNT extra.
            'asignados_finalizados': asignados.filter(
                estado=Job.Estado.FINALIZADO).count(),
            'asignados_en_proceso': asignados.filter(
                estado=Job.Estado.EN_PROCESO).count(),
            'is_student': True,
        })
    else:
        base_qs = Job.objects.filter(creador=user)
        pendientes = base_qs.filter(
            estado=Job.Estado.PENDIENTE_REVISION).order_by('-created_at')
        disponibles = base_qs.filter(estado=Job.Estado.DISPONIBLE).order_by('-created_at')
        en_proceso = base_qs.filter(estado=Job.Estado.EN_PROCESO).order_by('-created_at')
        finalizados = base_qs.filter(estado=Job.Estado.FINALIZADO).order_by('-created_at')
        rechazados = base_qs.filter(estado=Job.Estado.RECHAZADO).order_by('-created_at')
        return render(request, 'jobs/my_jobs.html', {
            'pendientes_revision': pendientes,
            'disponibles': disponibles,
            'en_proceso_jobs': en_proceso,
            'finalizados_jobs': finalizados,
            'rechazados_jobs': rechazados,
            'total_creados': base_qs.count(),
            'is_student': False,
        })
