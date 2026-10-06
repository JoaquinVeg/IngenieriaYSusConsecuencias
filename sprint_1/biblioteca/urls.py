from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='login'),
    path('panel/', views.panel_principal, name='panel_principal'),
    path('logout/', views.cerrar_sesion, name='logout'),
]
