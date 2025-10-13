from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

# Modelos (ajusta si aún no tienes Barbero/Cliente)
from .models import Duenio as DuenioModel
from .models import Barbero as BarberoModel
from .models import Cliente as ClienteModel
from .models import Pagos      as PagosModel
from .models import Servicios  as ServiciosModel
from .models import Citas      as CitasModel
from .models import Resultados as ResultadosModel

# Create your views here.

# ---------- Protección por sesión ----------
def duenio_required(view_func):
    def _wrapped(request, *args, **kwargs):
        if request.session.get("role") != "duenio":
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped

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

# --- Endpoint JSON súper simple ---
@csrf_exempt                # ⚠️ MVP: para producción usa CSRF token
@require_POST
def api_login(request):
    data = json.loads(request.body.decode("utf-8"))
    role = (data.get("role") or "").strip()     # 'duenio' | 'barbero' | 'cliente'
    user = (data.get("user") or "").strip()
    pwd  = (data.get("password") or "")

    model_map = {
        "duenio":   DuenioModel,
        "barbero": BarberoModel,
        "cliente": ClienteModel,
    }
    if role not in model_map:
        return JsonResponse({"ok": False, "error": "rol_invalido"}, status=400)

    Model = model_map[role]
    pk_name = Model._meta.pk.name

    # MVP: trae toda la tabla a un arreglo y filtra en Python
    rows = list(Model.objects.values("user", "password", pk_name))
    match = next(
        (r for r in rows
        if (r.get("user") or "").strip() == user and (r.get("password") or "") == pwd),
        None
    )

    if not match:
        return JsonResponse({"ok": False, "error": "credenciales_invalidas"}, status=401)

    # Si quieres sesión de servidor (útil para vistas protegidas luego):
    request.session["role"] = role
    request.session["username"] = user
    request.session["user_pk"] = match[pk_name]

    # A dónde redirigir (nombres de URL)
    redirect_name = {"duenio": "duenio", "barbero": "barbero", "cliente": "cliente"}[role]
    return JsonResponse({"ok": True, "redirect": reverse(redirect_name)})


class Pagos(TemplateView):
    template_name = "pagos.html"

class Resultados(TemplateView):
    template_name = "resultados.html"

class Servicios(TemplateView):
    template_name = "servicios.html"


# === APIS === 
# ---------- API: solicitar_tabla ----------
@csrf_exempt           # MVP; en prod quita esto y manda CSRF token
@require_POST
def api_solicitar_tabla(request):
    # Solo dueños pueden consultar tablas
    if request.session.get("role") != "duenio":
        return JsonResponse({"ok": False, "error": "no_autorizado"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "json_invalido"}, status=400)

    table = (data.get("table") or "").strip().lower()

    model_map = {
        "duenio":     DuenioModel,
        "barbero":    BarberoModel,
        "cliente":    ClienteModel,
        "pagos":      PagosModel,
        "servicios":  ServiciosModel,
        "citas":      CitasModel,
        "resultados": ResultadosModel,
    }
    if table not in model_map:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    Model = model_map[table]
    # Trae todas las columnas; para MVP es suficiente.
    rows = list(Model.objects.values())
    return JsonResponse({"ok": True, "rows": rows})