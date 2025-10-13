"""
URL configuration for Proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views as v

from .views import (
    Login,
    Barbero,
    Citas,
    Cliente,
    Duenio,
    Pagos,
    Resultados,
    Servicios,
)

urlpatterns = [
    # ruta raíz: al entrar al sitio mostramos el login
    path('', Login.as_view(), name='login'),
    path('login/', Login.as_view(), name='login_page'),
    path('barbero/', Barbero.as_view(), name='barbero'),
    path('citas/', Citas.as_view(), name='citas'),
    path('cliente/', Cliente.as_view(), name='cliente'),
    path('duenio/', Duenio.as_view(), name='duenio'),
    path('pagos/', Pagos.as_view(), name='pagos'),
    path('resultados/', Resultados.as_view(), name='resultados'),
    path('servicios/', Servicios.as_view(), name='servicios'),

    # Endpoint JSON:
    path('api/login/', v.api_login, name='api_login'),  # <-- endpoint JSON
    path('api/solicitar_tabla/', v.api_solicitar_tabla, name='api_solicitar_tabla'),  # <—
]
