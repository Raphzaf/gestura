import sys, cv2, numpy as np, glob, os
files = sys.argv[2:]
tiles = []
for f in files:
    im = cv2.resize(cv2.imread(f), (960, 540), interpolation=cv2.INTER_AREA)
    cv2.putText(im, os.path.basename(f)[2:-4] + "s", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(im)
while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i+2]) for i in range(0, len(tiles), 2)]
cv2.imwrite(sys.argv[1], np.vstack(rows))
