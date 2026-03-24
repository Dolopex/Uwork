from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['autor', 'receptor', 'trabajo', 'puntuacion', 'created_at']
    list_filter = ['puntuacion']
