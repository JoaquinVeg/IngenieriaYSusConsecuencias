from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.db import models
from datetime import date
from .models import Usuario, Libro, Prestamo, Multa
from datetime import datetime

def iniciar_sesion(request):
    if request.method == 'POST':
        usuario_input = request.POST.get('username')
        password_input = request.POST.get('password')
        
        user = authenticate(request, username=usuario_input, password=password_input)
        
        if user is not None:
            if user.is_superuser or user.is_staff:
                login(request, user)
                return redirect('panel_principal')
            else:
                messages.error(request, "Acceso denegado: Solo el encargado de la biblioteca puede ingresar.")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
            
    return render(request, 'biblioteca/login.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def panel_principal(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear_libro':
            codigo = request.POST.get('codigo_libro')
            titulo = request.POST.get('titulo')
            autor = request.POST.get('autor')
            editorial = request.POST.get('editorial')
            anho = request.POST.get('anho') or None
            try:
                Libro.objects.create(
                    codigo=codigo, 
                    titulo=titulo, 
                    autor=autor, 
                    editorial=editorial, 
                    anho=anho, 
                    estado='Disponible'
                )
                messages.success(request, f"Libro '{titulo}' registrado exitosamente.")
            except Exception:
                messages.error(request, "Error: El código del libro ya existe o los datos son inválidos.")
                
        elif accion == 'crear_usuario':
            rut = request.POST.get('rut_usuario')
            nombre = request.POST.get('nombre')
            correo = request.POST.get('correo')
            tipo = request.POST.get('tipo')
            try:
                Usuario.objects.create(rut=rut, nombre=nombre, correo=correo, tipo=tipo)
                messages.success(request, f"Usuario '{nombre}' registrado exitosamente.")
            except Exception:
                messages.error(request, "Error: El RUT ya está registrado o los datos son inválidos.")

    # MODIFICADO: Ahora cuenta únicamente los libros que están disponibles (resta los prestados)
    total_libros = Libro.objects.filter(estado='Disponible').count()
    
    context = {
        'total_libros': total_libros,
    }
    return render(request, 'biblioteca/panel_principal.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def solicitar_prestamo(request):
    query = request.GET.get('q', '')
    libros_disponibles = Libro.objects.filter(estado='Disponible')
    if query:
        libros_disponibles = libros_disponibles.filter(
            models.Q(titulo__icontains=query) | models.Q(codigo__icontains=query)
        )

    if request.method == 'POST':
        rut = request.POST.get('rut')
        codigo = request.POST.get('codigo')

        try:
            usuario = Usuario.objects.get(rut=rut)
            libro = Libro.objects.get(codigo=codigo)

            if usuario.multa_pendiente:
                messages.error(request, f"Error: El usuario {usuario.nombre} tiene multas pendientes.")
            elif libro.estado != 'Disponible':
                messages.error(request, f"Error: El libro '{libro.titulo}' no está disponible.")
            else:
                # Crear el préstamo
                Prestamo.objects.create(usuario=usuario, libro=libro)
                
                # MODIFICADO: Cambiar el estado del libro a 'Prestado' para que descuente del panel
                libro.estado = 'Prestado'
                libro.save()

                messages.success(request, f"¡Préstamo registrado con éxito! Libro: {libro.titulo} | Usuario: {usuario.nombre}.")

        except Usuario.DoesNotExist:
            messages.error(request, "Error: RUT de usuario no encontrado.")
        except Libro.DoesNotExist:
            messages.error(request, "Error: Código de libro no encontrado.")

    context = {
        'libros': libros_disponibles,
        'query': query
    }
    return render(request, 'biblioteca/solicitar_prestamo.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def devolver_libro(request):
    prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

    if request.method == 'POST':
        prestamo_id = request.POST.get('prestamo_id')

        try:
            prestamo = Prestamo.objects.get(id=prestamo_id, devuelto=False)
            prestamo.devuelto = True
            prestamo.save()
            
            # Devuelve el libro a estado 'Disponible' (esto sumará de nuevo al panel)
            prestamo.libro.estado = 'Disponible'
            prestamo.libro.save()

            hoy = date.today()
            if hoy > prestamo.fecha_devolucion:
                dias_atraso = (hoy - prestamo.fecha_devolucion).days
                monto_multa = dias_atraso * 1000

                Multa.objects.create(
                    usuario=prestamo.usuario,
                    prestamo=prestamo,
                    dias_atraso=dias_atraso,
                    monto=monto_multa,
                    pagada=False
                )

                prestamo.usuario.multa_pendiente = True
                prestamo.usuario.save()

                messages.warning(request, f"Libro devuelto con ATRASO ({dias_atraso} días). Se generó una multa de ${monto_multa} para {prestamo.usuario.nombre}.")
            else:
                messages.success(request, f"¡Éxito! El libro '{prestamo.libro.titulo}' ha sido devuelto a tiempo y está disponible.")

            prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')

        except Prestamo.DoesNotExist:
            messages.error(request, "Error: Préstamo no encontrado o ya fue devuelto.")

    context = {
        'prestamos_activos': prestamos_activos
    }
    return render(request, 'biblioteca/devolver_libro.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def gestionar_multas(request):
    if request.method == 'POST':
        multa_id = request.POST.get('multa_id')
        try:
            multa = Multa.objects.get(id=multa_id)
            multa.pagada = True
            multa.save()

            usuario = multa.usuario
            tiene_otras_multas = Multa.objects.filter(usuario=usuario, pagada=False).exists()
            if not tiene_otras_multas:
                usuario.multa_pendiente = False
                usuario.save()

            messages.success(request, f"Multa de ${multa.monto} de {usuario.nombre} marcada como PAGADA.")
        except Multa.DoesNotExist:
            messages.error(request, "Error: Multa no encontrada.")

    multas_pendientes = Multa.objects.filter(pagada=False)
    context = {
        'multas': multas_pendientes
    }
    return render(request, 'biblioteca/gestionar_multas.html', context)

@user_passes_test(lambda u: u.is_superuser, login_url='login')
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

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def ver_reportes(request):
    hoy = date.today()
    
    prestamos_activos = Prestamo.objects.filter(devuelto=False).select_related('usuario', 'libro')
    prestamos_atrasados = prestamos_activos.filter(fecha_devolucion__lt=hoy)
    multas_pendientes = Multa.objects.filter(pagada=False).select_related('usuario', 'prestamo__libro')
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    prestamos_por_periodo = None
    
    if fecha_inicio and fecha_fin:
        prestamos_por_periodo = Prestamo.objects.filter(
            fecha_prestamo__range=[fecha_inicio, fecha_fin]
        ).select_related('usuario', 'libro')

    context = {
        'prestamos_activos': prestamos_activos,
        'prestamos_atrasados': prestamos_atrasados,
        'multas_pendientes': multas_pendientes,
        'prestamos_por_periodo': prestamos_por_periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'biblioteca/reportes.html', context)