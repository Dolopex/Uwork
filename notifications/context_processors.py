from .models import Notification


def notif_count(request):
    if request.user.is_authenticated:
        return {'notif_count': Notification.objects.filter(usuario=request.user, leida=False).count()}
    return {'notif_count': 0}
