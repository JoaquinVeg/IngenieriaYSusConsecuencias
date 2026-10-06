from django.db import models
from datetime import timedelta, date

class Usuario(models.Model):
    TIPO_USUARIO = (
        ('Estudiante', 'Estudiante'),
        ('Docente', 'Docente'),
    )
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO)
    multa_pendiente = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} - {self.tipo}"

class Libro(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    editorial = models.CharField(max_length=100, blank=True, null=True)
    anho = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20, default='Disponible')

    def __str__(self):
        return self.titulo

# HU-05: Cálculo Automático de Fecha de Devolución (días hábiles)
def sumar_dias_habiles(fecha_inicio, dias):
    fecha_actual = fecha_inicio
    dias_agregados = 0
    while dias_agregados < dias:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() < 5:  # Lunes (0) a Viernes (4)
            dias_agregados += 1
    return fecha_actual

# HU-04 y HU-06: Modelo de Préstamo con Renovación Única
class Prestamo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField(auto_now_add=True)
    fecha_devolucion = models.DateField(blank=True, null=True)
    devuelto = models.BooleanField(default=False)
    renovado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk: 
            # HU-05: 5 días hábiles estudiante, 10 docente
            dias_prestamo = 5 if self.usuario.tipo == 'Estudiante' else 10
            self.fecha_devolucion = sumar_dias_habiles(date.today(), dias_prestamo)
            self.libro.estado = 'Prestado'
            self.libro.save()
        super().save(*args, **kwargs)

    # HU-06: Renovación Única
    def renovar_prestamo(self):
        if not self.renovado:
            dias_prestamo = 5 if self.usuario.tipo == 'Estudiante' else 10
            self.fecha_devolucion = sumar_dias_habiles(self.fecha_devolucion, dias_prestamo)
            self.renovado = True
            self.save()
            return True, f"Préstamo renovado con éxito. Nueva fecha: {self.fecha_devolucion}"
        return False, "Error: Este préstamo ya utilizó su renovación única."

    def __str__(self):
        return f"{self.libro.titulo} -> {self.usuario.nombre} (Vence: {self.fecha_devolucion})"
