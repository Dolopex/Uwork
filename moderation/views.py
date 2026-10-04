"""Vistas de moderación — §6.5.4 del documento de pendientes.

Todas exigen `is_staff`: la modalidad declarada es "moderación manual desde
panel de administración (los autores del proyecto como administradores
iniciales)".
"""
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from jobs.models import Job

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
        reportante=request.user,
        motivo=request.POST.get('motivo') or MotivoReporte.OTRO,
        descripcion=request.POST.get('descripcion', '').strip(),
        plazo_respuesta=timezone.now() + timedelta(hours=settings.MODERATION_SLA_HOURS),
    )
    messages.success(request, 'Reporte enviado. Lo revisaremos pronto.')
    return redirect('jobs:job_detail', pk=pk)


@staff_required
def panel_reportes(request):
    """Cola de moderación. Los reportes con SLA vencido se listan primero."""
    filtros = request.GET.get('estado', 'abiertos')
    qs = Reporte.objects.select_related('trabajo', 'reportante')
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
    """Aplica la sanción elegida en el formulario de moderación."""
    usuario = reporte.trabajo.creador
    motivo = (request.POST.get('motivo_sancion') or '').strip()
    if not motivo:
        messages.error(request, 'Debes indicar el motivo de la sanción.')
        return redirect('moderation:panel_reportes')

    tipo = request.POST.get('tipo_sancion', Sancion.Tipo.PERMANENTE)
    hasta = None
    if tipo == Sancion.Tipo.TEMPORAL:
        dias = int(request.POST.get('dias', 7) or 7)
        hasta = timezone.now() + timedelta(days=dias)

    sancion = Sancion.objects.create(
        usuario=usuario, aplicada_por=request.user, tipo=tipo,
        motivo=motivo, reporte=reporte, hasta=hasta,
    )
    usuario.aplicar_baneo(motivo, hasta)
    reporte.estado = Reporte.Estado.RESUELTO
    reporte.resolucion = Reporte.Resolucion.SANCIONADO
    reporte.resuelto_por = request.user
    reporte.resuelto_at = timezone.now()
    reporte.save(update_fields=['estado', 'resolucion', 'resuelto_por',
                                'resuelto_at'])

    messages.success(request, 'Sanción registrada en la bitácora (#{}). '
                              'El usuario fue desconectado.'.format(sancion.pk))
    return redirect('moderation:panel_reportes')


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

    sancion.usuario.levantar_baneo()
    sancion.levantada_por = request.user
    sancion.levantada_at = timezone.now()
    sancion.save(update_fields=['levantada_por', 'levantada_at'])

    messages.success(request, 'Baneo levantado. La cuenta de {} vuelve a '
                              'estar activa.'.format(sancion.usuario))
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
    return redirect('moderation:apelaciones')
