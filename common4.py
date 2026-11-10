import os, glob, json, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from config import RAW_DIR, P1_WORK, WORK_DIR, OUT_DIR

EXTRACT = pd.Timestamp("2026-09-23")      # date of the Chicago Data Portal download (administrative censoring date)
USECOLS = ["ID", "VIOLATION DATE", "VIOLATION CODE", "VIOLATION STATUS", "VIOLATION STATUS DATE", "INSPECTION NUMBER",
           "INSPECTION STATUS", "INSPECTION CATEGORY", "DEPARTMENT BUREAU", "LATITUDE", "LONGITUDE"]
BASE = ["hard_z", "yb_z", "own_z", "ldens_z"]
CATS = ["COMPLAINT", "PERIODIC", "PERMIT"]

def W(*p): return os.path.join(WORK_DIR, *p)
def zs(s): return (s - s.mean()) / s.std()

class Enc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, pd.Timestamp): return str(o)
        return super().default(o)
def jdump(obj, path): json.dump(obj, open(path, "w"), indent=1, cls=Enc)
def jload(path): return json.load(open(path))

def summarize(params, bse, names, df):
    """exp(b), t-based 95% CI with df = G-1, p-value from t."""
    out = {}
    tc = stats.t.ppf(0.975, df)
    for c in names:
        b, se = float(params[c]), float(bse[c])
        out[c] = dict(b=b, se=se, irr=float(np.exp(b)), lo=float(np.exp(b - tc * se)), hi=float(np.exp(b + tc * se)),
                      p=float(2 * stats.t.sf(abs(b / se), df)))
    return out

def pois_fit(d, y, xc, group="ca", off="off"):
    """Poisson regression with a log-exposure offset; standard errors clustered by `group`; t(G-1) inference."""
    d = d[[y, off, group] + xc].dropna()
    X = sm.add_constant(d[xc].astype(float))
    m = sm.GLM(d[y].astype(float), X, family=sm.families.Poisson(), offset=d[off]).fit(
        cov_type="cluster", cov_kwds={"groups": d[group].values})
    G = d[group].nunique()
    r = summarize(m.params, m.bse, xc, G - 1); r["_n"] = int(m.nobs); r["_G"] = int(G)
    return r
