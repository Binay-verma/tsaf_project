import unittest
import numpy as np
from pooling_simulation import generate
from event_comparators import fit_responses


class SimulationTests(unittest.TestCase):
    def test_noiseless_correct_dates_recover_heterogeneous_effects(self):
        truth,x,y,beta,_=generate(1,1,3.,0,0.)
        typed,_,_,_=fit_responses(x[:730],y[:730])
        np.testing.assert_allclose(typed,beta,atol=1e-12)
        np.testing.assert_allclose(x,truth)

    def test_future_outcomes_cannot_change_fit(self):
        _,x,y,_,_=generate(42,4,3.,2,3.)
        before=fit_responses(x[:730],y[:730])
        y[730:]=1e14
        after=fit_responses(x[:730],y[:730])
        for a,b in zip(before,after):np.testing.assert_array_equal(a,b)


if __name__=='__main__':unittest.main()
