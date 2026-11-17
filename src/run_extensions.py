import argparse
import subprocess
import sys
import time

from src.config import RESULTS_DIR
from src.run_experiment import ROOT

EXTENSIONS_DIR = RESULTS_DIR / "extensions"
RUNS_DIR = EXTENSIONS_DIR / "runs"
WORKERS = 3


def config(label, name, *options):
    return {"label": label, "name": name, "options": list(options)}


GROUPS = {
    "E1": [
        config("E1a", "E1a_celoe_strict_disc_hv1_n0_europe", "--membership", "strict", "--has-value", "--problem", "europe"),
        config("E1b", "E1b_celoe_strict_disc_hv0_n0_europe", "--membership", "strict", "--no-has-value", "--problem", "europe"),
        config("E1c", "E1c_celoe_extended_disc_hv1_n0_europe", "--membership", "extended", "--has-value", "--problem", "europe"),
    ],
    "E2": [
        config("E2a", "E2a_celoe_strict_b3_hv1_n0", "--membership", "strict", "--has-value", "--bins", "3"),
        config("E2b", "E2b_celoe_strict_b5_hv1_n0", "--membership", "strict", "--has-value", "--bins", "5"),
    ],
    "E4": [
        config("E4a", "E4a_celoe_strict_disc_hv1_n0_t300", "--membership", "strict", "--has-value", "--time", "300",
               "--repeats", "0", "--folds", "0,1,2,3,4"),
        config("E4b", "E4b_celoe_strict_disc_hv0_n0_t300", "--membership", "strict", "--no-has-value", "--time", "300",
               "--repeats", "0", "--folds", "0,1,2,3,4"),
    ],
}


def run_config(c):
    command = [sys.executable, "-m", "src.run_experiment", "--name", c["name"], "--algorithm", "celoe", "--noise", "0",
               "--workers", str(WORKERS), "--runs-dir", str(RUNS_DIR)]
    command += [] if "--time" in c["options"] else ["--time", "60"]
    command += c["options"]
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] {c['name']} ...", flush=True)
    subprocess.run(command, cwd=ROOT, check=False)
    print(f"[{time.strftime('%H:%M:%S')}] {c['name']} finished in {time.time() - start:.0f}s", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=list(GROUPS))
    args = parser.parse_args()
    for c in GROUPS[args.group]:
        run_config(c)


if __name__ == "__main__":
    main()
