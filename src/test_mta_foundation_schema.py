"""Exercise BOTH foundation output paths/all9arms without real model weights.

All fake predictions live in temporary directories and are never research
results. This regression catches the missing scenario metadata field that
input-only tests did not exercise.
"""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import mta_model_engine_v2 as engine
import mta_holiday_study as study


class TensorFixture:
    def __init__(self, values): self.values = values
    def __getitem__(self, key): return TensorFixture(self.values[key])
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.values


class ChronosFixture:
    quantiles = [.01]+[k/20 for k in range(1, 20)]+[.99]
    @classmethod
    def from_pretrained(cls, *args, **kwargs): return cls()
    def predict(self, inputs, prediction_length, **kwargs):
        return [TensorFixture(np.tile(np.mean(item['target'])+np.asarray(self.quantiles)[:, None]*.01,
                                     (1, prediction_length))[None, :, :]) for item in inputs]


class TimesFixture:
    def __init__(self, *args, **kwargs): pass
    def predict_batch(self, inputs, horizon, **kwargs):
        return [SimpleNamespace(forecast=np.full(horizon, np.mean(item)+.005),
                    quantiles=np.tile(np.mean(item)+np.arange(1, 10)[None, :]*.001, (horizon, 1))) for item in inputs]


class MTAFoundationSchemaTests(unittest.TestCase):
    def test_both_providers_all_arms_write_complete_lag7_rows(self):
        days = pd.date_range('2023-01-01', '2026-10-21')
        data = pd.DataFrame({'MTA_Subway': 2.+np.arange(len(days))*.0001}, index=days)
        origin = pd.Timestamp('2026-09-10')
        cases = pd.DataFrame([dict(family='fixture_event', state='MTA_Subway', year=2026,
            origin=origin, date=origin+pd.Timedelta(days=h-1), horizon=h,
            decision_origin='2026-09-17', decision_lead=h-7,
            actual=float(data.loc[origin+pd.Timedelta(days=h-1), 'MTA_Subway'])) for h in [8, 14, 21]])
        modules = {
            'torch': SimpleNamespace(set_num_threads=lambda n: None, manual_seed=lambda n: None),
            'chronos': SimpleNamespace(Chronos2Pipeline=ChronosFixture),
            'timesfm3': SimpleNamespace(TimesFM3Evaluator=TimesFixture, ModelConfig=lambda **kwargs: kwargs),
        }
        for worker in ['chronos', 'timesfm']:
            with self.subTest(provider=worker), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                out = root/'cohort'
                output = out/worker
                output.mkdir(parents=True)
                weights = root/'fixture_weights'
                weights.write_bytes(b'SYNTHETIC UNIT FIXTURE; NOT MODEL WEIGHTS')
                digest = hashlib.sha256(weights.read_bytes()).hexdigest()
                for relative, value in [
                    ('results/mechanism_controls_v1/chronos_download.json',
                     dict(files=[dict(name='model.safetensors', path=str(weights), sha256=digest)])),
                    ('results/second_model_audit_v1/weight_download.json', dict(path=str(weights), sha256=digest))]:
                    p = root/relative
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(json.dumps(value))
                protocol = dict(threads=2, seed=42, horizon=21, batch=16, expected_tasks=1)
                self.assertNotIn('scenario', protocol)
                (out/'protocol.json').write_text(json.dumps(protocol))
                with patch.dict(sys.modules, modules), patch.object(engine, 'ROOT', root), \
                     patch.object(engine, 'OUT', out), patch.object(engine, 'ARMS', study.FOUNDATION_ARMS), \
                     patch.object(engine, 'frames', study.frames), \
                     patch.object(engine, 'setup', return_value=(protocol, output, cases, data)), redirect_stdout(io.StringIO()):
                    engine.foundation(worker)
                actual = pd.read_csv(output/'predictions.csv')
                self.assertEqual(len(actual), 27)
                self.assertEqual(set(actual.arm), set(study.FOUNDATION_ARMS))
                self.assertEqual(set(actual.scenario), {'lag7'})
                self.assertEqual(set(actual.horizon), {8, 14, 21})
                self.assertTrue((actual.horizon-actual.decision_lead == 7).all())
                self.assertEqual(json.loads((output/'run.json').read_text())['rows'], 27)


if __name__ == '__main__':
    unittest.main()
