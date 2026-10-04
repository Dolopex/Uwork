"""Formularios de moderación y del canal de apelación."""
from django import forms

from .models import Apelacion, Reporte


class ReporteForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['motivo', 'descripcion']
        widgets = {
            'motivo': forms.Select(),
            'descripcion': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Describe el problema'}),
        }
        labels = {
            'motivo': 'Motivo del reporte',
            'descripcion': 'Detalle (opcional)',
        }


class ApelacionForm(forms.ModelForm):
    class Meta:
        model = Apelacion
        fields = ['motivo']
        widgets = {
            'motivo': forms.Textarea(
                attrs={'rows': 4,
                       'placeholder': 'Explica por qué consideras que la '
                                      'sanción no corresponde'}),
        }
        labels = {'motivo': 'Por qué solicitas la revisión'}
