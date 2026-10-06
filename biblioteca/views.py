from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from .models import Usuario, Libro

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
            
            # Criterio 3 HU-02: Campos obligatorios vacíos
            if not codigo or not titulo or not autor:
                messages.warning(request, "Todos los campos obligatorios (código, título, autor) deben ser completados.")
            # Criterio 2 HU-02: Código duplicado
            elif Libro.objects.filter(codigo=codigo).exists():
                messages.error(request, f"Error: El código '{codigo}' ya está registrado en el sistema.")
            else:
                # Criterio 1 HU-02: Registro exitoso
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
                    messages.error(request, f"Error inesperado al registrar el libro: {str(e)}")
                    
        # HU-03: Registro de Usuarios (Estudiantes y Docentes)
        elif accion == 'crear_usuario':
            rut = request.POST.get('rut_usuario', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            correo = request.POST.get('correo', '').strip()
            tipo = request.POST.get('tipo', '').strip()
            
            # Criterio 3 HU-03: Campos vacíos / Tipo de usuario no seleccionado
            if not rut or not nombre or not correo:
                messages.warning(request, "Todos los campos obligatorios (RUT, nombre, correo) deben ser completados.")
            elif not tipo or tipo not in ['Estudiante', 'Docente']:
                messages.warning(request, "Debe seleccionar un tipo de usuario válido (Estudiante o Docente).")
            # Criterio 2 HU-03: RUT duplicado
            elif Usuario.objects.filter(rut=rut).exists():
                messages.error(request, f"Error: El RUT '{rut}' ya está registrado en el sistema.")
            else:
                # Criterio 1 HU-03: Registro exitoso
                try:
                    Usuario.objects.create(rut=rut, nombre=nombre, correo=correo, tipo=tipo)
                    messages.success(request, f"Usuario '{nombre}' registrado exitosamente como {tipo}.")
                except Exception as e:
                    messages.error(request, f"Error inesperado al registrar el usuario: {str(e)}")

    total_libros = Libro.objects.count()
    total_usuarios = Usuario.objects.count()
    
    context = {
        'total_libros': total_libros,
        'total_usuarios': total_usuarios,
    }
    return render(request, 'biblioteca/panel_principal.html', context)
