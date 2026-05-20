from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SupportTicket
from .forms import SupportTicketForm


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
    return render(request, 'support/ticket_form.html', {'form': form})


@login_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(reporter=request.user)
    return render(request, 'support/my_tickets.html', {'tickets': tickets})
