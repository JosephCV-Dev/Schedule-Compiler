"""Claves de comparación; nunca sustituyen la etiqueta original."""

import re
import unicodedata

from schedule_compiler.domain.models import RoomIdentity


def room_identity(name: str) -> RoomIdentity:
    text = " ".join(unicodedata.normalize("NFKC", name).upper().split())
    if not text:
        raise ValueError("Un aula conocida necesita un nombre no vacío.")
    match = re.fullmatch(r"([A-Z]+[0-9]+)[\s-]*AUL[\s-]*([0-9]+)", text)
    if match:
        building, number = match.groups()
        return RoomIdentity(name, f"AUL:{building}:{int(number)}", "CODIGO_AUL")
    match = re.fullmatch(r"([A-Z]+[0-9]+)[\s-]*AC[\s-]*([0-9]+)", text)
    if match:
        building, number = match.groups()
        return RoomIdentity(name, f"AC:{building}:{number}", "CODIGO_AC")
    return RoomIdentity(name, f"NOMBRE:{text}", "NOMBRE_LITERAL")
