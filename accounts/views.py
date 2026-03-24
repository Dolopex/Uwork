from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from .forms import StudentRegisterForm, EmployerRegisterForm, ProfileForm
from .models import User


def role_select(request):
    """Primera vista: ¿Eres estudiante o necesitas un trabajo hecho?"""
    if request.user.is_authenticated:
        return redirect('jobs:job_list')
    return render(request, 'accounts/role_select.html')


def register_student(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido a U-Work, estudiante!')
            return redirect('jobs:job_list')
    else:
        form = StudentRegisterForm()
    return render(request, 'accounts/register_student.html', {'form': form})


def register_employer(request):
    if request.method == 'POST':
        form = EmployerRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido a U-Work!')
            return redirect('jobs:job_list')
    else:
        form = EmployerRegisterForm()
    return render(request, 'accounts/register_employer.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'accounts/user_detail.html', {'profile_user': user})


@login_required
def balance(request):
    from jobs.models import Job, Application

    user = request.user

    # Jobs created by user
    trabajos_creados = Job.objects.filter(creador=user)
    total_publicados = trabajos_creados.count()
    publicados_disponibles = trabajos_creados.filter(estado=Job.Estado.DISPONIBLE).count()
    publicados_en_proceso = trabajos_creados.filter(estado=Job.Estado.EN_PROCESO).count()
    publicados_finalizados = trabajos_creados.filter(estado=Job.Estado.FINALIZADO).count()
    total_gastado = trabajos_creados.filter(estado=Job.Estado.FINALIZADO).aggregate(total=Sum('pago'))['total'] or 0

    # Applications by user
    postulaciones = Application.objects.filter(usuario=user)
    total_postulaciones = postulaciones.count()
    postulaciones_pendientes = postulaciones.filter(estado=Application.Estado.PENDIENTE).count()
    postulaciones_aceptadas = postulaciones.filter(estado=Application.Estado.ACEPTADA).count()
    postulaciones_rechazadas = postulaciones.filter(estado=Application.Estado.RECHAZADA).count()

    # Jobs assigned to user (earnings)
    trabajos_asignados = Job.objects.filter(asignado=user)
    total_asignados = trabajos_asignados.count()
    asignados_finalizados = trabajos_asignados.filter(estado=Job.Estado.FINALIZADO).count()
    total_ganado = trabajos_asignados.filter(estado=Job.Estado.FINALIZADO).aggregate(total=Sum('pago'))['total'] or 0
    asignados_en_proceso = trabajos_asignados.filter(estado=Job.Estado.EN_PROCESO).count()

    # Reviews
    reviews_recibidas = user.reviews_recibidas.count()
    reviews_realizadas = user.reviews_hechas.count()

    # Category breakdown for chart
    categorias_data = []
    if user.es_estudiante:
        cat_qs = trabajos_asignados.values('categoria').annotate(total=Count('id')).order_by('-total')
    else:
        cat_qs = trabajos_creados.values('categoria').annotate(total=Count('id')).order_by('-total')

    cat_colors = {
        'academico': '#4F46E5', 'tecnologia': '#2563EB', 'diseno': '#7C3AED',
        'redaccion': '#D97706', 'traduccion': '#059669', 'otro': '#6B7280',
    }
    cat_labels = dict(Job.Categoria.choices)
    for item in cat_qs:
        categorias_data.append({
            'nombre': cat_labels.get(item['categoria'], item['categoria']),
            'total': item['total'],
            'color': cat_colors.get(item['categoria'], '#6B7280'),
        })

    # Monthly activity (last 6 months)
    from django.utils import timezone
    import datetime
    now = timezone.now()
    meses = []
    for i in range(5, -1, -1):
        d = now - datetime.timedelta(days=30 * i)
        month_start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_d = now - datetime.timedelta(days=30 * (i - 1))
            month_end = next_d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = now

        if user.es_estudiante:
            count = Application.objects.filter(
                usuario=user,
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).count()
        else:
            count = Job.objects.filter(
                creador=user,
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).count()

        meses.append({
            'label': month_start.strftime('%b'),
            'count': count,
        })

    max_mes = max((m['count'] for m in meses), default=1) or 1

    context = {
        'total_publicados': total_publicados,
        'publicados_disponibles': publicados_disponibles,
        'publicados_en_proceso': publicados_en_proceso,
        'publicados_finalizados': publicados_finalizados,
        'total_gastado': total_gastado,
        'total_postulaciones': total_postulaciones,
        'postulaciones_pendientes': postulaciones_pendientes,
        'postulaciones_aceptadas': postulaciones_aceptadas,
        'postulaciones_rechazadas': postulaciones_rechazadas,
        'total_asignados': total_asignados,
        'asignados_finalizados': asignados_finalizados,
        'asignados_en_proceso': asignados_en_proceso,
        'total_ganado': total_ganado,
        'reviews_recibidas': reviews_recibidas,
        'reviews_realizadas': reviews_realizadas,
        'categorias_data': categorias_data,
        'meses': meses,
        'max_mes': max_mes,
    }
    return render(request, 'accounts/balance.html', context)
