import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from schedule_compiler.main import create_app

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    with TestClient(create_app(ROOT / "data", ROOT / "examples")) as client:
        yield client


def test_health_and_openapi_advertise_real_analysis(client):
    assert client.get('/api/v1/health').json()['compiler_available'] is True
    schema = client.get('/openapi.json').json()
    assert 'post' in schema['paths']['/api/v1/analyses']
    assert client.get('/docs').status_code == 200


def test_post_actual_carolina_matches_full_contract(client):
    response = client.post('/api/v1/analyses', json={
        'source': (ROOT / 'examples/horario_carolina.hor').read_text(),
        'source_name': 'carolina.hor',
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['status'] == 'VALIDO' and body['ast']['kind'] == 'Program'
    assert len(body['tokens']) == 276 and len(body['schedules'][0]['sessions']) == 16
    assert body['symbols'] and body['checks'] and body['catalog_diagnostics']
    assert len(body['metadata']['catalog_sha256']) == 64


@pytest.mark.parametrize('example,status', [
    ('error-lexico', 'INVALIDO'), ('error-sintactico', 'INVALIDO'),
    ('error-semantico', 'INVALIDO'), ('aula-pendiente', 'INCOMPLETO'),
    ('aula-ocupada', 'INVALIDO'), ('compiladores', 'VALIDO'),
])
def test_example_http_flow_returns_program_results_not_server_failures(client, example, status):
    resource = client.get(f'/api/v1/examples/{example}')
    assert resource.status_code == 200
    data = resource.json()
    response = client.post('/api/v1/analyses', json={key: data[key] for key in ('source', 'source_name', 'scope')})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['status'] == status
    if example == 'error-lexico':
        assert body['ast'] is None and body['phases'][1]['state'] == 'NO_EJECUTADA'
    if example == 'error-sintactico':
        assert body['ast'] is None and body['phases'][2]['state'] == 'NO_EJECUTADA'
    if example == 'error-semantico':
        assert body['ast'] is not None and body['symbols']


@pytest.mark.parametrize('payload', [
    {}, {'source': 12}, {'source': None}, {'source': '', 'source_name': ''},
    {'source': '', 'catalog_id': '../../README.md'}, {'source': '', 'language_version': '0.1'},
    {'source': '', 'scope': 'AUDITORIA'}, {'source': '', 'file_path': '/tmp/no.hor'},
])
def test_malformed_requests_are_transport_errors(client, payload):
    assert client.post('/api/v1/analyses', json=payload).status_code == 422


def test_empty_source_is_a_syntax_diagnostic_not_http_error(client):
    response = client.post('/api/v1/analyses', json={'source': ''})
    assert response.status_code == 200
    assert response.json()['diagnostics'][0]['code'] == 'PROGRAMA_VACIO'


@pytest.mark.parametrize('name', ['valido', 'invalido', 'incompleto'])
def test_exported_contract_examples_match_real_http_results(client, name):
    example = json.loads((ROOT / 'contracts/examples' / f'{name}.json').read_text())
    response = client.post('/api/v1/analyses', json=example['request'])
    assert response.status_code == 200
    assert response.json() == example['response']


def test_catalog_routes_preserve_original_and_working_provenance(client):
    response = client.get('/api/v1/catalogs')
    assert response.status_code == 200, response.text
    assert {r['id'] for r in response.json()} == {'isc-26-1-original', 'isc-26-1-trabajo'}
    assert all(r['offers'] == 66 and r['sessions'] == 131 for r in response.json())
    detail = client.get('/api/v1/catalogs/isc-26-1-trabajo')
    assert detail.status_code == 200, detail.text
    assert len(detail.json()['adjustments']) == 2
    original = client.get('/api/v1/catalogs/isc-26-1-original/audit').json()
    working = client.get('/api/v1/catalogs/isc-26-1-trabajo/audit').json()
    assert any(d['code'] == 'CHOQUE_AULA' for d in original['diagnostics'])
    assert not any(d['code'] == 'CHOQUE_AULA' for d in working['diagnostics'])
    assert len([d for d in working['diagnostics'] if d['code'] == 'AULA_PENDIENTE']) == 2
    assert working['stored_audit_scope'] == 'FUENTE_ORIGINAL'


def test_example_listing_and_policy_are_available(client):
    examples = client.get('/api/v1/examples')
    assert examples.status_code == 200 and any(e['id'] == 'carolina' for e in examples.json())
    policy = client.get('/api/v1/policies/proyecto-v0.2')
    assert policy.status_code == 200
    assert not policy.json()['teacher_rules_enabled'] and policy.json()['allow_new_rooms']


@pytest.mark.parametrize('url', ['/api/v1/catalogs/no', '/api/v1/catalogs/no/audit',
                                 '/api/v1/examples/no', '/api/v1/policies/no'])
def test_unknown_resource_ids_return_not_found(client, url):
    assert client.get(url).status_code == 404


def test_missing_data_is_a_configuration_failure(tmp_path):
    with TestClient(create_app(tmp_path, tmp_path)) as client:
        response = client.post('/api/v1/analyses', json={'source': 'HORARIO "X" { INSCRIBIR "Y" }'})
        assert response.status_code == 503
        assert str(tmp_path) not in response.text
        assert client.get('/api/v1/examples/carolina').status_code == 503


def test_unsupported_policy_is_reported_as_configuration_error(tmp_path):
    for source in (ROOT / 'data').glob('*.json'):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    path = tmp_path / 'politica_proyecto.json'
    policy = json.loads(path.read_text())
    policy['capacidad'] = 'ACTIVA'
    path.write_text(json.dumps(policy))
    with TestClient(create_app(tmp_path, ROOT / 'examples')) as client:
        assert client.post('/api/v1/analyses', json={'source': ''}).status_code == 503


def test_server_does_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app()) as client:
        assert client.get('/api/v1/catalogs').status_code == 200
