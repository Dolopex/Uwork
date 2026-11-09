from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from jobs.models import Job
from notifications.models import Notification
from .models import Review
from .forms import ReviewForm


@login_required
def create_review(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk, estado=Job.Estado.FINALIZADO)
    # Determinar a quién se califica
    if request.user == job.creador:
        receptor = job.asignado
    elif request.user == job.asignado:
        receptor = job.creador
    else:
        messages.error(request, 'No participaste en este trabajo.')
        return redirect('jobs:job_detail', pk=job_pk)

    if receptor is None:
        messages.error(request, 'No hay usuario para calificar.')
        return redirect('jobs:job_detail', pk=job_pk)

    if Review.objects.filter(autor=request.user, receptor=receptor, trabajo=job).exists():
        messages.warning(request, 'Ya calificaste a este usuario para este trabajo.')
        return redirect('jobs:job_detail', pk=job_pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.autor = request.user
            review.receptor = receptor
            review.trabajo = job
            review.save()
            # El promedio del receptor lo recalcula la señal post_save de
            # reviews.signals (también cuando se borra una reseña).
            # Aviso al usuario calificado.
            Notification.objects.create(
                usuario=receptor,
                tipo=Notification.Tipo.RESENA,
                mensaje='Recibiste una nueva calificación por "{}".'.format(
                    job.titulo),
                link=reverse('jobs:job_detail', args=[job.pk]),
            )
            messages.success(request, '¡Calificación enviada!')
            return redirect('jobs:job_detail', pk=job_pk)
    else:
        form = ReviewForm()
    return render(request, 'reviews/create_review.html', {'form': form, 'job': job, 'receptor': receptor})
