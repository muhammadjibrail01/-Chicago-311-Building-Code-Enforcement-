"""Run the whole Paper 4 analysis in order:   python run_all.py            (all steps)
                                             python run_all.py --from 3  (resume from step 3)
                                             python run_all.py --only 7  (one step)
Logs are written to WORK_DIR/logs/. Prerequisite: Paper 1's steps 00 and 02 (they write tract.csv and the tract shapefile)."""
import argparse, glob, os, subprocess, sys, time
from config import WORK_DIR
HERE = os.path.dirname(os.path.abspath(__file__)); CODE = os.path.join(HERE, "code")
ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="start", type=int, default=1); ap.add_argument("--only", type=int); a = ap.parse_args()
os.makedirs(os.path.join(WORK_DIR, "logs"), exist_ok=True)
env = dict(os.environ, PYTHONPATH=os.pathsep.join([HERE, CODE, os.environ.get("PYTHONPATH", "")]), MPLBACKEND="Agg")
for s in sorted(glob.glob(os.path.join(CODE, "[0-9][0-9]_*.py"))):
    k = int(os.path.basename(s)[:2])
    if (a.only is not None and k != a.only) or k < a.start: continue
    t = time.time(); log = os.path.join(WORK_DIR, "logs", os.path.basename(s).replace(".py", ".log"))
    with open(log, "w") as fh: rc = subprocess.run([sys.executable, s], cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
    print(f"[{'OK  ' if rc == 0 else 'FAIL'}] {os.path.basename(s):28s} {time.time() - t:7.1f}s   log: {log}", flush=True)
    if rc != 0:
        print("Stopped. Open the log above to see the error, fix it, then resume with --from", k); sys.exit(1)
print("All steps finished. The manuscript is in", os.path.join(HERE, "manuscript"))
