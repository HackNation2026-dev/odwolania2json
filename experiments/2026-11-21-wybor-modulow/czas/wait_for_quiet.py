import sys, time
sys.path.insert(0, ".")
import tlib
lim = float(sys.argv[1]) if len(sys.argv) > 1 else 2700
g = tlib.wait_quiet(lim, strict=True, poll_s=15, label="oczekiwanie")
print(g, flush=True)
sys.exit(0 if g["quiet"] else 1)
