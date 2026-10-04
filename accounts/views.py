from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from .forms import StudentRegisterForm, EmployerRegisterForm, StudentProfileForm, EmployerProfileForm
from .models import User
from .services import enviar_email_verificacion


def role_select(request):
    """Primera vista: ¿Eres estudiante o necesitas un trabajo hecho?"""
    if request.user.is_authenticated:
        return redirect('jobs:job_list')
    return render(request, 'accounts/role_select.html')


def _registrar_y_verificar(request, form, template):
    """Guarda la cuenta, envía el correo de verificación y no inicia sesión.

    R11 — la cuenta queda inactiva hasta que el usuario haga clic en el
    enlace de confirmación, así que no se llama a login() aquí.
    """
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        enviar_email_verificacion(user)
        request.session['pending_verification_email'] = user.email
        messages.success(
            request,
            '¡Cuenta creada! Revisa tu correo ({}) para activarla.'.format(
                user.email),
        )
        return redirect('accounts:check_email')
    return render(request, template, {'form': form})


def register_student(request):
    form = StudentRegisterForm(request.POST or None, request.FILES or None)
    return _registrar_y_verificar(
        request, form, 'accounts/register_student.html')


def register_employer(request):
    form = EmployerRegisterForm(request.POST or None, request.FILES or None)
    return _registrar_y_verificar(
        request, form, 'accounts/register_employer.html')


# ── R11 — Verificación de email ────────────────────────────────

def check_email(request):
    """Pantalla intermedia: 'revisa tu correo' tras registrarse."""
    email = request.session.pop('pending_verification_email', '')
    return render(request, 'accounts/check_email.html', {'email': email})


def verify_email(request, token):
    """Confirma la cuenta al hacer clic en el enlace del correo."""
    try:
        user = User.objects.get(email_verification_token=token)
    except (User.DoesNotExist, ValueError, TypeError):
        return render(request, 'accounts/verify_email.html',
                      {'estado': 'invalido'})

    if user.is_email_verified:
        return render(request, 'accounts/verify_email.html',
                      {'estado': 'ya_verificado'})

    if user.token_verificacion_expirado:
        return render(request, 'accounts/verify_email.html',
                      {'estado': 'expirado', 'email': user.email})

    user.verificar_email()
    return render(request, 'accounts/verify_email.html',
                  {'estado': 'exito', 'email': user.email})


def resend_verification(request):
    """Reenvía el correo de verificación (accessible sin iniciar sesión)."""
    email = ''
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        user = User.objects.filter(email__iexact=email).first()
        # Mismo mensaje exista o no el correo: no revelamos qué emails
        # están registrados.
        if user and not user.is_email_verified:
            enviar_email_verificacion(user)
        messages.success(
            request,
            'Si ese correo tiene una cuenta pendiente de verificación, '
            'te enviamos un nuevo enlace.',
        )
        return redirect('accounts:login')

    return render(request, 'accounts/resend_verification.html',
                  {'email': email})


@login_required
def reenviar_verificacion_mixta(request):
    """Reenvía la verificación al usuario ya autenticado pero no verificado."""
    if not request.user.is_email_verified:
        enviar_email_verificacion(request.user)
        messages.success(request, 'Te enviamos un nuevo enlace de verificación.')
    return redirect('accounts:check_email')


@login_required
def profile(request):
    FormClass = StudentProfileForm if request.user.es_estudiante else EmployerProfileForm
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:profile')
    else:
        form = FormClass(instance=request.user)
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
    # Build proper calendar month boundaries
    for i in range(5, -1, -1):
        # month_start: first day of (current_month - i)
        year  = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year  -= 1
        month_start = now.replace(year=year, month=month, day=1,
                                  hour=0, minute=0, second=0, microsecond=0)
        # month_end: first day of next month
        next_month = month + 1
        next_year  = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        month_end = now.replace(year=next_year, month=next_month, day=1,
                                hour=0, minute=0, second=0, microsecond=0)
        # For the current month cap at now
        if i == 0:
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
