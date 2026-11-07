"""Synthetic checks of the combination analysis (no project outcomes)."""
import unittest
import numpy as np
import pandas as pd
import representation_combination_v1 as r


class CombinationTests(unittest.TestCase):
    def test_frame_and_balanced(self, ):
        rows = []
        for arm, bias in [('day5', 1.), ('pooled_day5', -1.), ('window5', 2.), ('pooled_window5', 0.)]:
            for fam in ['A', 'B']:
                for y in [2024, 2025]:
                    rows.append(dict(version='document_aligned', model='ridge', family=fam, state='S', year=y, date=f'{y}-01-02',
                                     origin=f'{y}-01-02', horizon=1, actual=10., mase_scale=1., prediction=10.+bias, arm=arm))
        path = r.ROOT/'results/_synthetic_combination_test.csv'
        pd.DataFrame(rows).to_csv(path, index=False)
        try:
            x = r.frame(str(path.relative_to(r.ROOT)), True)
        finally:
            path.unlink()
        day = x[x.representation.eq('day')]
        self.assertTrue((day.typed == 1).all() and (day.pooled == 1).all() and (day["combine"] == 0).all())
        win = x[x.representation.eq('window')]
        self.assertTrue((win.typed == 2).all() and (win.pooled == 0).all() and (win["combine"] == 1).all())
        b = r.balanced(x, 'combine')
        self.assertEqual(b[('ridge', 'day', 1)], 0.); self.assertEqual(b[('ridge', 'window', 1)], 1.)


if __name__ == '__main__':
    unittest.main()
