from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ("id", "correo_electronico", "nombre", "apellido", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "id_rol")
    search_fields = ("correo_electronico", "nombre", "apellido")
    ordering = ("correo_electronico",)

    fieldsets = (
        (None, {"fields": ("correo_electronico", "password")}),  # ✅ password ya existe en AbstractBaseUser
        ("Información personal", {"fields": ("nombre", "apellido", "id_rol")}),
        ("Permisos", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("correo_electronico", "nombre", "apellido", "password1", "password2", "is_staff", "is_active")}
        ),
    )

admin.site.register(Usuario, UsuarioAdmin)
