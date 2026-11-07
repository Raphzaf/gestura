# Mesures de friction matérielle

Scripts qui ont produit les chiffres de `docs/friction_utilisation.md`, avec le vrai
moteur de Gestura (modèles MediaPipe). Les photos ne sont pas fournies : utilisez un
dossier de vos propres images contenant des mains.

```bash
python scripts/friction/robustness.py <dossier_images> robustness.json
```

```bash
python scripts/friction/cpu2.py <image_avec_une_main.jpg> cpu.json
```

`distance_far.py` ajoute les distances les plus grandes (lancer depuis `scripts/friction/`).
