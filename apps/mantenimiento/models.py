from django.db import models

# Create your models here.
class Roles(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.nombre_rol
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'