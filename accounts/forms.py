from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .validators import institutional_email
from .upload_validators import validar_imagen


class _AyudaDeContrasenaMixin:
    """Ayuda de las contraseñas en español y estado de los controles.

    UserCreationForm deja el texto de ayuda en inglés y duplicado en los
    dos campos. Se reescribe una sola vez para que el formulario se lea
    igual en toda la aplicación y para que aria-describedby apunte a un
    texto que existe en la página.

    Los atributos data-* viajan en el HTML desde el servidor. Asi el
    formulario no depende del orden en que se carguen los scripts: el
    medidor y la confirmacion siempre encuentran su control.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['password1'].help_text = (
            'Mínimo 8 caracteres. No puede ser solo numérica ni un patrón '
            'común como tu nombre.'
        )
        self.fields['password2'].help_text = 'Escribe la misma contraseña otra vez.'
        self.fields['password1'].widget.attrs['data-password-meter'] = 'true'
        self.fields['password2'].widget.attrs['data-password-match'] = 'id_password1'


class StudentRegisterForm(_AyudaDeContrasenaMixin, UserCreationForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Las habilidades se escriben como etiquetas, no como un bloque de
        # texto: el atributo activa el control en el formulario.
        self.fields['habilidades'].widget.attrs['data-tags'] = 'true'

    # §6.5.3 — validación MIME y de tamaño real en uploads
    def clean_foto(self):
        validar_imagen(self.cleaned_data.get('foto'))
        return self.cleaned_data.get('foto')

    def clean_foto_carnet(self):
        validar_imagen(self.cleaned_data.get('foto_carnet'))
        return self.cleaned_data.get('foto_carnet')


class EmployerRegisterForm(_AyudaDeContrasenaMixin, UserCreationForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Las habilidades se escriben como etiquetas, igual que en el
        # registro: es la misma manera de escribir la misma cosa.
        self.fields['habilidades'].widget.attrs['data-tags'] = 'true'

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
