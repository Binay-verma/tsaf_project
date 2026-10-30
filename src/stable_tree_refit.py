"""New versioned tree-only run with an explicit float32 feature interface."""
from pathlib import Path
import hashlib
import json
import numpy as np
import robust_baselines


if __name__ == '__main__':
    original_design = robust_baselines.design_frame

    def stable_design(*args, **kwargs):
        frame, event = original_design(*args, **kwargs)
        return frame.astype(np.float32), event

    robust_baselines.design_frame = stable_design
    # Explicit --out remains mandatory to protect the historical version1 run.
    import sys
    if '--out' not in sys.argv:
        raise ValueError('Supply --out results/stable_tree_refit_v2 with its recorded protocol')
    index = sys.argv.index('--out')+1
    sys.argv[index] = str(Path(sys.argv[index]).resolve())
    robust_baselines.main()
    out = Path(sys.argv[sys.argv.index('--out')+1])
    metadata = json.loads((out/'run.json').read_text())
    metadata['numerical_contract'] = 'float32 complete feature matrix, including query rows'
    metadata['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out/'run.json').write_text(json.dumps(metadata, indent=2)+'\n')
