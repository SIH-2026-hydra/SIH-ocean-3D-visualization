import numpy as np
import pytest

xr = pytest.importorskip('xarray')

from app.core.config import Settings
from app.acquisition import AcquisitionManager
from app.repositories.factory import create_repository
from app.services.operational_data_manager import OperationalDataManager, OperationalDataRequest
from app.repositories.exceptions import DatasetUnavailableError


class RecordingAdapter:
    provider = 'Copernicus Marine'
    def __init__(self):
        self.calls = []

    def acquire(self, request, destination):
        self.calls.append(request)
        path = destination / f'regional_temperature_{len(self.calls)}.nc'
        requested_min_depth = request.min_depth if request.min_depth is not None else 0.0
        requested_max_depth = request.max_depth if request.max_depth is not None else 100.0
        coordinates = {
            'time': np.array([(request.start_time or '2026-09-01T00:00:00Z').replace('Z', '')], dtype='datetime64[ns]'),
            'depth': [requested_min_depth, requested_max_depth],
            'latitude': [request.min_latitude, (request.min_latitude + request.max_latitude) / 2, request.max_latitude],
            'longitude': [request.min_longitude, (request.min_longitude + request.max_longitude) / 2, request.max_longitude],
        }
        values = np.full((1, 2, 3, 3), 26.5)
        xr.Dataset(
            {'thetao': (tuple(coordinates), values, {'units': 'degC'})},
            coords=coordinates,
            attrs={'product': 'GLOBAL_ANALYSISFORECAST_PHY_001_024', 'source': 'MERCATOR GLO12', 'forecast_cycle': '2026-09-01T00:00:00Z'},
        ).to_netcdf(path)
        return [path]


def request(**overrides):
    values = {
        'variables': ('temperature',),
        'min_latitude': -10.0,
        'max_latitude': 20.0,
        'min_longitude': 50.0,
        'max_longitude': 100.0,
        'start_time': '2026-09-01T00:00:00Z',
        'end_time': '2026-09-01T00:00:00Z',
    }
    values.update(overrides)
    return OperationalDataRequest(**values)


def test_cache_miss_acquires_validates_registers_and_serves_bundle(tmp_path):
    adapter = RecordingAdapter()
    refreshes = []
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)), on_registered=lambda: refreshes.append(True))

    result = manager.ensure(request())

    assert result.cache_hit is False
    assert len(adapter.calls) == 1
    assert len(result.bundles) == 1
    assert manager.registry.ready is True
    assert manager.registry.by_variable('temperature') == list(result.bundles)
    assert refreshes == [True]

    repository = create_repository(Settings(ocean_provider='copernicus', copernicus_data_dir=str(tmp_path), copernicus_cache_dir=str(tmp_path)))
    try:
        records = repository.query_ocean_records(parameter='temperature', depth=0, min_lat=-10, max_lat=20, min_lon=50, max_lon=100)
        assert records and records[0]['temperature'] == pytest.approx(26.5)
    finally:
        repository.close()


def test_repeated_matching_request_reuses_cached_bundle_without_acquiring(tmp_path):
    adapter = RecordingAdapter()
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))
    manager.ensure(request())

    result = manager.ensure(request())

    assert result.cache_hit is True
    assert len(adapter.calls) == 1


def test_cache_hit_makes_restored_data_available_before_returning(tmp_path):
    adapter = RecordingAdapter()
    first = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))
    first.ensure(request())

    availability = []
    restarted = OperationalDataManager(
        tmp_path,
        acquisition_manager=AcquisitionManager((RecordingAdapter(),)),
        on_available=lambda: availability.append(True),
    )

    result = restarted.ensure(request())

    assert result.cache_hit is True
    assert availability == [True]


def test_cache_miss_is_spatial_and_temporal_aware(tmp_path):
    adapter = RecordingAdapter()
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))
    manager.ensure(request())

    manager.ensure(request(min_latitude=-25.0))
    manager.ensure(request(start_time='2026-09-02T00:00:00Z', end_time='2026-09-02T00:00:00Z'))

    assert len(adapter.calls) == 3


def test_request_driven_cache_reuses_a_viewport_but_grows_for_new_viewport_and_depth(tmp_path):
    adapter = RecordingAdapter()
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))

    arabian_sea = request(min_latitude=8.0, max_latitude=18.0, min_longitude=55.0, max_longitude=70.0, min_depth=0.0, max_depth=50.0)
    bay_of_bengal = request(min_latitude=8.0, max_latitude=18.0, min_longitude=80.0, max_longitude=95.0, min_depth=0.0, max_depth=50.0)

    assert manager.ensure(arabian_sea).cache_hit is False
    assert manager.ensure(arabian_sea).cache_hit is True
    assert manager.ensure(bay_of_bengal).cache_hit is False
    assert manager.ensure(request(**{**arabian_sea.__dict__, 'min_depth': 75.0, 'max_depth': 75.0})).cache_hit is False
    assert len(adapter.calls) == 3


def test_ensure_query_requires_an_explicit_viewport_and_preserves_request_dimensions(tmp_path):
    adapter = RecordingAdapter()
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))

    with pytest.raises(ValueError, match='viewport'):
        manager.ensure_query(parameter='temperature', min_latitude=None, max_latitude=10, min_longitude=60, max_longitude=70, timestamp=None)

    manager.ensure_query(
        parameter='temperature', min_latitude=8, max_latitude=18, min_longitude=55, max_longitude=70,
        timestamp='2026-09-01T00:00:00Z', depth=50, resolution='0.083deg',
    )
    acquired = adapter.calls[0]
    assert (acquired.min_depth, acquired.max_depth, acquired.resolution) == (50, 50, '0.083deg')


def test_cache_directory_and_validated_bundles_persist_across_manager_restart(tmp_path):
    cache_dir = tmp_path / 'nested' / 'operational-cache'
    adapter = RecordingAdapter()
    first = OperationalDataManager(cache_dir, acquisition_manager=AcquisitionManager((adapter,)))
    assert cache_dir.is_dir()
    first.ensure(request())
    assert (cache_dir / '.oceanx-operational-cache.json').is_file()

    restarted_adapter = RecordingAdapter()
    restarted = OperationalDataManager(cache_dir, acquisition_manager=AcquisitionManager((restarted_adapter,)))
    restarted.registry.discover = lambda: pytest.fail('persistent cache should not revalidate NetCDF files')
    result = restarted.ensure(request())
    assert result.cache_hit is True
    assert restarted_adapter.calls == []


def test_failed_post_validation_resolution_rolls_back_registry_and_manifest(tmp_path):
    class IncompleteAdapter(RecordingAdapter):
        def acquire(self, requested, destination):
            narrowed = type(requested)(**(requested.__dict__ | {'max_longitude': requested.max_longitude - 1}))
            return super().acquire(narrowed, destination)

    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((IncompleteAdapter(),)))
    with pytest.raises(DatasetUnavailableError, match='does not cover'):
        manager.ensure(request())
    assert manager.registry.datasets == []
    assert not (tmp_path / '.oceanx-operational-cache.json').exists()


def test_runtime_diagnostics_report_cache_lifecycle(tmp_path, caplog):
    adapter = RecordingAdapter()
    manager = OperationalDataManager(tmp_path, acquisition_manager=AcquisitionManager((adapter,)))
    with caplog.at_level('INFO'):
        manager.ensure(request())
        manager.ensure(request())
    assert 'Operational cache miss' in caplog.text
    assert 'Scientific acquisition completed' in caplog.text
    assert 'DatasetBundle registered and persistent cache updated' in caplog.text
    assert 'Operational cache hit' in caplog.text
