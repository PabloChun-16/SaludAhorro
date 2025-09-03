from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Usuario
from .forms import UsuarioForm

class UsuarioListView(ListView):
    model = Usuario
    template_name = "mantenimiento_usuarios/lista.html"
    context_object_name = "usuarios"


class UsuarioCreateView(CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "mantenimiento_usuarios/crear.html"
    success_url = reverse_lazy("mantenimiento:mantenimiento_usuarios:lista")


class UsuarioUpdateView(UpdateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "mantenimiento_usuarios/editar.html"
    success_url = reverse_lazy("mantenimiento:mantenimiento_usuarios:lista")


class UsuarioDeleteView(DeleteView):
    model = Usuario
    template_name = "mantenimiento_usuarios/eliminar.html"  # (no usamos el *_confirm_delete por defecto)
    success_url = reverse_lazy("mantenimiento:mantenimiento_usuarios:lista")