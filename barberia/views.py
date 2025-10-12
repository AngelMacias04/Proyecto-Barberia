from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class Barbero(TemplateView):
    template_name = "barbero.html"

class Citas(TemplateView):
    template_name = "citas.html"

class Cliente(TemplateView):
    template_name = "cliente.html"

class Duenio(TemplateView):
    template_name = "duenio.html"

class Login(TemplateView):
    template_name = "login.html"

class Pagos(TemplateView):
    template_name = "pagos.html"

class Resultados(TemplateView):
    template_name = "resultados.html"

class Servicios(TemplateView):
    template_name = "servicios.html"
