from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.decorators import method_decorator 
from django.db import connection, transaction
from datetime import date, datetime
import csv
import io
import zipfile

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

@method_decorator(duenio_required, name="dispatch")
class Duenio(TemplateView):
    template_name = "panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rol"] = self.request.session.get("role", "")
        ctx["username"] = self.request.session.get("username", "")
        return ctx
    
def _normalize_and_validate_fks(Model, payload):
    # 1) Normaliza "" / "NULL" -> None
    for k, v in list(payload.items()):
        if isinstance(v, str) and (v == "" or v.upper() == "NULL"):
            payload[k] = None

    # 2) Valida FKs
    for f in Model._meta.fields:
        if getattr(f, "is_relation", False) and getattr(f, "many_to_one", False):
            key = f.attname  # p.ej. 'servicio2_id'
            if key in payload:
                val = payload[key]
                if val is None:
                    if not f.null:
                        return f"'{key}' es obligatorio"
                else:
                    target = f.target_field.attname  # p.ej. 'id_servicio'
                    if not f.related_model.objects.filter(**{target: val}).exists():
                        return f"fk_inexistente: {key}={val}"
    return None
    
class Login(TemplateView):
    template_name = "login.html"


# === APIS === 
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
    return JsonResponse({"ok": True, "redirect": reverse("bienvenido")})

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
        return JsonResponse({"ok": True, "rows": rows, "fields": meta["fields"]})

    except Exception as e:
        return JsonResponse({"ok": False, "error": f"server_error: {e}"}, status=500)
    
# ---------- CREATE ----------
@csrf_exempt
@require_POST
def api_crear_registro(request):
    data = json.loads(request.body.decode("utf-8"))
    table = (data.get("table") or "").strip().lower()
    row   = data.get("row") or {}

    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    payload = {k: v for k, v in row.items() if k in meta["fields"]}

    # Normaliza/valida FKs (tu helper)
    err = _normalize_and_validate_fks(Model, payload)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    # Usar SP para crear citas con validación de disponibilidad y total calculado
    if table == "citas":
        required = ["id_barbero_id", "id_cliente_id", "dia", "hora"]
        missing = [r for r in required if r not in payload or payload[r] in ("", None)]
        if missing:
            return JsonResponse({"ok": False, "error": f"faltan_campos:{','.join(missing)}"}, status=400)

        params = [
            payload.get("id_barbero_id"),
            payload.get("id_cliente_id"),
            payload.get("dia"),
            payload.get("hora"),
            payload.get("servicio1_id"),
            payload.get("servicio2_id"),
            payload.get("servicio3_id"),
        ]
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL sp_crear_cita(%s,%s,%s,%s,%s,%s,%s)",
                    params,
                )
                result = cursor.fetchall()
                cols = [c[0] for c in cursor.description] if cursor.description else []
            if not result:
                return JsonResponse({"ok": False, "error": "sp_sin_resultado"}, status=500)

            row0 = dict(zip(cols, result[0])) if cols else {}
            pk_value = row0.get("id_cita") or result[0][0]
            total = row0.get("total_calculado")
            return JsonResponse({"ok": True, "pk": pk_value, "total": total})
        except Exception as e:
            msg = str(e)
            if "barbero_ocupado" in msg:
                return JsonResponse({"ok": False, "error": "barbero_ocupado"}, status=400)
            return JsonResponse({"ok": False, "error": f"sp_error:{msg}"}, status=400)

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

    data = json.loads(request.body.decode("utf-8"))
    table = (data.get("table") or "").strip().lower()
    rows  = data.get("rows") or []

    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    pk, fields = meta["pk"], meta["fields"]
    updated = 0
    errors  = []

    try:
        for i, r in enumerate(rows):
            if pk not in r:
                errors.append({"index": i, "error": f"falta_pk:{pk}"})
                continue

            pk_val = r[pk]
            # Solo columnas válidas (sin PK)
            payload = {k: r[k] for k in fields if k in r and k != pk}

            # Normaliza vacíos/"NULL" -> None (no solo en FKs)
            for k, v in list(payload.items()):
                if isinstance(v, str) and (v.strip() == "" or v.strip().lower() == "null"):
                    payload[k] = None

            # Valida/normaliza FKs
            err = _normalize_and_validate_fks(Model, payload)
            if err:
                errors.append({"index": i, "pk": pk_val, "error": err})
                continue

            # Ejecuta update y cuenta afectadas
            affected = Model.objects.filter(**{pk: pk_val}).update(**payload)
            if affected == 0:
                # puede ser PK inexistente o los valores ya eran iguales
                errors.append({"index": i, "pk": pk_val, "error": "sin_cambios_o_no_encontrado"})
            updated += affected

        return JsonResponse({"ok": True, "updated": updated, "errors": errors})
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


# ---------- EXPORT CSV ----------
@csrf_exempt
@require_POST
def api_export_csv(request):
    role = (request.session.get("role") or "").strip().lower()
    if role != "duenio":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"json_invalido:{e}"}, status=400)

    table = (data.get("table") or "").strip().lower()
    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    try:
        rows = list(Model.objects.values(*meta["fields"]))
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(meta["fields"])
        for r in rows:
            writer.writerow([r.get(f, "") if r.get(f, "") is not None else "" for f in meta["fields"]])

        csv_text = buffer.getvalue()
        # UTF-8 con BOM para que Excel lo detecte al abrir con doble clic
        content_bytes = csv_text.encode("utf-8-sig")
        resp = HttpResponse(content_bytes, content_type="text/csv; charset=utf-8")
        filename = f"{table}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"export_error:{e}"}, status=400)


# ---------- EXPORT CSV (TODAS LAS TABLAS) ----------
@csrf_exempt
@require_POST
def api_export_all(request):
    role = (request.session.get("role") or "").strip().lower()
    if role != "duenio":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    # Orden para respetar FKs básicas
    table_order = ["pagos", "servicios", "barbero", "cliente", "citas", "resultados", "duenio"]

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for table in table_order:
            Model, meta = _model_and_meta(table)
            if not Model:
                continue
            rows = list(Model.objects.values(*meta["fields"]))
            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer)
            writer.writerow(meta["fields"])
            for r in rows:
                writer.writerow([r.get(f, "") if r.get(f, "") is not None else "" for f in meta["fields"]])
            csv_text = buffer.getvalue()
            zf.writestr(f"{table}.csv", csv_text.encode("utf-8-sig"))

    mem.seek(0)
    resp = HttpResponse(mem.read(), content_type="application/zip")
    filename = f"backup-todo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    resp["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    return resp


# ---------- IMPORT CSV ----------
@csrf_exempt
@require_POST
def api_import_csv(request):
    role = (request.session.get("role") or "").strip().lower()
    if role != "duenio":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    table = (request.POST.get("table") or "").strip().lower()
    Model, meta = _model_and_meta(table)
    if not Model:
        return JsonResponse({"ok": False, "error": "tabla_invalida"}, status=400)

    if "file" not in request.FILES:
        return JsonResponse({"ok": False, "error": "archivo_faltante"}, status=400)

    file_obj = request.FILES["file"]
    try:
        raw = file_obj.read()
        for enc in ("utf-8-sig", "utf-16", "cp1252"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                text = None
        if text is None:
            return JsonResponse({"ok": False, "error": "encoding_no_soportado"}, status=400)
        reader = csv.DictReader(io.StringIO(text))
        # Validar columnas
        headers = [h.strip() for h in reader.fieldnames or []]
        invalid = [h for h in headers if h not in meta["fields"]]
        if invalid:
            return JsonResponse({"ok": False, "error": f"columnas_invalidas:{','.join(invalid)}"}, status=400)

        created = 0
        skipped = 0
        with transaction.atomic():
            for i, row in enumerate(reader):
                payload = {}
                for k, v in row.items():
                    v = "" if v is None else v
                    if isinstance(v, str) and (v.strip() == "" or v.strip().lower() == "null"):
                        payload[k] = None
                    else:
                        payload[k] = v
                # solo columnas conocidas
                payload = {k: v for k, v in payload.items() if k in meta["fields"]}

                # Si ya existe el mismo PK, omitir la fila y seguir
                pk_name = meta.get("pk")
                pk_val = payload.get(pk_name)
                if pk_name and pk_val is not None:
                    if Model.objects.filter(**{pk_name: pk_val}).exists():
                        skipped += 1
                        continue

                err = _normalize_and_validate_fks(Model, payload)
                if err:
                    raise ValueError(f"fila_{i+1}:{err}")
                Model.objects.create(**payload)
                created += 1
        return JsonResponse({"ok": True, "created": created, "skipped": skipped})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"import_error:{e}"}, status=400)


# ---------- IMPORT CSV (TODAS LAS TABLAS) ----------
@csrf_exempt
@require_POST
def api_import_all(request):
    role = (request.session.get("role") or "").strip().lower()
    if role != "duenio":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    if "file" not in request.FILES:
        return JsonResponse({"ok": False, "error": "archivo_faltante"}, status=400)

    file_obj = request.FILES["file"]
    try:
        order = ["pagos", "servicios", "barbero", "cliente", "citas", "resultados", "duenio"]
        created_summary = {}
        with transaction.atomic():
            with zipfile.ZipFile(file_obj) as zf:
                for table in order:
                    Model, meta = _model_and_meta(table)
                    if not Model:
                        continue
                    filename = f"{table}.csv"
                    if filename not in zf.namelist():
                        continue
                    raw = zf.read(filename)
                    # decodifica en utf-8-sig, fallback utf-16 y cp1252
                    text = None
                    for enc in ("utf-8-sig", "utf-16", "cp1252"):
                        try:
                            text = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            text = None
                    if text is None:
                        raise ValueError(f"encoding_no_soportado:{filename}")
                    reader = csv.DictReader(io.StringIO(text))
                    headers = [h.strip() for h in reader.fieldnames or []]
                    invalid = [h for h in headers if h not in meta["fields"]]
                    if invalid:
                        raise ValueError(f"columnas_invalidas:{filename}:{','.join(invalid)}")

                    created = 0
                    for i, row in enumerate(reader):
                        payload = {}
                        for k, v in row.items():
                            v = "" if v is None else v
                            if isinstance(v, str) and (v.strip() == "" or v.strip().lower() == "null"):
                                payload[k] = None
                            else:
                                payload[k] = v
                        payload = {k: v for k, v in payload.items() if k in meta["fields"]}
                        err = _normalize_and_validate_fks(Model, payload)
                        if err:
                            raise ValueError(f"{filename}:fila_{i+1}:{err}")
                        Model.objects.create(**payload)
                        created += 1
                    created_summary[table] = created
        return JsonResponse({"ok": True, "created": created_summary})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"import_error:{e}"}, status=400)


# ---------- TOP servicios / clientes ----------
@csrf_exempt
@require_POST
def api_top_servicios_clientes(request):
    role = (request.session.get("role") or "").strip().lower()
    if role != "duenio":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"json_invalido:{e}"}, status=400)

    inicio = data.get("inicio") or str(date.today().replace(month=1, day=1))
    fin = data.get("fin") or str(date.today())
    limit = int(data.get("limit") or 5)

    try:
        with connection.cursor() as cursor:
            cursor.callproc("sp_top_servicios_clientes", [inicio, fin, limit])
            top_servicios = cursor.fetchall()
            cols_serv = [c[0] for c in cursor.description] if cursor.description else []
            cursor.nextset()
            top_clientes = cursor.fetchall()
            cols_cli = [c[0] for c in cursor.description] if cursor.description else []

        def as_dict(rows, cols):
            return [dict(zip(cols, r)) for r in rows] if cols else []

        return JsonResponse({
            "ok": True,
            "servicios": as_dict(top_servicios, cols_serv),
            "clientes": as_dict(top_clientes, cols_cli),
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"sp_error:{e}"}, status=400)
