import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(*args, source=None):
    return subprocess.run([sys.executable, '-m', 'schedule_compiler.cli.analyze', *map(str, args)],
                          input=source, text=True, capture_output=True, cwd=ROOT)


def test_cli_actual_personal_schedule_prints_results():
    result = run(ROOT / 'examples/horario_personal.hor')
    assert result.returncode == 0 and not result.stderr
    assert 'Resultado: VALIDO' in result.stdout and 'SEMANTICO: COMPLETADA' in result.stdout


def test_cli_json_matches_result_contract():
    result = run(ROOT / 'examples/horario_carolina.hor', '--json')
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data['status'] == 'VALIDO' and data['ast']['children']
    assert len(data['tokens']) == 276 and data['symbols']


def test_cli_incomplete_is_not_success_exit():
    result = run(ROOT / 'examples/semantico/aula_pendiente.hor', '--scope', 'PROPUESTA', '--json')
    assert result.returncode == 1 and not result.stderr
    assert json.loads(result.stdout)['status'] == 'INCOMPLETO'


def test_cli_occupied_room_reports_error():
    result = run(ROOT / 'examples/semantico/aula_ocupada.hor', '--scope', 'PROPUESTA')
    assert result.returncode == 1 and 'CHOQUE_AULA' in result.stderr


def test_cli_invalid_syntax_blocks_semantics():
    result = run('--json', source='HORARIO "X" {}')
    payload = json.loads(result.stdout)
    assert result.returncode == 1 and payload['phases'][-1]['state'] == 'NO_EJECUTADA'


def test_cli_missing_configuration_is_exit_two(tmp_path):
    result = run('--data-dir', tmp_path, source='HORARIO "X" {}')
    assert result.returncode == 2 and 'No se pudieron cargar' in result.stderr
