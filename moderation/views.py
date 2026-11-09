"""Vistas de moderación — §6.5.4 del documento de pendientes.

Todas las de panel exigen `is_staff`: la modalidad declarada es "moderación
manual desde panel de administración (los autores del proyecto como
administradores iniciales)".
"""
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.services import enviar_email
from jobs.models import Job
from notifications.models import Notification

from .forms import ApelacionForm
from .models import Apelacion, MotivoReporte, Reporte, Sancion

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)


# ── Reportes ────────────────────────────────────────────────────

@login_required
@require_POST
def reportar_trabajo(request, pk):
    """Botón "Reportar publicación" de cada trabajo."""
    trabajo = get_object_or_404(Job, pk=pk)

    # Un usuario no puede reportar su propia publicación ni duplicar un
    # reporte abierto sobre el mismo trabajo.
    if trabajo.creador_id == request.user.id:
        messages.error(request, 'No puedes reportar tu propia publicación.')
        return redirect('jobs:job_detail', pk=pk)

    if Reporte.objects.filter(trabajo=trabajo,
                              reportante=request.user,
                              estado__in=[Reporte.Estado.ABIERTO,
                                          Reporte.Estado.EN_REVISION]
                              ).exists():
        messages.info(request, 'Ya tienes un reporte abierto sobre esta '
                               'publicación.')
        return redirect('jobs:job_detail', pk=pk)

    Reporte.objects.create(
        trabajo=trabajo,
        trabajo_titulo=trabajo.titulo,
        # Se guarda el autor del contenido: si el moderador retira la
        # publicación, `trabajo` queda en NULL pero la sanción sigue
        # teniendo a quién aplicarse.
        contenido_autor=trabajo.creador,
        reportante=request.user,
        motivo=request.POST.get('motivo') or MotivoReporte.OTRO,
        descripcion=request.POST.get('descripcion', '').strip(),
        plazo_respuesta=timezone.now() + timedelta(hours=settings.MODERATION_SLA_HOURS),
    )
    # Aviso a los moderadores de que hay contenido en la cola.
    _notificar_staff(
        Notification.Tipo.REPORTE,
        'Nueva publicación reportada: "{}".'.format(trabajo.titulo),
        reverse('moderation:panel_reportes'),
    )
    messages.success(request, 'Reporte enviado. Lo revisaremos pronto.')
    return redirect('jobs:job_detail', pk=pk)


@staff_required
def panel_reportes(request):
    """Cola de moderación. Los reportes con SLA vencido se listan primero."""
    filtros = request.GET.get('estado', 'abiertos')
    qs = Reporte.objects.select_related(
        'trabajo', 'reportante', 'contenido_autor')
    if filtros == 'todos':
        pass
    elif filtros == 'vencidos':
        qs = qs.filter(estado__in=[Reporte.Estado.ABIERTO,
                                   Reporte.Estado.EN_REVISION],
                       plazo_respuesta__lt=timezone.now())
    else:
        qs = qs.filter(estado__in=[Reporte.Estado.ABIERTO,
                                   Reporte.Estado.EN_REVISION])

    vencidos = [r for r in qs if r.sla_vencido]
    en_curso = [r for r in qs if not r.sla_vencido]
    return render(request, 'moderation/panel_reportes.html', {
        'reportes_vencidos': vencidos,
        'reportes_en_curso': en_curso,
        'filtro': filtros,
        'sla_horas': settings.MODERATION_SLA_HOURS,
    })


@staff_required
@require_POST
def resolver_reporte(request, pk):
    """Cierra un reporte y deja constancia de la resolución."""
    reporte = get_object_or_404(Reporte, pk=pk)
    accion = request.POST.get('accion')

    if accion == 'retirar':
        # El reporte sobrevive (trabajo es SET_NULL) para conservar la
        # evidencia; trabajo_titulo ya guarda el título. Hay que limpiar la
        # referencia en memoria porque Django bloquea el save() si el objeto
        # relacionado fue borrado.
        if reporte.trabajo_id:
            trabajo = reporte.trabajo
            reporte.trabajo = None
            trabajo.delete()
        reporte.estado = Reporte.Estado.RESUELTO
        reporte.resolucion = Reporte.Resolucion.RETIRADO
        messages.success(request, 'Contenido retirado y reporte cerrado.')
    elif accion == 'descartar':
        reporte.estado = Reporte.Estado.RESUELTO
        reporte.resolucion = Reporte.Resolucion.SIN_ACCION
        messages.info(request, 'Reporte descartado.')
    elif accion == 'sancionar':
        return _sancionar_desde_reporte(request, reporte)
    else:
        messages.error(request, 'Acción no reconocida.')
        return redirect('moderation:panel_reportes')

    reporte.resuelto_por = request.user
    reporte.resuelto_at = timezone.now()
    reporte.save(update_fields=['estado', 'resolucion', 'resuelto_por',
                                'resuelto_at'])
    return redirect('moderation:panel_reportes')


def _sancionar_desde_reporte(request, reporte):
    """Aplica la sanción elegida en el formulario de moderación.

    P0-4 — antes hacía `reporte.trabajo.creador` a ciegas: si el trabajo ya
    había sido retirado (trabajo = NULL) la vista reventaba con
    AttributeError y el panel de moderación devolvía 500. Ahora se usa la
    referencia guardada en `contenido_autor`.
    """
    usuario = reporte.trabajo.creador if reporte.trabajo_id and reporte.trabajo \
        else reporte.contenido_autor
    if usuario is None:
        messages.error(
            request,
            'No se puede sancionar: no hay un autor identificado para este '
            'reporte.')
        return redirect('moderation:panel_reportes')

    motivo = (request.POST.get('motivo_sancion') or '').strip()
    if not motivo:
        messages.error(request, 'Debes indicar el motivo de la sanción.')
        return redirect('moderation:panel_reportes')

    tipo = request.POST.get('tipo_sancion', Sancion.Tipo.PERMANENTE)
    hasta = None
    if tipo == Sancion.Tipo.TEMPORAL:
        try:
            dias = int(request.POST.get('dias', 7) or 7)
        except (TypeError, ValueError):
            dias = 7
        dias = max(1, min(dias, 365))
        hasta = timezone.now() + timedelta(days=dias)

    sancion = Sancion.objects.create(
        usuario=usuario,
        usuario_username=usuario.get_username(),
        usuario_email=usuario.email or '',
        aplicada_por=request.user,
        tipo=tipo, motivo=motivo, reporte=reporte, hasta=hasta,
    )
    usuario.aplicar_baneo(motivo, hasta)
    _avisar_sancion(usuario, sancion)
    reporte.estado = Reporte.Estado.RESUELTO
    reporte.resolucion = Reporte.Resolucion.SANCIONADO
    reporte.resuelto_por = request.user
    reporte.resuelto_at = timezone.now()
    reporte.save(update_fields=['estado', 'resolucion', 'resuelto_por',
                                'resuelto_at'])

    messages.success(request, 'Sanción registrada en la bitácora (#{}). '
                              'El usuario fue desconectado.'.format(sancion.pk))
    return redirect('moderation:panel_reportes')


def _avisar_sancion(usuario, sancion):
    """Notifica en la app y por correo al usuario sancionado.

    El sancionado se queda sin sesión (el middleware la cierra), así que la
    notificación en la app solo es visible si vuelve a entrar; el correo es
    el canal fiable para que sepa qué pasó y dónde apelar.
    """
    Notification.objects.create(
        usuario=usuario,
        tipo=Notification.Tipo.BANNEO,
        mensaje='Tu cuenta fue suspendida: {}. Puedes apelar desde el canal '
                'de revisión.'.format(sancion.motivo[:180]),
        link=reverse('moderation:apelacion_crear'),
    )
    hasta = ('La suspensión vence el {}.'.format(
        sancion.hasta.strftime('%d/%m/%Y %H:%M'))) if sancion.hasta else \
        'La suspensión es permanente.'
    cuerpo = (
        'Hola {nombre},\n\n'
        'Tu cuenta de U-Work fue suspendida por la moderación.\n\n'
        'Motivo: {motivo}\n'
        '{hasta}\n\n'
        'Si consideras que la sanción no corresponde, puedes solicitar la '
        'revisión en el canal de apelación:\n\n'
        '  {enlace}\n\n'
        'El equipo de moderación responde las apelaciones.'
    ).format(
        nombre=usuario.first_name or usuario.get_username(),
        motivo=sancion.motivo,
        hasta=hasta,
        enlace='{}{}'.format(settings.SITE_URL,
                             reverse('moderation:apelacion_crear')),
    )
    enviar_email(usuario.email, 'Suspensión de tu cuenta en U-Work', cuerpo)


# ── Moderación previa a publicar ────────────────────────────────

@staff_required
def panel_publicaciones(request):
    """Trabajos enviados a revisión y cola de publicación.

    §6.5.4 / Términos §6: el contenido no se hace público hasta que un
    moderador lo aprueba.
    """
    pendientes = Job.objects.filter(
        estado=Job.Estado.PENDIENTE_REVISION
    ).select_related('creador').order_by('created_at')
    return render(request, 'moderation/panel_publicaciones.html', {
        'pendientes': pendientes,
        'rechazados': Job.objects.filter(
            estado=Job.Estado.RECHAZADO
        ).select_related('creador').order_by('-updated_at')[:50],
    })


@staff_required
@require_POST
def revisar_trabajo(request, pk):
    """Aprueba o rechaza una publicación pendiente."""
    job = get_object_or_404(Job, pk=pk)
    decision = request.POST.get('decision')

    if decision == 'aprobar':
        job.estado = Job.Estado.DISPONIBLE
        job.motivo_rechazo = ''
        job.save(update_fields=['estado', 'motivo_rechazo', 'updated_at'])
        Notification.objects.create(
            usuario=job.creador,
            tipo=Notification.Tipo.APROBACION,
            mensaje='Tu publicación "{}" fue aprobada y ya está visible.'.format(
                job.titulo),
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
        messages.success(request, 'Publicación aprobada.')
    elif decision == 'rechazar':
        motivo = (request.POST.get('motivo') or '').strip()
        if not motivo:
            messages.error(request, 'Indica el motivo del rechazo.')
            return redirect('moderation:panel_publicaciones')
        job.estado = Job.Estado.RECHAZADO
        job.motivo_rechazo = motivo
        job.save(update_fields=['estado', 'motivo_rechazo', 'updated_at'])
        Notification.objects.create(
            usuario=job.creador,
            tipo=Notification.Tipo.APROBACION,
            mensaje='Tu publicación "{}" fue rechazada: {}'.format(
                job.titulo, motivo[:180]),
            link=reverse('jobs:job_detail', args=[job.pk]),
        )
        messages.info(request, 'Publicación rechazada.')
    else:
        messages.error(request, 'Decisión no reconocida.')
        return redirect('moderation:panel_publicaciones')

    return redirect('moderation:panel_publicaciones')


# ── Bitácora de sanciones ───────────────────────────────────────

@staff_required
def bitacora_sanciones(request):
    sanciones = Sancion.objects.select_related(
        'usuario', 'aplicada_por', 'levantada_por')
    vigentes = [s for s in sanciones if s.vigente]
    levantadas = [s for s in sanciones if not s.vigente]
    return render(request, 'moderation/bitacora.html', {
        'sanciones': sanciones,
        'vigentes': vigentes,
        'levantadas': levantadas,
    })


@staff_required
@require_POST
def levantar_sancion(request, pk):
    """Retira un baneo. La fila original se conserva: se marca la fecha."""
    sancion = get_object_or_404(Sancion, pk=pk)
    if not sancion.vigente:
        messages.info(request, 'Esa sanción ya estaba levantada.')
        return redirect('moderation:bitacora')
    if sancion.usuario_id and sancion.usuario:
        sancion.usuario.levantar_baneo()

    sancion.levantada_por = request.user
    sancion.levantada_at = timezone.now()
    sancion.save(update_fields=['levantada_por', 'levantada_at'])

    messages.success(request, 'Baneo levantado. La cuenta de {} vuelve a '
                              'estar activa.'.format(sancion.usuario_nombre))
    return redirect('moderation:bitacora')


# ── Apelaciones ─────────────────────────────────────────────────

@staff_required
def panel_apelaciones(request):
    apelaciones = Apelacion.objects.select_related(
        'usuario', 'sancion', 'resuelta_por')
    return render(request, 'moderation/apelaciones.html', {
        'apelaciones': apelaciones,
        'pendientes': [a for a in apelaciones if a.pendiente],
    })


@staff_required
@require_POST
def resolver_apelacion(request, pk):
    apelacion = get_object_or_404(Apelacion, pk=pk)
    decision = request.POST.get('decision')
    respuesta = (request.POST.get('respuesta') or '').strip()

    if not respuesta:
        messages.error(request, 'Escribe la respuesta al usuario.')
        return redirect('moderation:apelaciones')

    if decision == 'aceptar':
        apelacion.estado = Apelacion.Estado.ACEPTADA
        if apelacion.sancion.usuario_id and apelacion.sancion.usuario:
            apelacion.sancion.usuario.levantar_baneo()
        apelacion.sancion.levantada_por = request.user
        apelacion.sancion.levantada_at = timezone.now()
        apelacion.sancion.save(
            update_fields=['levantada_por', 'levantada_at'])
        messages.success(request, 'Apelación aceptada y baneo levantado.')
    elif decision == 'rechazar':
        apelacion.estado = Apelacion.Estado.RECHAZADA
        messages.info(request, 'Apelación rechazada. La sanción se mantiene.')
    else:
        messages.error(request, 'Decisión no reconocida.')
        return redirect('moderation:apelaciones')

    apelacion.respuesta = respuesta
    apelacion.resuelta_por = request.user
    apelacion.resuelta_at = timezone.now()
    apelacion.save(update_fields=['estado', 'respuesta', 'resuelta_por',
                                 'resuelta_at'])
    _avisar_apelacion_resuelta(apelacion, decision, respuesta)
    return redirect('moderation:apelaciones')


def _avisar_apelacion_resuelta(apelacion, decision, respuesta):
    """Notifica al apelante que su recurso fue resuelto."""
    if not apelacion.usuario_id or not apelacion.usuario:
        return
    aceptada = decision == 'aceptar'
    Notification.objects.create(
        usuario=apelacion.usuario,
        tipo=Notification.Tipo.APELACION,
        mensaje='Tu apelación fue {}. {}'.format(
            'aceptada' if aceptada else 'rechazada', respuesta[:160]),
        link=reverse('moderation:mis_apelaciones'),
    )
    cuerpo = (
        'Hola {nombre},\n\n'
        'Tu apelación sobre la sanción de tu cuenta fue {estado}.\n\n'
        'Respuesta de la moderación:\n  {respuesta}\n\n'
        'Puedes consultar el detalle en:\n  {enlace}\n'
    ).format(
        nombre=apelacion.usuario.first_name
        or apelacion.usuario.get_username(),
        estado='aceptada' if aceptada else 'rechazada',
        respuesta=respuesta,
        enlace='{}{}'.format(settings.SITE_URL,
                             reverse('moderation:mis_apelaciones')),
    )
    enviar_email(apelacion.usuario.email,
                 'Respuesta a tu apelación en U-Work', cuerpo)


# ── Canal de apelación del usuario sancionado ────────────────────

def _sanciones_activas_del_usuario(usuario):
    return Sancion.objects.filter(
        usuario=usuario, levantada_at__isnull=True
    ).select_related('reporte')


@login_required
def apelacion_crear(request):
    """Canal de apelación del sancionado — §6.5.4.

    Es la única vía de salida de un usuario baneado: el middleware de
    baneo cierra la sesión en cada request, así que esta ruta está en la
    lista de excepciones de `BannedUserMiddleware`.
    """
    sanciones = _sanciones_activas_del_usuario(request.user)

    if not sanciones:
        return render(request, 'moderation/apelacion_form.html', {
            'form': None,
            'sanciones': [],
            'sin_sancion': True,
        })

    if request.method == 'POST':
        form = ApelacionForm(request.POST)
        if form.is_valid():
            sancion_id = request.POST.get('sancion')
            sancion = next(
                (s for s in sanciones if str(s.pk) == str(sancion_id)),
                sanciones[0])
            apelacion = Apelacion.objects.create(
                sancion=sancion,
                usuario=request.user,
                usuario_username=request.user.get_username(),
                motivo=form.cleaned_data['motivo'],
            )
            _notificar_staff(
                Notification.Tipo.APELACION,
                'Nueva apelación de {}.'.format(request.user.get_username()),
                reverse('moderation:apelaciones'),
            )
            messages.success(
                request,
                'Tu apelación fue registrada. La moderación la responderá.')
            return redirect('moderation:mis_apelaciones')
    else:
        form = ApelacionForm()

    return render(request, 'moderation/apelacion_form.html', {
        'form': form,
        'sanciones': sanciones,
        'sin_sancion': False,
    })


@login_required
def mis_apelaciones(request):
    """Historial de apelaciones del usuario."""
    apelaciones = Apelacion.objects.filter(
        usuario=request.user).select_related('sancion', 'resuelta_por')
    return render(request, 'moderation/mis_apelaciones.html', {
        'apelaciones': apelaciones,
    })


# ── Utilidades ──────────────────────────────────────────────────

def _notificar_staff(tipo, mensaje, link):
    """Crea una notificación para cada miembro del personal."""
    User = get_user_model()
    for staff in User.objects.filter(is_staff=True, is_active=True):
        Notification.objects.create(
            usuario=staff, tipo=tipo, mensaje=mensaje, link=link)
