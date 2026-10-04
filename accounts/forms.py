from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .validators import institutional_email
from .upload_validators import validar_imagen


class StudentRegisterForm(UserCreationForm):
    # R10 — el estudiante solo puede registrarse con correo institucional.
    email = forms.EmailField(
        required=True,
        validators=[institutional_email],
        help_text='Debe ser un correo institucional de la universidad.',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'cedula', 'telefono', 'fecha_nacimiento', 'direccion',
            'universidad', 'carrera', 'semestre',
            'foto', 'foto_carnet', 'habilidades',
            'pregunta_seguridad', 'respuesta_seguridad',
            'password1', 'password2',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'habilidades': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: Python, Diseño, Traducción'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ciudad, barrio o dirección'}),
            'pregunta_seguridad': forms.TextInput(attrs={'placeholder': 'Ej: ¿Nombre de tu primera mascota?'}),
            'respuesta_seguridad': forms.TextInput(attrs={'placeholder': 'Tu respuesta secreta'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = User.Rol.ESTUDIANTE
        if commit:
            user.save()
        return user

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_foto(self):
        validar_imagen(self.cleaned_data.get('foto'))
        return self.cleaned_data.get('foto')

    def clean_foto_carnet(self):
        validar_imagen(self.cleaned_data.get('foto_carnet'))
        return self.cleaned_data.get('foto_carnet')


class EmployerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'cedula', 'telefono', 'fecha_nacimiento', 'direccion',
            'foto',
            'password1', 'password2',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ciudad, barrio o dirección'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = User.Rol.EMPLEADOR
        if commit:
            user.save()
        return user

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_foto(self):
        validar_imagen(self.cleaned_data.get('foto'))
        return self.cleaned_data.get('foto')


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'foto', 'foto_carnet',
            'telefono', 'cedula', 'fecha_nacimiento', 'direccion',
            'universidad', 'carrera', 'semestre', 'habilidades',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'habilidades': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Python, Diseño gráfico, Traducción'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ciudad, barrio o dirección'}),
        }

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_foto(self):
        validar_imagen(self.cleaned_data.get('foto'))
        return self.cleaned_data.get('foto')

    def clean_foto_carnet(self):
        validar_imagen(self.cleaned_data.get('foto_carnet'))
        return self.cleaned_data.get('foto_carnet')


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'foto',
            'telefono', 'cedula', 'fecha_nacimiento', 'direccion',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ciudad, barrio o dirección'}),
        }

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_foto(self):
        validar_imagen(self.cleaned_data.get('foto'))
        return self.cleaned_data.get('foto')
