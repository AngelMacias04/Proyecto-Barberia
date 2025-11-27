from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Barbero
from .models import Citas
from .models import Cliente
from .models import Duenio
from .models import Pagos
from .models import Resultados
from .models import Servicios


class BaseImportExportAdmin(ImportExportModelAdmin):
    """Enable import/export options for every registered model."""
    pass


admin.site.register(Barbero, BaseImportExportAdmin)
admin.site.register(Citas, BaseImportExportAdmin)
admin.site.register(Cliente, BaseImportExportAdmin)
admin.site.register(Duenio, BaseImportExportAdmin)
admin.site.register(Pagos, BaseImportExportAdmin)
admin.site.register(Resultados, BaseImportExportAdmin)
admin.site.register(Servicios, BaseImportExportAdmin)
