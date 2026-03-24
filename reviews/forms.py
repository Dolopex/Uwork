from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.Select(choices=[(i, f'{i} ⭐') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe tu opinión...'}),
        }
