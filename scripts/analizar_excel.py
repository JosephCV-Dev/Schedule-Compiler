"""Extrae y audita el Excel de ISC sin modificarlo ni inferir datos ausentes.

Es una herramienta de preparación de datos; no es el compilador del proyecto.
Solo requiere la biblioteca estándar de Python.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile


NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DIAS = (
    ("LUNES", "D", "E"),
    ("MARTES", "F", "G"),
    ("MIERCOLES", "H", "I"),
    ("JUEVES", "J", "K"),
    ("VIERNES", "L", "M"),
)
INTERVALO = re.compile(r"\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*")


def identificador(texto: str) -> str:
    """Normaliza IDs conservando por separado los nombres originales."""
    ascii_text = unicodedata.normalize("NFKD", texto.upper())
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", "_", ascii_text).strip("_")


def leer_excel(ruta: Path) -> tuple[str, dict[int, dict[str, str]]]:
    with ZipFile(ruta) as archivo:
        textos = []
        if "xl/sharedStrings.xml" in archivo.namelist():
            raiz = ET.fromstring(archivo.read("xl/sharedStrings.xml"))
            textos = [
                "".join(t.text or "" for t in item.findall(".//s:t", NS))
                for item in raiz
            ]
        libro = ET.fromstring(archivo.read("xl/workbook.xml"))
        relaciones = ET.fromstring(archivo.read("xl/_rels/workbook.xml.rels"))
        destinos = {r.attrib["Id"]: r.attrib["Target"] for r in relaciones}
        hojas = libro.find("s:sheets", NS)
        if hojas is None or len(hojas) != 1:
            raise ValueError("Esta herramienta espera el libro de ISC de una sola hoja.")
        hoja = hojas[0]
        destino = destinos[hoja.attrib[REL_ID]]
        destino = destino.lstrip("/") if destino.startswith("/") else f"xl/{destino}"
        raiz = ET.fromstring(archivo.read(destino))
        filas = {}
        for fila in raiz.findall("s:sheetData/s:row", NS):
            valores = {}
            for celda in fila.findall("s:c", NS):
                referencia = celda.attrib["r"]
                tipo = celda.attrib.get("t")
                valor = celda.find("s:v", NS)
                texto = valor.text if valor is not None and valor.text else ""
                if tipo == "s":
                    texto = textos[int(texto)]
                elif tipo == "inlineStr":
                    texto = "".join(t.text or "" for t in celda.findall(".//s:t", NS))
                if texto:
                    valores[re.sub(r"\d", "", referencia)] = texto
            filas[int(fila.attrib["r"])] = valores
        cabecera = filas.get(1, {})
        if cabecera.get("A", "").strip() != "SEMESTRE Y CARRERA":
            raise ValueError("La estructura del Excel no coincide con la fuente de ISC.")
        return hoja.attrib["name"], {
            numero: valores
            for numero, valores in filas.items()
            if numero != 1 and valores.get("B", "").strip()
        }


def leer_intervalo(texto: str, celda: str) -> tuple[int, int]:
    coincidencia = INTERVALO.fullmatch(texto)
    if coincidencia is None:
        raise ValueError(f"Intervalo no reconocido en {celda}: {texto!r}")
    h1, m1, h2, m2 = map(int, coincidencia.groups())
    if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and 0 <= m1 <= 59 and 0 <= m2 <= 59):
        raise ValueError(f"Hora fuera de rango en {celda}: {texto!r}")
    inicio, fin = h1 * 60 + m1, h2 * 60 + m2
    if fin <= inicio:
        raise ValueError(f"Intervalo no positivo o nocturno en {celda}: {texto!r}")
    return inicio, fin


def hhmm(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def buscar_conflictos(sesiones: list[dict], campo: str) -> list[dict]:
    conflictos = []
    for a, b in combinations(sesiones, 2):
        if a["dia"] != b["dia"] or a[campo] != b[campo]:
            continue
        if not a[campo]:
            continue
        inicio = max(a["inicio_minutos"], b["inicio_minutos"])
        fin = min(a["fin_minutos"], b["fin_minutos"])
        if inicio < fin:
            conflictos.append({
                "recurso": a[campo],
                "dia": a["dia"],
                "inicio": hhmm(inicio),
                "fin": hhmm(fin),
                "sesiones": [a["id"], b["id"]],
                "filas": [a["origen"]["fila"], b["origen"]["fila"]],
                "celdas_hora": [a["origen"]["hora"], b["origen"]["hora"]],
                "celdas_aula": [a["origen"]["aula"], b["origen"]["aula"]],
            })
    return conflictos


def analizar(ruta: Path) -> dict:
    hoja, filas = leer_excel(ruta)
    ofertas, sesiones, avisos, cargas = [], [], [], []
    materias, grupos, aulas = {}, {}, {}
    for numero, fila in filas.items():
        grupo = fila["A"].strip()
        materia = fila["B"].strip()
        materia_id = identificador(materia)
        oferta_id = f"{identificador(grupo)}_{materia_id}"
        horas = int(fila["C"])
        oferta = {
            "id": oferta_id,
            "materia_id": materia_id,
            "materia": materia,
            "grupo": grupo,
            "horas_semanales_declaradas": horas,
            "docente_id": None,
            "origen": {
                "hoja": hoja, "fila": numero,
                "grupo": f"A{numero}", "materia": f"B{numero}", "horas": f"C{numero}",
                "materia_texto_original": fila["B"],
            },
            "sesiones": [],
        }
        materias.setdefault(materia_id, {
            "id": materia_id, "nombres_fuente": [], "requiere_laboratorio": None,
        })
        if materia not in materias[materia_id]["nombres_fuente"]:
            materias[materia_id]["nombres_fuente"].append(materia)
        grupos.setdefault(grupo, {"id": grupo, "alumnos": None})
        for dia, columna_hora, columna_aula in DIAS:
            texto_hora = fila.get(columna_hora, "")
            texto_aula = fila.get(columna_aula, "")
            celda_hora = f"{columna_hora}{numero}"
            celda_aula = f"{columna_aula}{numero}"
            if not texto_hora.strip():
                if texto_aula.strip():
                    avisos.append({
                        "codigo": "AULA_SIN_INTERVALO", "fila": numero,
                        "hora": celda_hora, "aula": celda_aula,
                        "valor_original": texto_aula,
                        "accion": "No crear una sesión ni inventar una hora.",
                    })
                elif texto_aula:
                    avisos.append({
                        "codigo": "CELDA_CON_ESPACIOS", "celda": celda_aula,
                        "valor_original": texto_aula,
                    })
                continue
            inicio, fin = leer_intervalo(texto_hora, celda_hora)
            aula = texto_aula.strip() or None
            if aula is not None:
                aulas.setdefault(aula, {"id": aula, "capacidad": None, "tipo": None})
            else:
                avisos.append({"codigo": "SESION_SIN_AULA", "hora": celda_hora})
            sesion = {
                "id": f"{oferta_id}_{dia}", "oferta_id": oferta_id,
                "grupo": grupo, "materia": materia, "dia": dia,
                "inicio": hhmm(inicio), "fin": hhmm(fin),
                "inicio_minutos": inicio, "fin_minutos": fin,
                "duracion_minutos": fin - inicio, "aula": aula,
                "origen": {
                    "hoja": hoja, "fila": numero,
                    "hora": celda_hora, "aula": celda_aula,
                    "hora_texto_original": texto_hora, "aula_texto_original": texto_aula,
                },
            }
            oferta["sesiones"].append(sesion)
            sesiones.append(sesion)
            if not re.fullmatch(r"\d{2}:\d{2}-\d{2}:\d{2}", texto_hora):
                avisos.append({
                    "codigo": "FORMATO_HORA_NORMALIZADO", "celda": celda_hora,
                    "original": texto_hora, "normalizado": f"{hhmm(inicio)}-{hhmm(fin)}",
                })
        minutos = sum(s["duracion_minutos"] for s in oferta["sesiones"])
        cargas.append({
            "oferta_id": oferta_id, "fila": numero,
            "horas_declaradas": horas, "minutos_observados": minutos,
            "coincide": minutos == horas * 60,
        })
        ofertas.append(oferta)
    if len({o["id"] for o in ofertas}) != len(ofertas):
        raise ValueError("La normalización generó identificadores de oferta repetidos.")
    posibles_alias = defaultdict(list)
    for aula in aulas:
        coincidencia = re.fullmatch(r"([A-Z]+\d+)-AUL(\d+)", aula)
        if coincidencia:
            edificio, numero_aula = coincidencia.groups()
            posibles_alias[f"{edificio}-AUL{int(numero_aula)}"].append(aula)
    return {
        "version": "0.1",
        "fuente": {
            "archivo": ruta.name, "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
            "hoja": hoja,
        },
        "resumen": {
            "ofertas": len(ofertas), "sesiones": len(sesiones),
            "grupos": len(grupos), "materias_ids_normalizados": len(materias),
            "nombres_materia_distintos_sin_espacios_extremos": len({o["materia"] for o in ofertas}),
            "aulas_con_nombre_literal": len(aulas),
            "horas_semanales_sumadas_de_todas_las_ofertas": sum(s["duracion_minutos"] for s in sesiones) / 60,
            "sesiones_por_dia": dict(Counter(s["dia"] for s in sesiones)),
            "primera_hora_observada": hhmm(min(s["inicio_minutos"] for s in sesiones)),
            "ultima_hora_observada": hhmm(max(s["fin_minutos"] for s in sesiones)),
        },
        "catalogos": {
            "materias": list(materias.values()), "grupos": list(grupos.values()),
            "aulas": list(aulas.values()), "docentes": [],
        },
        "ofertas": ofertas,
        "auditoria": {
            "advertencias_importacion": avisos,
            "carga_semanal": cargas,
            "conflictos_aula_por_nombre_literal": buscar_conflictos(sesiones, "aula"),
            "conflictos_grupo_por_etiqueta": buscar_conflictos(sesiones, "grupo"),
            "posibles_alias_aula_por_confirmar": [v for v in posibles_alias.values() if len(v) > 1],
            "datos_no_disponibles": [
                "Docentes y sus disponibilidades.", "Capacidades y tipos de aulas.",
                "Matrícula por grupo u oferta.", "Requisitos de laboratorio.",
                "Reglamento de horarios permitidos.",
                "Ocupación de recursos por otras carreras o actividades.",
            ],
            "nota": "Los datos ausentes son desconocidos, no asignaciones inválidas demostradas.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("excel", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    if args.excel.resolve() == args.salida.resolve():
        parser.error("La salida debe ser distinta del Excel original.")
    resultado = analizar(args.excel)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "salida": str(args.salida), **resultado["resumen"],
        "conflictos_aula": len(resultado["auditoria"]["conflictos_aula_por_nombre_literal"]),
        "conflictos_grupo": len(resultado["auditoria"]["conflictos_grupo_por_etiqueta"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
