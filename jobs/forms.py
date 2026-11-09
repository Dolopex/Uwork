from django import forms
from django.utils import timezone

from accounts.upload_validators import validar_imagen
from .models import Job, Application

#: Limites de longitud de los textos largos. El formulario muestra un
#: contador con el maximo, asi que el servidor tiene que aplicar la misma
#: cifra: un maxlength en el HTML es una ayuda visual, no una garantia.
LIMITE_DESCRIPCION = 2000
LIMITE_REQUISITOS = 1000
LIMITE_MENSAJE = 1200


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'titulo', 'descripcion', 'requisitos', 'habilidades_requeridas',
            'categoria', 'modalidad', 'ubicacion', 'pago', 'duracion_estimada',
            'fecha_limite', 'urgente', 'imagen',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej: Diseño de logo para emprendimiento'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 5,
                'maxlength': LIMITE_DESCRIPCION,
                'placeholder': 'Describe detalladamente qué necesitas...',
            }),
            'requisitos': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': LIMITE_REQUISITOS,
                'placeholder': 'Ej: Manejo de Figma, experiencia previa en branding...',
            }),
            'habilidades_requeridas': forms.TextInput(attrs={'placeholder': 'Ej: Python, Diseño gráfico, Excel'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ej: Bogotá, Campus Norte'}),
            'duracion_estimada': forms.TextInput(attrs={'placeholder': 'Ej: 3 días, 1 semana, 2 horas'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date'}),
            'pago': forms.NumberInput(attrs={'min': '0', 'step': '100', 'placeholder': '0'}),
            'imagen': forms.FileInput(),
        }
        labels = {
            'titulo': 'Título del trabajo',
            'descripcion': 'Descripción',
            'requisitos': 'Requisitos',
            'habilidades_requeridas': 'Habilidades requeridas',
            'pago': 'Pago ofrecido (COP)',
            'categoria': 'Categoría',
            'modalidad': 'Modalidad',
            'ubicacion': 'Ubicación',
            'duracion_estimada': 'Duración estimada',
            'fecha_limite': 'Fecha límite',
            'urgente': 'Marcar como urgente',
            'imagen': 'Imagen o referencia',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los atributos data-* viajan en el HTML desde el servidor: el
        # contador, el importe en pesos y las etiquetas encuentran su
        # control sin depender del orden de carga de los scripts.
        self.fields['titulo'].widget.attrs['data-counter'] = 'true'
        self.fields['descripcion'].widget.attrs['data-counter'] = 'true'
        self.fields['requisitos'].widget.attrs['data-counter'] = 'true'
        self.fields['pago'].widget.attrs['data-money'] = 'true'
        self.fields['habilidades_requeridas'].widget.attrs['data-tags'] = 'true'

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_imagen(self):
        validar_imagen(self.cleaned_data.get('imagen'))
        return self.cleaned_data.get('imagen')

    # El contador del formulario anuncia un maximo: el servidor lo aplica.
    def clean_descripcion(self):
        valor = self.cleaned_data.get('descripcion') or ''
        if len(valor) > LIMITE_DESCRIPCION:
            raise forms.ValidationError(
                'La descripción no puede superar los {} caracteres.'.format(LIMITE_DESCRIPCION))
        return valor

    def clean_requisitos(self):
        valor = self.cleaned_data.get('requisitos') or ''
        if len(valor) > LIMITE_REQUISITOS:
            raise forms.ValidationError(
                'Los requisitos no pueden superar los {} caracteres.'.format(LIMITE_REQUISITOS))
        return valor

    # P1-3 — el pago no puede ser negativo. `min='0'` en el HTML es solo una
    # ayuda visual: un POST directo lo esquivaba.
    def clean_pago(self):
        pago = self.cleaned_data.get('pago')
        if pago is not None and pago < 0:
            raise forms.ValidationError('El pago no puede ser negativo.')
        return pago

    # P1-4 — `fecha_limite` era decorativo: los trabajos vencidos seguían
    # aceptando postulaciones. Ahora la fecha es obligatoria y futura.
    def clean_fecha_limite(self):
        fecha = self.cleaned_data.get('fecha_limite')
        if fecha is None:
            raise forms.ValidationError('Indica la fecha límite del trabajo.')
        if fecha < timezone.localdate():
            raise forms.ValidationError(
                'La fecha límite no puede ser anterior a hoy.')
        return fecha


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={
                'rows': 5,
                'maxlength': LIMITE_MENSAJE,
                'placeholder': '¿Por qué quieres realizar este trabajo?',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mensaje'].widget.attrs['data-counter'] = 'true'

    # El contador del formulario anuncia un maximo: el servidor lo aplica.
    def clean_mensaje(self):
        valor = self.cleaned_data.get('mensaje') or ''
        if len(valor) > LIMITE_MENSAJE:
            raise forms.ValidationError(
                'El mensaje no puede superar los {} caracteres.'.format(LIMITE_MENSAJE))
        return valor
