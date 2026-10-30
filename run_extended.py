"""Reproduce expanded validation, including a pre-test selected exploratory baseline."""
import subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
def run(name):subprocess.run([sys.executable,str(p/'src'/name)],check=True,cwd=p)
for script in ['cache_identity.py','test_extended.py','audit_regional_calendars.py','extended_validation.py','extended_sarimax.py','repair_sarimax_optimizer.py','strong_baseline.py','summarize_extended.py','write_validation_report.py']:run(script)
print('Completed. See results/extended_validation and VALIDATION_REPORT.md.')
