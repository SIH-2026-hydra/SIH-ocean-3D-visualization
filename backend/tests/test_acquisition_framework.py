import sys
from pathlib import Path

import pytest

from app.acquisition import AcquisitionManager, ScientificAcquisitionRequest
from app.acquisition.copernicus import CopernicusAcquisitionAdapter
from app.repositories.exceptions import ProviderUnavailableError


class RecordingAdapter:
    provider = 'Test provider'

    def __init__(self):
        self.requests = []

    def acquire(self, request, destination):
        self.requests.append((request, destination))
        return ()


def request(**overrides):
    values = dict(provider='Test provider', variables=('temperature',), min_latitude=8, max_latitude=18, min_longitude=55, max_longitude=70, start_time='2026-09-01T00:00:00Z', min_depth=0, max_depth=50, resolution='0.083deg')
    values.update(overrides)
    return ScientificAcquisitionRequest(**values)


def test_acquisition_manager_dispatches_abstract_request_without_provider_logic(tmp_path):
    adapter = RecordingAdapter()
    manager = AcquisitionManager((adapter,))

    assert manager.acquire(request(), tmp_path) == ()
    forwarded, destination = adapter.requests[0]
    assert forwarded.variables == ('temperature',)
    assert forwarded.min_depth == 0
    assert destination == tmp_path


def test_acquisition_manager_rejects_unknown_provider(tmp_path):
    with pytest.raises(ProviderUnavailableError, match='No acquisition adapter'):
        AcquisitionManager(()).acquire(request(provider='Unknown'), tmp_path)


def test_copernicus_adapter_isolates_sdk_and_translates_request(monkeypatch, tmp_path):
    calls = []

    class FakeCopernicus:
        @staticmethod
        def subset(**kwargs):
            calls.append(kwargs)
            output = Path(kwargs['output_directory']) / kwargs['output_filename']
            output.write_bytes(b'fixture')
            return str(output)

    monkeypatch.setitem(sys.modules, 'copernicusmarine', FakeCopernicus)
    result = CopernicusAcquisitionAdapter().acquire(request(provider='Copernicus Marine'), tmp_path)

    assert result[0].is_file()
    assert calls[0]['dataset_id'] == 'GLOBAL_ANALYSISFORECAST_PHY_001_024'
    assert calls[0]['variables'] == ['thetao']
    assert calls[0]['minimum_latitude'] == 8


def test_copernicus_adapter_reports_provider_runtime_failure(monkeypatch, tmp_path):
    monkeypatch.delitem(sys.modules, 'copernicusmarine', raising=False)
    original_import = __import__

    def no_provider_runtime(name, *args, **kwargs):
        if name == 'copernicusmarine':
            raise ImportError('not installed')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr('builtins.__import__', no_provider_runtime)
    with pytest.raises(ProviderUnavailableError, match='provider runtime'):
        CopernicusAcquisitionAdapter().acquire(request(provider='Copernicus Marine'), tmp_path)
