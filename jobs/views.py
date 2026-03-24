from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application
from .forms import JobForm, ApplicationForm


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
    if request.user.is_authenticated:
        user_applied = job.postulaciones.filter(usuario=request.user).exists()
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'user_applied': user_applied,
    })


@login_required
def job_create(request):
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
    job.postulaciones.exclude(pk=app_id).update(estado=Application.Estado.RECHAZADA)
    messages.success(request, f'{application.usuario} ha sido asignado al trabajo.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def job_finish(request, pk):
    job = get_object_or_404(Job, pk=pk, creador=request.user, estado=Job.Estado.EN_PROCESO)
    job.estado = Job.Estado.FINALIZADO
    job.save()
    messages.success(request, 'Trabajo marcado como finalizado.')
    return redirect('jobs:job_detail', pk=pk)


@login_required
def my_jobs(request):
    creados = Job.objects.filter(creador=request.user)
    asignados = Job.objects.filter(asignado=request.user)
    postulados = Job.objects.filter(postulaciones__usuario=request.user).distinct()
    return render(request, 'jobs/my_jobs.html', {
        'creados': creados,
        'asignados': asignados,
        'postulados': postulados,
    })
