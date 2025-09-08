from django.test import TestCase
from .models import Laboratorio

class LaboratorioModelTest(TestCase):
    def test_crear_laboratorio(self):
        lab = Laboratorio.objects.create(
            nombre="Laboratorio Central",
            direccion="Ciudad",
            telefono="12345678",
            email="lab@correo.com"
        )
        self.assertEqual(str(lab), "Laboratorio Central")
