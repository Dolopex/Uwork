from django import forms
from .models import Job, Application


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
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe detalladamente qué necesitas...'}),
            'requisitos': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Manejo de Figma, experiencia previa en branding...'}),
            'habilidades_requeridas': forms.TextInput(attrs={'placeholder': 'Ej: Python, Diseño gráfico, Excel'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ej: Bogotá, Campus Norte'}),
            'duracion_estimada': forms.TextInput(attrs={'placeholder': 'Ej: 3 días, 1 semana, 2 horas'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date'}),
            'pago': forms.NumberInput(attrs={'min': '0', 'step': '100', 'placeholder': '0'}),
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


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Por qué quieres realizar este trabajo?'}),
        }
