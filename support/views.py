from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from notifications.models import Notification

from .models import SupportTicket
from .forms import SupportTicketForm

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            ticket.save()
            messages.success(request, 'Tu reporte fue enviado. Lo revisaremos pronto.')
            return redirect('support:my_tickets')
    else:
        usuario_pk = request.GET.get('usuario')
        initial = {}
        if usuario_pk:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                initial['usuario_reportado'] = User.objects.get(pk=usuario_pk)
                initial['tipo'] = SupportTicket.Tipo.USUARIO
            except User.DoesNotExist:
                pass
        form = SupportTicketForm(initial=initial)

    # El campo usuario_reportado guarda una clave primaria: para nombrarlo
    # en la pantalla hace falta buscarlo. El nombre va en el contexto y no
    # en la plantilla, que no debe hacer consultas.
    #
    # El campo se pide con form['usuario_reportado'] y no con
    # form.usuario_reportado: en Python no existe el acceso por atributo
    # a los campos de un formulario, solo el acceso por indice.
    reportado = None
    valor_reportado = form['usuario_reportado'].value()
    if valor_reportado:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        reportado = User.objects.filter(pk=valor_reportado).first()

    return render(request, 'support/ticket_form.html', {
        'form': form,
        'reportado': reportado,
    })


@login_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(reporter=request.user)
    return render(request, 'support/my_tickets.html', {'tickets': tickets})


@staff_required
def panel_tickets(request):
    """Cola de soporte del personal.

    Antes los tickets se creaban y nadie los leía: el estado nunca pasaba
    de ABIERTO y el usuario no recibía respuesta.
    """
    filtro = request.GET.get('estado', 'abiertos')
    qs = SupportTicket.objects.select_related(
        'reporter', 'usuario_reportado', 'resuelto_por')
    if filtro == 'todos':
        pass
    elif filtro == 'resueltos':
        qs = qs.filter(estado=SupportTicket.Estado.RESUELTO)
    else:
        qs = qs.filter(estado__in=[SupportTicket.Estado.ABIERTO,
                                   SupportTicket.Estado.EN_REVISION])

    return render(request, 'support/panel_tickets.html', {
        'tickets': qs,
        'filtro': filtro,
        'abiertos': SupportTicket.objects.filter(
            estado__in=[SupportTicket.Estado.ABIERTO,
                        SupportTicket.Estado.EN_REVISION]).count(),
        'resueltos': SupportTicket.objects.filter(
            estado=SupportTicket.Estado.RESUELTO).count(),
    })


@staff_required
@require_POST
def resolver_ticket(request, pk):
    """Responde un ticket y avisa al usuario que lo abrió."""
    ticket = get_object_or_404(SupportTicket, pk=pk)
    estado = request.POST.get('estado', SupportTicket.Estado.RESUELTO)
    respuesta = (request.POST.get('respuesta') or '').strip()

    if estado not in {c[0] for c in SupportTicket.Estado.choices}:
        messages.error(request, 'Estado no válido.')
        return redirect('support:panel_tickets')

    if estado == SupportTicket.Estado.RESUELTO and not respuesta:
        messages.error(request, 'Escribe la respuesta al usuario.')
        return redirect('support:panel_tickets')

    ticket.estado = estado
    ticket.respuesta = respuesta
    ticket.resuelto_por = request.user
    ticket.resuelto_at = timezone.now() if estado == SupportTicket.Estado.RESUELTO \
        else None
    ticket.save(update_fields=['estado', 'respuesta', 'resuelto_por',
                               'resuelto_at'])

    if estado == SupportTicket.Estado.RESUELTO:
        Notification.objects.create(
            usuario=ticket.reporter,
            tipo=Notification.Tipo.TICKET,
            mensaje='Tu reporte de soporte #{} fue resuelto: {}'.format(
                ticket.pk, respuesta[:160]),
            link=reverse('support:my_tickets'),
        )
        messages.success(request, 'Ticket #{} resuelto y usuario avisado.'
                                  .format(ticket.pk))
    else:
        messages.info(request, 'Ticket #{} marcado como {}.'.format(
            ticket.pk, ticket.get_estado_display()))
    return redirect('support:panel_tickets')
