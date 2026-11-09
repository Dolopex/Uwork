from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg
from .forms import StudentRegisterForm, EmployerRegisterForm, StudentProfileForm, EmployerProfileForm
from .models import User
from .services import enviar_email_verificacion
from .deletion import eliminar_archivos_de_usuario


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
def reenviar_mi_verificacion(request):
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


# ── R16 — Eliminar mi cuenta (Ley 1581 de 2012, art. 17) ─────────

def _resumen_datos_borrables(usuario):
    """Cuenta qué se va a eliminar, para mostrarlo antes de confirmar."""
    from jobs.models import Application, Job
    from notifications.models import Notification
    from reviews.models import Review
    from support.models import SupportTicket

    return {
        'empleador': {
            'trabajos': Job.objects.filter(creador=usuario).count(),
            'postulaciones': Application.objects.filter(usuario=usuario).count(),
        },
        'estudiante': {
            'trabajos_asignados': Job.objects.filter(asignado=usuario).count(),
            'postulaciones': Application.objects.filter(usuario=usuario).count(),
        },
        'calificaciones_hechas': Review.objects.filter(autor=usuario).count(),
        'calificaciones_recibidas': Review.objects.filter(receptor=usuario).count(),
        'notificaciones': Notification.objects.filter(usuario=usuario).count(),
        'tickets': SupportTicket.objects.filter(reporter=usuario).count(),
        'tickets_sobre_el': SupportTicket.objects.filter(
            usuario_reportado=usuario).count(),
    }


@login_required
def delete_account(request):
    """Supresión de la cuenta a petición del titular.

    Exige confirmar la contraseña: evita que alguien con una sesión abierta
    en un dispositivo compartido borre la cuenta por accidente.
    """
    usuario = request.user

    if request.method == 'POST':
        if not usuario.check_password(request.POST.get('password', '')):
            messages.error(
                request,
                'La contraseña no coincide. Tu cuenta no fue eliminada.',
            )
            return render(request, 'accounts/delete_account.html', {
                'resumen': _resumen_datos_borrables(usuario),
                'error_password': True,
            })

        # Django borra en cascada los registros relacionados (los modelos
        # usan CASCADE); los archivos de MEDIA_ROOT se borran aparte.
        # logout() va antes del delete() para que la sesión no quede
        # apuntando a un id de usuario que ya no existe.
        nombre = usuario.username
        eliminar_archivos_de_usuario(usuario)
        logout(request)
        usuario.delete()

        messages.success(
            request,
            'Tu cuenta "{}" fue eliminada permanentemente.'.format(nombre),
        )
        return redirect('accounts:role_select')

    return render(request, 'accounts/delete_account.html', {
        'resumen': _resumen_datos_borrables(usuario),
    })


#: Abreviaturas de mes en espanol. strftime('%b') devuelve el mes del
#: locale del proceso, que en un servidor es ingles.
MESES_ES = ('ene', 'feb', 'mar', 'abr', 'may', 'jun',
            'jul', 'ago', 'sep', 'oct', 'nov', 'dic')


def _ventanas_menuales(cantidad=6):
    """Ventanas de los ultimos N meses, de la mas antigua a la mas reciente."""
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    ventanas = []
    for i in range(cantidad - 1, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        inicio = now.replace(year=year, month=month, day=1,
                              hour=0, minute=0, second=0, microsecond=0)
        siguiente_mes = month + 1
        siguiente_anio = year
        if siguiente_mes > 12:
            siguiente_mes = 1
            siguiente_anio += 1
        # El mes en curso se cierra mañana: si no, un trabajo guardado
        # hace un segundo queda fuera del corte.
        fin = now.replace(year=siguiente_anio, month=siguiente_mes, day=1,
                          hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            fin = now + timedelta(days=1)
        ventanas.append({
            'inicio': inicio,
            'fin': fin,
            'label': MESES_ES[month - 1],
        })
    return ventanas


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

    # --- Desglose por categoria y por modalidad ---
    # El color no codifica la categoria: la categoria no es un estado. La
    # barra se dibuja con el acento y el nombre va al lado, asi que el
    # grafico no se convierte en un arcoiris.
    if user.es_estudiante:
        base_desglose = trabajos_asignados
    else:
        base_desglose = trabajos_creados

    cat_labels = dict(Job.Categoria.choices)
    categorias_data = [
        {'nombre': cat_labels.get(item['categoria'], item['categoria']),
         'total': item['total']}
        for item in base_desglose.values('categoria')
        .annotate(total=Count('id')).order_by('-total')
    ]

    mod_labels = dict(Job.Modalidad.choices)
    modalidades_data = [
        {'nombre': mod_labels.get(item['modalidad'], item['modalidad']),
         'total': item['total']}
        for item in base_desglose.values('modalidad')
        .annotate(total=Count('id')).order_by('-total')
    ]

    # --- Ventanas de los ultimos seis meses ---
    # Doce meses: seis no alcanzan a cubrir un ciclo completo de trabajo
    # y dejan fuera el invierno academic anterior.
    ventanas = _ventanas_menuales(12)

    # --- Dinero por mes ---
    # El modelo Job no guarda la fecha de finalizacion: se usa updated_at,
    # que es la ultima modificacion del trabajo y por tanto el momento en
    # que paso a estado finalizado (salvo que se edite despues).
    if user.es_estudiante:
        base_dinero = trabajos_asignados.filter(estado=Job.Estado.FINALIZADO)
    else:
        base_dinero = trabajos_creados.filter(estado=Job.Estado.FINALIZADO)

    dinero_mes = []
    for ventana in ventanas:
        total = base_dinero.filter(
            updated_at__gte=ventana['inicio'],
            updated_at__lt=ventana['fin'],
        ).aggregate(total=Sum('pago'))['total'] or 0
        dinero_mes.append({'label': ventana['label'], 'total': total})

    max_dinero_mes = max((m['total'] for m in dinero_mes), default=0) or 0

    # --- Actividad por mes ---
    if user.es_estudiante:
        base_actividad = Application.objects.filter(usuario=user)
    else:
        base_actividad = trabajos_creados

    actividad_mes = []
    for ventana in ventanas:
        count = base_actividad.filter(
            created_at__gte=ventana['inicio'],
            created_at__lt=ventana['fin'],
        ).count()
        actividad_mes.append({'label': ventana['label'], 'count': count})

    max_actividad_mes = max((m['count'] for m in actividad_mes), default=0) or 0

    # --- Dinero que aun no esta en el total ---
    # Un trabajo en proceso ya tiene un valor pactado: no se ha cobrado
    # (el estudiante) ni se ha pagado (el empleador), pero ya no es
    # hipotetico.
    if user.es_estudiante:
        en_proceso_dinero = trabajos_asignados.filter(
            estado=Job.Estado.EN_PROCESO).aggregate(total=Sum('pago'))['total'] or 0
    else:
        en_proceso_dinero = trabajos_creados.filter(
            estado=Job.Estado.EN_PROCESO).aggregate(total=Sum('pago'))['total'] or 0

    # --- Promedio por trabajo finalizado ---
    promedio_trabajo = base_dinero.aggregate(promedio=Avg('pago'))['promedio'] or 0

    # --- Como le va al usuario ---
    postulaciones_recibidas = 0
    aceptadas_recibidas = 0
    candidatos_por_trabajo = 0
    if user.es_estudiante:
        tasa_aceptacion = (
            round(postulaciones_aceptadas * 100 / total_postulaciones)
            if total_postulaciones else 0
        )
    else:
        # Del lado del empleador lo que cuenta es cuanto le aceptan de lo
        # que le postulan a sus avisos.
        postulaciones_recibidas = Application.objects.filter(
            trabajo__creador=user).count()
        aceptadas_recibidas = Application.objects.filter(
            trabajo__creador=user,
            estado=Application.Estado.ACEPTADA).count()
        tasa_aceptacion = (
            round(aceptadas_recibidas * 100 / postulaciones_recibidas)
            if postulaciones_recibidas else 0
        )
        candidatos_por_trabajo = (
            round(postulaciones_recibidas / total_publicados, 1)
            if total_publicados else 0
        )

    # --- Distribucion de las calificaciones recibidas ---
    distribucion_calificaciones = []
    for puntos in (5, 4, 3, 2, 1):
        distribucion_calificaciones.append({
            'puntos': puntos,
            'total': user.reviews_recibidas.filter(puntuacion=puntos).count(),
        })
    max_calificacion = max(
        (d['total'] for d in distribucion_calificaciones), default=0) or 0

    # --- Ultimas calificaciones recibidas ---
    ultimas_calificaciones = list(
        user.reviews_recibidas.select_related('autor', 'trabajo').order_by('-created_at')[:3]
    )

    # --- Actividad reciente ---
    if user.es_estudiante:
        actividad_reciente = list(
            Application.objects.filter(usuario=user)
            .select_related('trabajo')
            .order_by('-created_at')[:5]
        )
    else:
        actividad_reciente = list(
            trabajos_creados.select_related('asignado').order_by('-created_at')[:5]
        )

    # --- El trabajo de mayor valor ---
    if user.es_estudiante:
        mejor_trabajo = trabajos_asignados.order_by('-pago').first()
    else:
        mejor_trabajo = trabajos_creados.order_by('-pago').first()

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
        'meses': actividad_mes,
        'max_mes': max_actividad_mes,
        # Lo nuevo
        'dinero_mes': dinero_mes,
        'max_dinero_mes': max_dinero_mes,
        'en_proceso_dinero': en_proceso_dinero,
        'promedio_trabajo': promedio_trabajo,
        'tasa_aceptacion': tasa_aceptacion,
        'postulaciones_recibidas': postulaciones_recibidas,
        'aceptadas_recibidas': aceptadas_recibidas,
        'candidatos_por_trabajo': candidatos_por_trabajo,
        'modalidades_data': modalidades_data,
        'distribucion_calificaciones': distribucion_calificaciones,
        'max_calificacion': max_calificacion,
        'ultimas_calificaciones': ultimas_calificaciones,
        'actividad_reciente': actividad_reciente,
        'mejor_trabajo': mejor_trabajo,
    }
    return render(request, 'accounts/balance.html', context)
