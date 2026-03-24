from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('job/<int:job_pk>/review/', views.create_review, name='create_review'),
]
