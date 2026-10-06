from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='login'),
    path('panel/', views.panel_principal, name='panel_principal'),
    path('solicitar/', views.solicitar_prestamo, name='solicitar_prestamo'),
    path('devolucion/', views.devolver_libro, name='devolver_libro'),
    path('renovar/', views.renovar_prestamo_view, name='renovar_prestamo'),
    path('logout/', views.cerrar_sesion, name='logout'),
]
