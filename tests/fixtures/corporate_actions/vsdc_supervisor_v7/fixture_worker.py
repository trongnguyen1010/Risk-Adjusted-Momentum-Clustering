"""Local test worker using the actual V6 worker CLI with synthetic source responses."""
from contextlib import ExitStack
import importlib.util
import os
from pathlib import Path
import sys
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(REPOSITORY / 'src'))

from delta_t1.ingestion.corporate_actions import vsdc_recovery_pausefix as collector
from tests.unit.ingestion.corporate_actions import test_vsdc_recovery_pausefix as fixtures


def main():
    project = Path(os.environ['DELTA_V7_TEST_PROJECT'])
    prep = project / 'prep'
    clock = fixtures.fixture.fixture.old.Clock()
    original_run = collector.run

    def run(project, output, **kwargs):
        assert not output.parent.exists(), 'Supervisor precreated the current run'
        return original_run(project, output,
            driver_factory=lambda config, guard: fixtures.fixture.Driver(config, guard, clock, None),
            clock=clock.now, **kwargs)

    spec = importlib.util.spec_from_file_location('fixture_actual_v6_worker', REPOSITORY / collector.WORKER)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    worker.ROOT = project
    with ExitStack() as stack:
        stack.enter_context(patch.object(collector, 'load_preparation', return_value=(collector.contract(), prep)))
        stack.enter_context(patch.object(collector, 'runtime', return_value={'test_only': 'frozen'}))
        stack.enter_context(patch.object(collector.mbs.old, 'readiness', return_value={'ready': True}))
        stack.enter_context(patch.object(collector, 'run', side_effect=run))
        return worker.main()


if __name__ == '__main__':
    raise SystemExit(main())
