import datetime as dt
import unittest
from pathlib import Path
import json
import tempfile
from collect_prospective_actuals import ready,extract,complete_result


class CollectionChecks(unittest.TestCase):
    def test_partial_existing_output_is_not_called_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'audit.json').write_text('{}')
            self.assertFalse(complete_result(root))

    def test_clock_gate_and_no_recurrence_in_other_years(self):
        self.assertFalse(ready(dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)))
        self.assertFalse(ready(dt.datetime(2026,11,11,tzinfo=dt.timezone.utc)))
        self.assertTrue(ready(dt.datetime(2026,11,12,tzinfo=dt.timezone.utc)))
        self.assertFalse(ready(dt.datetime(2027,11,12,tzinfo=dt.timezone.utc)))

    def test_incomplete_actuals_not_scored(self):
        root=Path(__file__).resolve().parents[1]
        raw=(root/'data/external/POSOCO_data.csv').read_bytes()
        meta=json.loads((root/'data/external/POSOCO_metadata.json').read_text())
        self.assertIsNone(extract(raw,meta))

    def test_wrong_units_are_rejected(self):
        root=Path(__file__).resolve().parents[1]
        meta=json.loads((root/'data/external/POSOCO_metadata.json').read_text())
        for field in meta['fields']:
            if field['name']=='Delhi: EnergyMet':field['units']='MW'
        with self.assertRaises(ValueError):
            extract((root/'data/external/POSOCO_data.csv').read_bytes(),meta)


if __name__=='__main__':
    unittest.main(verbosity=2)
