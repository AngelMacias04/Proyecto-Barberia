from django.contrib import admin
from .models import Barbero
from .models import Citas
from .models import Cliente
from .models import Duenio
from .models import Pagos
from .models import Resultados
from .models import Servicios
# Register your models here.

admin.site.register(Barbero)
admin.site.register(Citas)
admin.site.register(Cliente)
admin.site.register(Duenio)
admin.site.register(Pagos)
admin.site.register(Resultados)
admin.site.register(Servicios)