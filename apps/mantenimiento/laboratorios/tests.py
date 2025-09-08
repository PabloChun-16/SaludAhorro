from django.test import TestCase
<<<<<<< HEAD
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
=======

# Create your tests here.
>>>>>>> 8f1bf632157c62fc82b9665437497b376869f702
