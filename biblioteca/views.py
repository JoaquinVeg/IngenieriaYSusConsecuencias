from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from datetime import date
from .models import Usuario, Libro, Prestamo

def iniciar_sesion(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '').strip()
        
        # Criterio 3 HU-01: Campos vacíos
        if not usuario_input or not password_input:
            messages.warning(request, "Todos los campos son obligatorios.")
            return render(request, 'biblioteca/login.html')
            
        user = authenticate(request, username=usuario_input, password=password_input)
        
        # Criterio 1 HU-01: Credenciales correctas
        if user is not None:
            if user.is_superuser or user.is_staff:
                login(request, user)
                return redirect('panel_principal')
            else:
                messages.error(request, "Acceso denegado: Solo el encargado de la biblioteca puede ingresar.")
        else:
            # Criterio 2 HU-01: Credenciales incorrectas
            messages.error(request, "Usuario o contraseña incorrectos. Por favor reintente.")
            
    return render(request, 'biblioteca/login.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url='login')
def panel_principal(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        # HU-02: Registro de Nuevos Libros
        if accion == 'crear_libro':
            codigo = request.POST.get('codigo_libro', '').strip()
            titulo = request.POST.get('titulo', '').strip()
            autor = request.POST.get('autor', '').strip()
            editorial = request.POST.get('editorial', '').strip()
            anho_str = request.POST.get('anho', '').strip()
            anho = int(anho_str) if anho_str else None
            
            if not codigo or not titulo or not autor:
                messages.warning(request, "Todos los campos obligatorios deben ser completados.")
            elif Libro.objects.filter(codigo=codigo).exists():
                messages.error(request, f"Error: El código '{codigo}' ya está registrado en el sistema.")
            else:
                try:
                    Libro.objects.create(
                        codigo=codigo, 
                        titulo=titulo, 
                        autor=autor, 
                        editorial=editorial if editorial else None, 
                        anho=anho, 
                        estado='Disponible'
                    )
                    messages.success(request, f"Libro '{titulo}' registrado exitosamente en el catálogo.")
                except Exception as e:
                    messages.error(request, f"Error al registrar el libro: {str(e)}")
                    
        # HU-03: Registro de Usuarios
        elif accion == 'crear_usuario':
            rut = request.POST.get('rut_usuario', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            correo = request.POST.get('correo', '').strip()
            tipo = request.POST.get('tipo', '').strip()
            
            if not rut or not nombre or not correo:
                messages.warning(request, "Todos los campos obligatorios deben ser completados.")
            elif not tipo or tipo not in ['Estudiante', 'Docente']:
                messages.warning(request, "Debe seleccionar un tipo de usuario válido (Estudiante o Docente).")
            elif Usuario.objects.filter(rut=rut).exists():
                messages.error(request, f"Error: El RUT '{rut}' ya está registrado en el sistema.")
            else:
                try:
                    Usuario.objects.create(rut=rut, nombre=nombre, correo=correo, tipo=tipo)
                    messages.success(request, f"Usuario '{nombre}' registrado exitosamente como {tipo}.")
                except Exception as e:
                    messages.error(request, f"Error al registrar el usuario: {str(e)}")

    total_libros = Libro.objects.filter(estado='Disponible').count()
    prestamos_activos = Prestamo.objects.filter(devuelto=False).count()
    
    context = {
        'total_libros': total_libros,
        'prestamos_activos': prestamos_activos,
    }
    return render(request, 'biblioteca/panel_principal.html', context)

# HU-04 y HU-05: Registro de Préstamo de Libros y Cálculo Automático de Devolución
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url='login')
def solicitar_prestamo(request):
    query = request.GET.get('q', '').strip()
    libros_disponibles = Libro.objects.filter(estado='Disponible')
    if query:
        libros_disponibles = libros_disponibles.filter(
            models.Q(titulo__icontains=query) | models.Q(codigo__icontains=query)
        )

    if request.method == 'POST':
        rut = request.POST.get('rut', '').strip()
        codigo = request.POST.get('codigo', '').strip()

        try:
            usuario = Usuario.objects.get(rut=rut)
            libro = Libro.objects.get(codigo=codigo)

            # Criterio 2 HU-04: Usuario con multa pendiente
            if usuario.multa_pendiente:
                messages.error(request, f"Error: El usuario {usuario.nombre} tiene multas pendientes y no puede solicitar préstamos.")
            # Criterio 3 HU-04: Libro no disponible
            elif libro.estado != 'Disponible':
                messages.error(request, f"Error: El libro '{libro.titulo}' no está disponible para préstamo.")
            else:
                # Criterio 1 HU-04 y HU-05: Préstamo exitoso y cálculo automático de fecha
                prestamo = Prestamo.objects.create(usuario=usuario, libro=libro)
                messages.success(
                    request, 
                    f"¡Préstamo registrado con éxito! Libro: {libro.titulo} | Usuario: {usuario.nombre} | Fecha de devolución: {prestamo.fecha_devolucion}"
                )

        except Usuario.DoesNotExist:
            messages.error(request, "Error: El RUT de usuario no se encuentra registrado en el sistema.")
        except Libro.DoesNotExist:
            messages.error(request, "Error: El código de libro no existe en el catálogo.")

    context = {
        'libros': libros_disponibles,
        'query': query
    }
    return render(request, 'biblioteca/solicitar_prestamo.html', context)

# HU-06: Devolución de Libros
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url='login')
def devolver_libro(request):
    prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

    if request.method == 'POST':
        prestamo_id = request.POST.get('prestamo_id')

        try:
            prestamo = Prestamo.objects.get(id=prestamo_id, devuelto=False)
            prestamo.devuelto = True
            prestamo.save()
            
            # Devuelve libro a disponible
            prestamo.libro.estado = 'Disponible'
            prestamo.libro.save()

            hoy = date.today()
            # Criterio 2 HU-06: Devolución con retraso
            if hoy > prestamo.fecha_devolucion:
                dias_atraso = (hoy - prestamo.fecha_devolucion).days
                monto_estimado = dias_atraso * 1000
                prestamo.usuario.multa_pendiente = True
                prestamo.usuario.save()
                messages.warning(
                    request, 
                    f"Libro devuelto con ATRASO ({dias_atraso} días). Se calcula una sanción de ${monto_estimado} para {prestamo.usuario.nombre}."
                )
            else:
                # Criterio 1 HU-06: Devolución en fecha
                messages.success(request, f"¡Éxito! El libro '{prestamo.libro.titulo}' ha sido devuelto a tiempo y vuelve a estar disponible.")

            prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

        except Prestamo.DoesNotExist:
            messages.error(request, "Error: Préstamo no encontrado o ya fue devuelto.")

    context = {
        'prestamos_activos': prestamos_activos
    }
    return render(request, 'biblioteca/devolver_libro.html', context)

# HU-06: Renovación Única de Préstamo
@user_passes_test(lambda u: u.is_superuser or u.is_staff, login_url='login')
def renovar_prestamo_view(request):
    prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

    if request.method == 'POST':
        prestamo_id = request.POST.get('prestamo_id')
        try:
            prestamo = Prestamo.objects.get(id=prestamo_id, devuelto=False)
            exito, mensaje = prestamo.renovar_prestamo()
            if exito:
                messages.success(request, mensaje)
            else:
                messages.error(request, mensaje)
        except Prestamo.DoesNotExist:
            messages.error(request, "Error: Préstamo no encontrado.")

        prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

    context = {
        'libros': prestamos_activos  
    }
    return render(request, 'biblioteca/renovar_prestamo.html', context)
