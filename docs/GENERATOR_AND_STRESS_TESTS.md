# Generator and Stress-Test Design

## Generator defaults

| Parameter | Default | Stress range |
|---|---:|---:|
| Reference size | 1000×1000 | fixed |
| Search size | 1000×1000 | fixed |
| Reference scale | 1 nm/px | fixed |
| Search scale | 10 nm/px | fixed |
| Rotation | uniform 0–360° | full continuous range |
| Scale variation | 0.75×–1.25× | 0.5×–2.0× |
| Edge brightening | 0.20 | 0.0–0.60 |
| Reference Gaussian noise | 3 | 0–10 |
| Search Gaussian noise | 8 | 0–20 |

## Stress categories

### Typical

- nominal 0° rotation;
- nominal 1.0× scale;
- moderate independent noise;
- normal edge brightening;
- DRAM and FinFET.

### Boundary

- rotation near 0° and 360°;
- scale near 0.5× and 2.0×;
- zero edge brightening;
- zero sensor noise.

### Edge

- 90°, 180°, 270° rotations;
- 0.5×, 0.75×, 1.5× and 2.0× scale;
- high edge brightening;
- high search noise.

### Combined worst case

The executed stress condition combines:

- rotation 137°;
- scale 0.75×;
- edge brightening 0.40;
- reference noise 10;
- search noise 20;
- elevated search speckle;
- elevated impulse noise.

## Known breaking points

The executed sweep shows that the hybrid remains strong across 0.5×–1.5× scale in the tested seeds, while 2.0× scale and some very high edge-brightening conditions can produce degraded localization. These cases are intentionally preserved as adversarial evidence rather than hidden.
