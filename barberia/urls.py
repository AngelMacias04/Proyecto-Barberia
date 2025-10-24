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

urlpatterns = [
    # Root -> login
    path("", v.Login.as_view(), name="login"),
    # path("login/", Login.as_view(), name="login_page"),
    path("bienvenido/", v.Duenio.as_view(), name="bienvenido"),

    # Endpoint JSON:
    path('api/login/', v.api_login, name='api_login'),  # <-- endpoint JSON

    path('api/solicitar_tabla/', v.api_solicitar_tabla, name='api_solicitar_tabla'),  # <—
    path('api/crear_registro/', v.api_crear_registro, name='api_crear_registro'),
    path('api/actualizar_tabla/', v.api_actualizar_tabla, name='api_actualizar_tabla'),
    path('api/eliminar_registro/', v.api_eliminar_registro, name='api_eliminar_registro'),
]
