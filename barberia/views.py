from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.decorators import method_decorator 

# Modelos (ajusta si aún no tienes Barbero/Cliente)
from .models import Duenio as DuenioModel
from .models import Barbero as BarberoModel
from .models import Cliente as ClienteModel
from .models import Pagos      as PagosModel
from .models import Servicios  as ServiciosModel
from .models import Citas      as CitasModel
from .models import Resultados as ResultadosModel

MODEL_MAP = {
    "duenio":     DuenioModel,
    "barbero":    BarberoModel,
    "cliente":    ClienteModel,
    "pagos":      PagosModel,
    "servicios":  ServiciosModel,
    "citas":      CitasModel,
    "resultados": ResultadosModel,
}

# Create your views here.

# ---------- Protección por sesión ----------
def duenio_required(view_func):
    def _wrapped(request, *args, **kwargs):
        role = request.session.get("role")
        if role not in {"duenio", "barbero", "cliente"}:
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped

class Barbero(TemplateView):
    template_name = "barbero.html"

class Citas(TemplateView):
    template_name = "citas.html"

class Cliente(TemplateView):
    template_name = "cliente.html"

# @method_decorator(duenio_required, name="dispatch")
# class Duenio(TemplateView):
#     template_name = "duenio.html" # change here

@method_decorator(duenio_required, name="dispatch")
class Duenio(TemplateView):
    template_name = "panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rol"] = self.request.session.get("role", "")
        ctx["username"] = self.request.session.get("username", "")
        return ctx
    
class Login(TemplateView):
    template_name = "login.html"

class Pagos(TemplateView):
    template_name = "pagos.html"

class Resultados(TemplateView):
    template_name = "resultados.html"

class Servicios(TemplateView):
    template_name = "servicios.html"


# === APIS === 
# ---------- API: login ----------
# @csrf_exempt
# @require_POST
# def api_login(request):
#     data = json.loads(request.body.decode("utf-8"))
#     role = (data.get("role") or "").strip()     # 'duenio' | 'barbero' | 'cliente'

#     user = (data.get("user") or "").strip()
#     pwd  = (data.get("password") or "")

#     model_map = {
#         "duenio":   DuenioModel,
#         "barbero": BarberoModel,
#         "cliente": ClienteModel,
#     }
#     if role not in model_map:
#         return JsonResponse({"ok": False, "error": "rol_invalido"}, status=400)

#     Model = model_map[role]
#     pk_name = Model._meta.pk.name

#     # MVP: trae toda la tabla a un arreglo y filtra en Python
#     rows = list(Model.objects.values("user", "password", pk_name))
#     match = next(
#         (r for r in rows
#         if (r.get("user") or "").strip() == user and (r.get("password") or "") == pwd),
#         None
#     )

#     if not match:
#         return JsonResponse({"ok": False, "error": "credenciales_invalidas"}, status=401)

#     # Si quieres sesión de servidor (útil para vistas protegidas luego):
#     request.session["role"] = role
#     request.session["username"] = user
#     request.session["user_pk"] = match[pk_name]

#     # A dónde redirigir (nombres de URL)
#     redirect_name = {"duenio": "duenio", "barbero": "barbero", "cliente": "cliente"}[role]
#     return JsonResponse({"ok": True, "redirect": reverse(redirect_name)})

# ---------- API: login ----------
@csrf_exempt
@require_POST
def api_login(request):
    data = json.loads(request.body.decode("utf-8"))
    role = (data.get("role") or "").strip()     # 'duenio' | 'barbero' | 'cliente'
    login_input = (data.get("user") or "").strip()  # el front siempre manda 'user'
    pwd  = (data.get("password") or "")

    model_map = {
        "duenio":  DuenioModel,
        "barbero": BarberoModel,
        "cliente": ClienteModel,
    }
    if role not in model_map:
        return JsonResponse({"ok": False, "error": "rol_invalido"}, status=400)

    Model = model_map[role]
    pk_name = Model._meta.pk.name

    # Campo de login según el rol:
    login_field = "user" if role == "duenio" else "nombre"

    # Buscar directo en la BD
    match = (
        Model.objects
        .filter(**{login_field: login_input, "password": pwd})
        .values(login_field, pk_name)
        .first()
    )
    if not match:
        return JsonResponse({"ok": False, "error": "credenciales_invalidas"}, status=401)

    # Sesión
    request.session["role"] = role
    request.session["username"] = match[login_field]  # guarda 'user' o 'nombre' según toque
    request.session["user_pk"] = match[pk_name]

    # Siempre redirge a 'duenio'
    return JsonResponse({"ok": True, "redirect": reverse("duenio")})

# Helper: resuelve modelo, lista de campos "planos" y nombre de PK
def _model_and_meta(table: str):
    """
    Devuelve (Model, meta) donde meta = {"fields": [...], "pk": <nombre_pk>}
    - Usa .attname para que, si hay FK, quede el *_id que espera Django en create/update.
    """
    Model = MODEL_MAP.get(table)
    if not Model:
        return None, None

    pk_name = Model._meta.pk.attname  # p.ej. 'id_duenio' (no siempre es 'id')

    fields = []
    for f in Model._meta.get_fields():
        # Ignorar relaciones automáticas y M2M
        if getattr(f, "many_to_many", False) or getattr(f, "auto_created", False):
            continue
        if getattr(f, "concrete", False):
            # Para FK: attname == '<campo>_id'; para campos normales attname == name
            fields.append(getattr(f, "attname", f.name))

    return Model, {"fields": fields, "pk": pk_name}

# ---------- Solictar tabla ----------
@csrf_exempt
@require_POST
def api_solicitar_tabla(request):
    role = (request.session.get("role") or "").strip().lower()
    user_pk = str(request.session.get("user_pk") or "")
    if not role or not user_pk:
        return JsonResponse({"ok": False, "error": "no_autenticado"}, status=401)
    # 
    # Solo dueños pueden consultar tablas
    # if request.session.get("role") != "duenio":
    #     return JsonResponse({"ok": False, "error": "no_autorizado"}, status=403)

    # Body JSON robusto
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"json_invalido: {e}"}, status=400)

    table = (data.get("table") or "").strip().lower()

    # Usa helper para resolver modelo y columnas válidas
    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    try:
        # 1) Arranca queryset
        qs = Model.objects.all()

        # 2) Filtrado directo por rol/tabla (dueño ve todo)
        if role != "duenio":
            if table == role:
                # barbero -> id_barbero; cliente -> id_cliente
                qs = qs.filter(**{f"id_{role}": user_pk})

            elif table == "citas":
                # citas tiene id_barbero e id_cliente
                qs = qs.filter(**{f"id_{role}": user_pk})

            elif table == "resultados":
                if role == "barbero":
                    qs = qs.filter(id_barbero=user_pk)
                elif role == "cliente":
                    # resultados de MIS citas
                    qs = qs.filter(
                        id_cita__in=CitasModel.objects
                            .filter(id_cliente=user_pk)
                            .values_list("id_cita", flat=True)
                    )
            # 'pagos' y 'servicios' = catálogos → sin filtro

        # 3) Proyección y respuesta (tu front sigue igual)
        rows = list(qs.values(*meta["fields"]))
        return JsonResponse({"ok": True, "rows": rows})

    except Exception as e:
        return JsonResponse({"ok": False, "error": f"server_error: {e}"}, status=500)
    # try:
    #     # Devuelve SOLO rows para que front siga igual
    #     rows = list(Model.objects.values(*meta["fields"]))
    #     return JsonResponse({"ok": True, "rows": rows})
    # except Exception as e:
    #     # Evita que salga el HTML de error de Django (causa el "Error de red")
    #     return JsonResponse({"ok": False, "error": f"server_error: {e}"}, status=500)

# ---------- CREATE ----------
@csrf_exempt
@require_POST
def api_crear_registro(request):
    if request.session.get("role") != "duenio":
        return JsonResponse({"ok": False, "error": "no_autorizado"}, status=403)

    data = json.loads(request.body.decode("utf-8"))
    table = (data.get("table") or "").strip().lower()
    row   = data.get("row") or {}

    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    # Filtra sólo columnas válidas
    payload = {k: v for k, v in row.items() if k in meta["fields"]}
    try:
        obj = Model.objects.create(**payload)
        pk_value = getattr(obj, meta["pk"])
        return JsonResponse({"ok": True, "pk": pk_value})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

# ---------- UPDATE ----------
@csrf_exempt
@require_POST
def api_actualizar_tabla(request):
    if request.session.get("role") != "duenio":
        return JsonResponse({"ok": False, "error": "no_autorizado"}, status=403)

    data = json.loads(request.body.decode("utf-8"))
    table = (data.get("table") or "").strip().lower()
    rows  = data.get("rows") or []

    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    pk, fields = meta["pk"], meta["fields"]
    updated = 0
    try:
        for r in rows:
            if pk not in r:
                continue
            pk_val = r[pk]
            payload = {k: r[k] for k in fields if k in r and k != pk}
            if payload:
                Model.objects.filter(**{pk: pk_val}).update(**payload)
                updated += 1
        return JsonResponse({"ok": True, "updated": updated})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

# ---------- DELETE ----------
@csrf_exempt
@require_POST
def api_eliminar_registro(request):
    rol = (request.session.get("role") or "").strip().lower()
    user_pk = str(request.session.get("user_pk") or "")
    if not rol or not user_pk:
        return JsonResponse({"ok": False, "error": "no_autenticado"}, status=401)
    
    data = json.loads(request.body.decode("utf-8"))
    table = (data.get("table") or "").strip().lower()
    pk_val = data.get("pk")

    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    try:
        deleted, _ = Model.objects.filter(**{meta["pk"]: pk_val}).delete()
        return JsonResponse({"ok": True, "deleted": deleted})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)