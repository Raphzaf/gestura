import json, sys
from pathlib import Path
import robustness as r
r.CONDITIONS = {"distance_x0.18": lambda im: r.distance(im, 0.18), "distance_x0.12": lambda im: r.distance(im, 0.12)}
r.run(Path(sys.argv[1]), Path(sys.argv[2]))
