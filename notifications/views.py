from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    notifs = Notification.objects.filter(usuario=request.user)
    # Mark all as read when the page is opened
    notifs.filter(leida=False).update(leida=True)
    return render(request, 'notifications/list.html', {'notifs': notifs})


@login_required
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, usuario=request.user)
    notif.leida = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')


@login_required
def unread_count(request):
    count = Notification.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({'count': count})
