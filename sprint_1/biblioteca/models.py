from django.db import models

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
