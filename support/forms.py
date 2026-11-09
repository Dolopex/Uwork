from django import forms
from .models import SupportTicket

#: Limite de longitud de la descripcion del reporte. El formulario muestra
#: un contador con el maximo, asi que el servidor aplica la misma cifra.
LIMITE_DESCRIPCION = 2000


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['tipo', 'descripcion', 'usuario_reportado']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'maxlength': LIMITE_DESCRIPCION,
                'placeholder': 'Describe el problema con el mayor detalle posible...',
            }),
            'usuario_reportado': forms.HiddenInput(),
        }
        labels = {
            'tipo': 'Tipo de reporte',
            'descripcion': 'Descripción',
            'usuario_reportado': 'Usuario reportado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].widget.attrs['data-counter'] = 'true'

    def clean_descripcion(self):
        valor = self.cleaned_data.get('descripcion') or ''
        if len(valor) > LIMITE_DESCRIPCION:
            raise forms.ValidationError(
                'La descripción no puede superar los {} caracteres.'.format(
                    LIMITE_DESCRIPCION))
        return valor
