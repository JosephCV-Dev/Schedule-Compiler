import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(*args, source=None):
    return subprocess.run([sys.executable, "-m", "schedule_compiler.cli.parse", *map(str, args)],
                          input=source, text=True, capture_output=True, cwd=ROOT)


def test_cli_prints_real_tree_branches():
    result = run(ROOT / "examples/oferta_compiladores.hor")
    assert result.returncode == 0 and not result.stderr
    assert "AST generado" in result.stdout
    assert "└── Oferta" in result.stdout and "├── Sesión" in result.stdout
    assert "COMPILADORES" in result.stdout and "Duración (horas): 2" in result.stdout


def test_cli_json_has_visual_tree_and_lexical_tokens():
    result = run("--json", source='HORARIO "X" { INSCRIBIR "Y" }')
    payload = json.loads(result.stdout)
    assert result.returncode == 0 and not result.stderr
    assert payload["state"] == payload["lexical"]["state"] == "COMPLETADA"
    assert payload["ast"]["kind"] == "Program"
    assert payload["ast"]["children"][0]["kind"] == "ScheduleDeclaration"
    assert len(payload["lexical"]["tokens"]) == 6


def test_cli_reports_syntax_errors_as_json_with_exit_one():
    result = run(ROOT / "examples/sintactico/error_tipo.hor", "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 1 and not result.stderr
    assert payload["state"] == "CON_ERRORES" and payload["ast"] is None
    assert payload["lexical"]["state"] == "COMPLETADA"
    assert payload["diagnostics"][0]["code"] == "TOKEN_INESPERADO"


def test_cli_lexical_error_skips_parser():
    result = run("--json", source='HORARIO "sin cierre')
    payload = json.loads(result.stdout)
    assert result.returncode == 1 and not result.stderr
    assert payload["state"] == "NO_EJECUTADA" and payload["ast"] is None
    assert payload["diagnostics"] == []
    assert payload["lexical"]["diagnostics"][0]["code"] == "CADENA_SIN_CIERRE"


def test_cli_stderr_points_to_missing_brace_at_eof():
    result = run(ROOT / "examples/sintactico/error_llave.hor")
    assert result.returncode == 1
    assert "No se generó un AST" in result.stdout
    assert "FIN_INESPERADO" in result.stderr and "error_llave.hor:3:1" in result.stderr


def test_cli_does_not_validate_semantic_values():
    result = run(ROOT / "examples/sintactico/valores_para_semantica.hor")
    assert result.returncode == 0 and not result.stderr
    assert 'Hora: "25:00"' in result.stdout and "Duración (horas): 0" in result.stdout


def test_cli_file_errors_are_separate_from_program_errors(tmp_path):
    assert run(tmp_path / "missing.hor").returncode == 2
    bad = tmp_path / "bad.hor"
    bad.write_bytes(b'\xff')
    assert run(bad).returncode == 2


def test_cli_file_supports_bom_crlf_and_unicode(tmp_path):
    path = tmp_path / "horario.hor"
    path.write_bytes('\ufeffHORARIO "😀" {\r\n INSCRIBIR "Y"\r\n}\r\n'.encode('utf-8'))
    result = run(path, "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ast"]["children"][0]["children"][0]["value"] == "😀"
    assert payload["ast"]["span"]["end"]["line"] == 4
