from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('job/new/', views.job_create, name='job_create'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('job/<int:pk>/apply/', views.job_apply, name='job_apply'),
    path('job/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('job/<int:pk>/accept/<int:app_id>/', views.accept_applicant, name='accept_applicant'),
    path('job/<int:pk>/change-status/', views.job_change_status, name='job_change_status'),
    path('job/<int:pk>/finish/', views.job_finish, name='job_finish'),
    path('job/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('job/<int:pk>/cancel/', views.cancel_application, name='cancel_application'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
]
