import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(*args, source=None):
    return subprocess.run([sys.executable, "-m", "schedule_compiler.cli.lex", *map(str, args)],
                          input=source, text=True, capture_output=True, cwd=ROOT)


def test_cli_emits_table_for_a_real_example():
    result = run(ROOT / "examples/oferta_compiladores.hor")
    assert result.returncode == 0 and result.stderr == ""
    assert all(label in result.stdout for label in ("TOKEN", "LEXEMA", "PATRÓN", "LÍNEA", "COLUMNA"))
    assert "Análisis léxico completado" in result.stdout


def test_cli_reads_stdin_and_produces_machine_readable_json():
    result = run("--json", source="HORA 12:00")
    payload = json.loads(result.stdout)
    assert result.returncode == 0 and result.stderr == ""
    assert payload["stage"] == "LEXICO" and payload["state"] == "COMPLETADA"
    assert payload["tokens"][1]["kind"] == "HORA_LITERAL"


def test_cli_errors_are_json_with_partial_tokens_and_exit_one():
    result = run("--json", source="DURACION 2;")
    payload = json.loads(result.stdout)
    assert result.returncode == 1 and result.stderr == ""
    assert payload["state"] == "CON_ERRORES"
    assert len(payload["tokens"]) == 2
    assert payload["diagnostics"][0]["origin"]["span"]["start"]["column"] == 11


def test_cli_table_errors_are_printed_to_stderr():
    result = run(source='HORARIO "abierto')
    assert result.returncode == 1
    assert "stdin:1:9: CADENA_SIN_CIERRE" in result.stderr


def test_cli_distinguishes_file_errors_from_source_errors(tmp_path):
    missing = run(tmp_path / "no_existe.hor")
    assert missing.returncode == 2 and "No se pudo leer" in missing.stderr
    invalid_utf8 = tmp_path / "no_utf8.hor"
    invalid_utf8.write_bytes(b'\xff\xff')
    assert run(invalid_utf8).returncode == 2


def test_cli_supports_utf8_bom_and_preserves_crlf_offsets(tmp_path):
    path = tmp_path / "archivo.hor"
    path.write_bytes(b'\xef\xbb\xbfHORA 12:00\r\nDURACION 2')
    result = run(path, "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["tokens"][0]["span"]["start"]["offset"] == 0
    assert payload["tokens"][2]["span"]["start"] == {"offset": 12, "line": 2, "column": 1}
