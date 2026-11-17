"""Carga explícita de las fuentes locales permitidas; nunca acepta rutas HTTP."""

import hashlib
import json
from pathlib import Path

from schedule_compiler.domain.models import (
    Catalog, CatalogAdjustment, CatalogSource, FieldValue, Group, Interval,
    Offer, Origin, Room, Session, Subject, ValidationPolicy, ValueState, Weekday,
)

CATALOG_FILES = {
    "isc-26-1-trabajo": "isc_26_1.trabajo.json",
    "isc-26-1-original": "isc_26_1.normalizado.json",
}
POLICY_FILES = {"proyecto-v0.2": "politica_proyecto.json"}


def known_or_unknown(value: str | None) -> FieldValue:
    return FieldValue(ValueState.UNKNOWN) if value is None else FieldValue(ValueState.KNOWN, value)


class DataRepository:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()

    def _read(self, identifier: str, allowed: dict[str, str]) -> tuple[str, bytes, dict]:
        if identifier not in allowed:
            raise ValueError(f"Recurso no reconocido: {identifier}")
        filename = allowed[identifier]
        content = (self.data_dir / filename).read_bytes()
        return filename, content, json.loads(content)

    def load_catalog(self, catalog_id: str = "isc-26-1-trabajo") -> Catalog:
        filename, content, data = self._read(catalog_id, CATALOG_FILES)
        source = CatalogSource(**{
            "file": data["fuente"]["archivo"],
            "sha256": data["fuente"]["sha256"],
            "sheet": data["fuente"]["hoja"],
        })
        offers = []
        for i, offer in enumerate(data["ofertas"]):
            sessions = []
            for j, session in enumerate(offer["sesiones"]):
                origin = session["origen"]
                origins = (
                    Origin("EXCEL", source.file, sheet=origin["hoja"], cells=(origin["hora"], origin["aula"])),
                    Origin("JSON", filename, pointer=f"/ofertas/{i}/sesiones/{j}"),
                )
                room = known_or_unknown(session["aula"])
                if session.get("estado_aula") == "SIN_ASIGNAR":
                    room = FieldValue(ValueState.UNASSIGNED)
                sessions.append(Session(
                    id=session["id"], offer_id=offer["id"], day=Weekday(session["dia"]),
                    interval=Interval(session["inicio_minutos"], session["fin_minutos"]),
                    room=room, origins=origins,
                ))
            origin = offer["origen"]
            offers.append(Offer(
                id=offer["id"], subject_id=offer["materia_id"], subject=offer["materia"],
                group=known_or_unknown(offer["grupo"]), teacher=known_or_unknown(offer["docente_id"]),
                weekly_hours=offer["horas_semanales_declaradas"], sessions=tuple(sessions),
                origins=(Origin("EXCEL", source.file, sheet=origin["hoja"],
                                cells=(origin["grupo"], origin["materia"], origin["horas"])),),
            ))
        adjustments = tuple(CatalogAdjustment(
            session_id=change["sesion_id"], previous_room=change["aula_anterior"],
            new_room=change["aula_nueva"], reason=change["motivo"],
            origin=Origin("JSON", filename, pointer=f"/ajustes_proyecto/cambios/{i}"),
        ) for i, change in enumerate(data.get("ajustes_proyecto", {}).get("cambios", [])))
        if len({o.id for o in offers}) != len(offers):
            raise ValueError("El catálogo contiene IDs de oferta duplicados.")
        sessions = [s for offer in offers for s in offer.sessions]
        if len({s.id for s in sessions}) != len(sessions):
            raise ValueError("El catálogo contiene IDs de sesión duplicados.")
        return Catalog(
            id=catalog_id, source=source, snapshot_sha256=hashlib.sha256(content).hexdigest(),
            offers=tuple(offers), adjustments=adjustments,
            rooms=tuple(Room(r["id"], r["capacidad"], r["tipo"]) for r in data["catalogos"]["aulas"]),
            groups=tuple(Group(g["id"], g["alumnos"]) for g in data["catalogos"]["grupos"]),
            subjects=tuple(Subject(s["id"], tuple(s["nombres_fuente"]), s["requiere_laboratorio"])
                           for s in data["catalogos"]["materias"]),
            limitations=tuple(data["auditoria"]["datos_no_disponibles"]) + (
                "CENTRO DE CÓMPUTO y FIE1AC0001 no tienen equivalencia física confirmada.",
            ),
        )

    def load_policy(self, policy_id: str = "proyecto-v0.2") -> ValidationPolicy:
        _, _, data = self._read(policy_id, POLICY_FILES)
        if data["version"] != "0.2":
            raise ValueError("Versión de política no soportada.")
        teacher = data["docente"]
        teacher_flags = [teacher[k] for k in (
            "validar_catalogo", "validar_asignacion", "validar_disponibilidad", "validar_cruces",
        )]
        if teacher["modo"] != "TEXTO_LIBRE" or any(v is not False for v in teacher_flags):
            raise ValueError("La política v0.2 requiere todas las reglas de profesores desactivadas.")
        room = data["aula"]
        for key in ("admitir_nombre_nuevo", "comprobar_ocupacion", "asignar_automaticamente"):
            if type(room[key]) is not bool:
                raise ValueError(f"La configuración {key} requiere un booleano.")
        if room["asignar_automaticamente"] or room["sin_asignar"] != "PENDIENTE":
            raise ValueError("v0.2 no asigna aulas automáticamente y conserva los pendientes.")
        if (data["capacidad"] != "NO_CONFIGURADA" or data["laboratorio"] != "NO_CONFIGURADA"
                or data["horario_permitido"] != "NO_CONFIGURADO"):
            raise ValueError("Capacidad, laboratorio y límites horarios requieren ampliar la política y sus datos.")
        return ValidationPolicy(
            id=policy_id, version=data["version"], teacher_rules_enabled=False,
            allow_new_rooms=room["admitir_nombre_nuevo"],
            check_room_occupancy=room["comprobar_ocupacion"],
            unassigned_room_status=room["sin_asignar"], auto_assign_rooms=False,
            capacity=data["capacidad"], laboratory=data["laboratorio"],
            permitted_hours=data["horario_permitido"],
        )
