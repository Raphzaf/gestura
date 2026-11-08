# Build Microsoft Store (MSIX)

Profil de build **isolé** pour publier Gestura sur le Microsoft Store. Il ne touche
pas au build classique (`dist/`, `installer/`, `release.yml`) : tout est produit dans
`store/out/`, ignoré par git.

| Fichier | Rôle |
|---|---|
| `build_store.py` | Script unique : validation, manifeste, logos, PyInstaller, MSIX, signature de test, soumission |
| `AppxManifest.template.xml` | Manifeste MSIX ; les `${...}` sont remplis depuis l'environnement et `pyproject.toml` |
| `.env.example` | Modèle de configuration (versionné, **toutes les valeurs vides**) |
| `.env` | Ta configuration réelle — **ignorée par git, ne jamais la committer** |
| `PUBLICATION.md` | **Liste de contrôle pour publier sur le Store**, étape par étape |
| `listing.md` | Textes de la fiche Store (FR/EN), notes de certification, justification de `runFullTrust` |
| `../.github/workflows/store.yml` | Même build sur GitHub Actions (manuel), secrets lus depuis GitHub |

## 1. Configuration

```powershell
copy store\.env.example store\.env
```

Remplis ensuite `store\.env` :

| Variable | Où la trouver | Secrète | Requise pour |
|---|---|---|---|
| `GESTURA_STORE_IDENTITY_NAME` | Partner Center > ton app > Gestion du produit > Identité du produit (`Package/Identity/Name`) | non | build |
| `GESTURA_STORE_PUBLISHER` | idem (`Package/Identity/Publisher`, commence par `CN=`) | non | build |
| `GESTURA_STORE_PUBLISHER_DISPLAY_NAME` | idem (`Package/Properties/PublisherDisplayName`) | non | build |
| `MSSTORE_TENANT_ID`, `MSSTORE_CLIENT_ID`, `MSSTORE_CLIENT_SECRET` | Partner Center > Paramètres du compte > Gestion des utilisateurs > Applications Azure AD | **oui** | `--submit` |
| `MSSTORE_SELLER_ID` | Partner Center > Paramètres du compte > Paramètres légaux / ID du vendeur | **oui** | `--submit` |
| `MSSTORE_PRODUCT_ID` | ID Store du produit (`9N…`) | non | `--submit` |
| `GESTURA_SIGN_CERT_PFX`, `GESTURA_SIGN_CERT_PASSWORD` | Ton certificat de test (`.pfx`) | **oui** | `--sign` |

Règles de sécurité appliquées par le script :

* les variables déjà présentes dans l'environnement (secrets CI) **priment** sur `store/.env` ;
* les valeurs secrètes sont **masquées** (`****`) dans toutes les commandes et sorties affichées ;
* le manifeste refuse tout placeholder secret : aucun identifiant de soumission ne peut finir dans le paquet ;
* `.gitignore` exclut `.env`, `.env.*` (sauf `.env.example`), `*.pfx`, `*.p12` et `store/out/`.

Vérifie à tout moment : `git check-ignore -v store/.env` doit afficher la règle `.env`.

## 2. Commandes

```powershell
python store\build_store.py --check                 # valide la config, génère manifeste + logos (tout OS)
python store\build_store.py                         # MSIX à téléverser (Windows + Windows SDK)
python store\build_store.py --sign                  # + copie signée pour tester sur ton PC
python store\build_store.py --submit                # + envoi dans Partner Center (brouillon)
python store\build_store.py --submit --commit       # + soumission à la certification
python store\build_store.py --submit --package store\out\Gestura_0.4.0.0_x64.msix   # soumettre sans rebuild
```

Sortie : `store\out\Gestura_<version>.0_x64.msix`. La version vient de `pyproject.toml`
(`0.4.0` → `0.4.0.0` ; le Store exige un dernier chiffre à 0). Code de sortie 2 =
configuration manquante ou invalide (le message liste les variables à renseigner).

Prérequis Windows : Python 3.12 + `pip install -r requirements-dev.txt pyinstaller`,
Windows 10/11 SDK (`makeappx.exe`, `signtool.exe`), et pour `--submit` le
[Microsoft Store Developer CLI](https://github.com/microsoft/msstore-cli) (`msstore`).

## 3. Signature

Le paquet envoyé au Store reste **non signé** : Microsoft le signe lors de la
certification, aucun certificat n'est donc nécessaire pour publier. `--sign` produit
uniquement une copie `*_test-signed.msix` pour l'installer sur ton PC ; le sujet du
certificat doit être identique à `GESTURA_STORE_PUBLISHER` et le certificat doit être
approuvé sur la machine (magasin « Personnes autorisées » / Trusted People).

## 4. CI (GitHub Actions)

`Actions > Microsoft Store > Run workflow` construit le MSIX sur `windows-latest` et le
publie comme artefact `Gestura-msix` ; cocher **submit** l'envoie dans Partner Center
(brouillon, ou certification si **commit** est coché). Configuration dans
`Settings > Secrets and variables > Actions`, **mêmes noms** que dans `store/.env` :

* *Variables* (facultatives : l'identité de Gestura, `RaphZaf.Gestura`, est déjà la
  valeur par défaut du workflow) : `GESTURA_STORE_IDENTITY_NAME`, `GESTURA_STORE_PUBLISHER`,
  `GESTURA_STORE_PUBLISHER_DISPLAY_NAME`, `MSSTORE_PRODUCT_ID` ;
* *Secrets* : `MSSTORE_TENANT_ID`, `MSSTORE_SELLER_ID`, `MSSTORE_CLIENT_ID`, `MSSTORE_CLIENT_SECRET`.

L'option **test_signed** (cochée par défaut) ajoute à l'artefact une copie signée avec un
certificat de test jetable et ce certificat (`Gestura-test-certificate.cer`), pour
installer le paquet sur ton PC sans outil de développement. La clé privée de ce
certificat n'existe que pendant l'exécution, puis elle est supprimée.

La soumission tourne dans un job séparé, lié à l'environnement GitHub
`microsoft-store` : tu peux y ajouter une approbation obligatoire avant tout envoi.
Les secrets ne sont donnés qu'à ce job.

## 5. Particularités du paquet

* **`runFullTrust`** (capacité restreinte) : nécessaire pour une application Win32 qui
  injecte souris et clavier. À justifier dans les notes de soumission, par exemple :
  « Gestura est un logiciel d'accessibilité qui contrôle la souris et le clavier par
  gestes captés par la webcam ; le traitement est 100 % local, aucune image n'est
  enregistrée ni envoyée. »
* **Webcam** : déclarée (`DeviceCapability webcam`) ; Windows demande l'autorisation au
  premier lancement.
* **Lancement au démarrage** : un paquet MSIX ne peut pas utiliser la clé `Run` du
  registre. Le manifeste déclare une tâche de démarrage désactivée par défaut ;
  l'utilisateur l'active dans *Paramètres Windows > Applications > Démarrage*.
  L'application détecte qu'elle est empaquetée et l'indique au lieu d'écrire dans le
  registre.
* **Paramètres et journaux** : écrits dans `%APPDATA%\Gestura`, que Windows redirige
  vers le dossier privé du paquet ; ils sont supprimés à la désinstallation.

## 6. À vérifier avant la première soumission

* Les options exactes du CLI `msstore` évoluent : contrôle-les avec
  `msstore reconfigure --help` et `msstore publish --help`, puis ajuste `submit()` dans
  `build_store.py` si besoin.
* Teste le paquet signé localement (`--sign`, puis double-clic sur le `.msix`) et lance
  le [Windows App Certification Kit](https://learn.microsoft.com/windows/uwp/debug-test-perf/windows-app-certification-kit)
  avant d'envoyer.
* La fiche Store (captures, description, politique de confidentialité) se remplit dans
  Partner Center ; une URL de politique de confidentialité est exigée pour les apps
  qui utilisent la webcam.
