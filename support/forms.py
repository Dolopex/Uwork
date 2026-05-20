from django import forms
from .models import SupportTicket


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['tipo', 'descripcion', 'usuario_reportado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe el problema con el mayor detalle posible...',
            }),
            'usuario_reportado': forms.HiddenInput(),
        }
        labels = {
            'tipo': 'Tipo de reporte',
            'descripcion': 'Descripción',
            'usuario_reportado': 'Usuario reportado',
        }
