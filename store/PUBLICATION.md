# Publier Gestura sur le Microsoft Store — liste de contrôle

Liste dans l'ordre. ✅ = déjà fait dans le dépôt. ☐ = à faire par toi.
Temps total estimé : **une journée de travail**, plus les délais de Microsoft
(vérification du compte, certification : quelques jours).

Fichiers utiles :
[`store/listing.md`](listing.md) (textes de la fiche, notes de certification) ·
[`PRIVACY.md`](../PRIVACY.md) (politique de confidentialité) ·
[`store/README.md`](README.md) (détail du script de build).

> Je n'ai pas pu consulter la documentation officielle de Microsoft (learn.microsoft.com
> bloqué depuis l'environnement de rédaction). Les noms de menus et les délais viennent
> de sources secondaires : **Partner Center fait foi** s'il affiche autre chose.

---

## Étape 0 — Ce qui est déjà prêt

- ✅ Paquet MSIX : manifeste, logos, script `store/build_store.py`, workflow GitHub
  « Microsoft Store »
- ✅ Secrets lus depuis `store/.env`, ignoré par git ; historique git vérifié : aucun
  secret ni certificat committé
- ✅ Démarrage automatique compatible MSIX (tâche de démarrage Windows)
- ✅ Lien vers la licence GPL v3 et le code source dans l'application (obligation de
  la GPL quand on distribue le programme)
- ✅ Politique de confidentialité FR/EN (`PRIVACY.md`)
- ✅ Textes de la fiche FR/EN, notes de certification, justification de `runFullTrust`
  (`store/listing.md`)

## Étape 1 — Préparer le dépôt GitHub (15 min)

- ☐ **Fusionner la branche dans `main`** : la politique de confidentialité et le
  profil Store doivent être sur `main` pour avoir des liens stables.
- ☐ **Rendre le dépôt public** : *GitHub > Settings > General > Danger Zone > Change
  visibility*. C'est **obligatoire** ici, pour trois raisons :
  1. la **GPL** impose de donner accès au code source à ceux qui reçoivent le
     programme ;
  2. le Store exige une **URL de politique de confidentialité** accessible à tous
     (l'application utilise la webcam) ;
  3. les **avis et le support** renvoient vers les tickets GitHub.

  Bonus : GitHub Actions devient gratuit et illimité pour un dépôt public.
- ☐ Vérifier que ces liens s'ouvrent **sans être connecté à GitHub** (fenêtre de
  navigation privée) :
  - <https://github.com/Raphzaf/gestura/blob/main/PRIVACY.md>
  - <https://github.com/Raphzaf/gestura/issues>

## Étape 2 — Créer le compte développeur (30 min + vérification)

- ☐ Créer un compte développeur Microsoft Store **individuel** sur
  <https://storedeveloper.microsoft.com> (ou <https://partner.microsoft.com/dashboard>).
  - L'inscription est annoncée **gratuite pour les particuliers** depuis 2025 (une
    seule source, à confirmer à l'inscription).
  - Prévoir une **vérification d'identité** (pièce d'identité), qui peut prendre
    quelques jours.
  - Le **nom d'éditeur affiché** sera visible dans le Store : ton nom, ou un nom
    commercial si tu en as un.
- ☐ **Profil de paiement** : IBAN du compte qui recevra les ventes.
- ☐ **Profil fiscal** : formulaire américain **W-8BEN** (personne physique non
  américaine), pour éviter une retenue d'impôt aux États-Unis.
- ☐ **Statut fiscal en France** : des ventes régulières relèvent en principe d'une
  activité déclarée (par exemple une micro-entreprise). **À vérifier avec un
  comptable** avant les premières ventes.

## Étape 3 — Réserver le nom et récupérer l'identité du paquet (10 min)

- ☐ *Partner Center > Applications et jeux > Nouveau produit > Application MSIX ou PWA*
  → réserver le nom **« Gestura »**. S'il est pris : « Gestura – Gesture Control » ou
  « Gestura Hands-Free ».
- ☐ *Gestion du produit > Identité du produit* : copier les valeurs dans `store/.env` :

  | Partner Center | `store/.env` |
  |---|---|
  | Package/Identity/Name | `GESTURA_STORE_IDENTITY_NAME` |
  | Package/Identity/Publisher (commence par `CN=`) | `GESTURA_STORE_PUBLISHER` |
  | Package/Properties/PublisherDisplayName | `GESTURA_STORE_PUBLISHER_DISPLAY_NAME` |
  | ID Store (`9N…`) | `MSSTORE_PRODUCT_ID` (seulement pour l'envoi automatique, étape 7) |

## Étape 4 — Construire et tester le paquet (30 min)

Identité du paquet de Gestura (Partner Center > Identité du produit) :

| Champ | Valeur |
|---|---|
| Package/Identity/Name | `RaphZaf.Gestura` |
| Package/Identity/Publisher | `CN=6E503161-3688-4B42-BF41-89B48D3EC8F0` |
| PublisherDisplayName | `RaphZaf` |
| ID Store | `9N969KZPH44B` |

Ces valeurs ne sont pas secrètes (elles figurent dans chaque paquet publié) : elles sont
déjà les valeurs par défaut du workflow GitHub.

### Option A (recommandée) — GitHub construit le paquet, sans rien installer

1. ☐ GitHub > **Actions** > **Microsoft Store** > **Run workflow** (laisser
   *test_signed* coché, *submit* décoché) > **Run workflow**. Durée : 15 à 25 min.
2. ☐ À la fin, ouvrir l'exécution et télécharger l'artefact **Gestura-msix** (en bas
   de la page), puis extraire le zip. Il contient :
   - `Gestura_0.3.0.0_x64.msix` → **le fichier à envoyer au Store** (étape 6) ;
   - `Gestura_0.3.0.0_x64_test-signed.msix` → la copie à installer sur ton PC ;
   - `Gestura-test-certificate.cer` → le certificat de cette copie.
3. ☐ Faire confiance au certificat de test (une fois par build) : clic droit sur
   **Démarrer** > **Terminal (administrateur)**, aller dans le dossier extrait, puis :
   ```powershell
   Import-Certificate -FilePath .\Gestura-test-certificate.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople
   ```
   (Ou : double-clic sur le `.cer` > *Installer le certificat* > *Ordinateur local* >
   *Placer tous les certificats dans le magasin suivant* > **Personnes autorisées**.)
4. ☐ Double-clic sur `Gestura_0.3.0.0_x64_test-signed.msix` > **Installer**.
5. ☐ Faire les tests de la section 4.4 ci-dessous.

La clé privée de ce certificat est détruite à la fin du build : personne ne peut
signer autre chose avec. Une fois les tests finis, tu peux le retirer
(`certlm.msc` > Personnes autorisées > Certificats > « Gestura test (CI) » > Supprimer).

### Option B — tout construire sur ton PC

Utile seulement si tu veux modifier le code et le tester sans passer par GitHub.

#### B.1 Installer les outils (une seule fois)
- ☐ Python 3.12 (python.org, cocher « Add to PATH ») et Git
- ☐ **Windows SDK** (fournit `makeappx`, `signtool` et le kit de certification) :
  installateur autonome du Windows 10/11 SDK sur le site de Microsoft

```powershell
git clone https://github.com/Raphzaf/gestura.git
cd gestura
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt pyinstaller==6.22.3
pip install -e . --no-deps
copy store\.env.example store\.env
notepad store\.env
```

Dans `store\.env`, remplis les trois variables `GESTURA_STORE_*` (tableau ci-dessus), puis :

```powershell
python store\build_store.py --check
```

#### B.2 Créer un certificat de test (une seule fois)
Il sert **uniquement** à installer le paquet sur ton PC avant l'envoi. Le Store signe
lui-même le paquet final. Dans PowerShell, en remplaçant `CN=…` par **exactement** ta
valeur `GESTURA_STORE_PUBLISHER` :

```powershell
$cert = New-SelfSignedCertificate -Type Custom -Subject "CN=REMPLACER-PAR-TON-PUBLISHER" -KeyUsage DigitalSignature -FriendlyName "Gestura test" -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
```

```powershell
mkdir $env:USERPROFILE\certs -Force
$pw = Read-Host "Mot de passe du certificat" -AsSecureString
Export-PfxCertificate -Cert $cert -FilePath "$env:USERPROFILE\certs\gestura-test.pfx" -Password $pw
```

Faire confiance à ce certificat sur ton PC (PowerShell **administrateur**) :

```powershell
Import-PfxCertificate -FilePath "$env:USERPROFILE\certs\gestura-test.pfx" -CertStoreLocation Cert:\LocalMachine\TrustedPeople -Password (Read-Host -AsSecureString)
```

Puis, dans `store\.env` :
`GESTURA_SIGN_CERT_PFX=C:\Users\<toi>\certs\gestura-test.pfx` et
`GESTURA_SIGN_CERT_PASSWORD=<le mot de passe>`.
Le certificat reste **hors du dépôt** (et `*.pfx` est de toute façon ignoré par git).

#### B.3 Construire et installer

```powershell
python store\build_store.py --sign
```

Résultat dans `store\out\` :
- `Gestura_0.3.0.0_x64.msix` → **le fichier à envoyer au Store** (non signé) ;
- `Gestura_0.3.0.0_x64_test-signed.msix` → double-clic pour l'installer sur ton PC.

### 4.4 Tests à faire sur la version installée


- ☐ Gestura se lance depuis le menu Démarrer ; Windows demande l'accès à la caméra
- ☐ La caméra s'allume, la main est détectée, le curseur bouge (en quittant le mode
  test), le pincement clique
- ☐ Le clavier virtuel écrit dans le Bloc-notes, accents compris
- ☐ Arrêt d'urgence : bouton rouge et Ctrl+Alt+Maj+G
- ☐ Les réglages sont conservés après redémarrage de Gestura
- ☐ *Paramètres Windows > Applications > Démarrage* : « Gestura » apparaît (désactivé
  par défaut) ; l'activer, redémarrer la session, vérifier le lancement
- ☐ Les liens « GPL v3 » et « source code » en bas du menu s'ouvrent
- ☐ **Kit de certification** : lancer *Windows App Cert Kit* (installé avec le SDK),
  tester l'application Gestura installée, corriger les erreurs signalées
- ☐ **Désinstaller la version de test** avant d'installer un jour la version du Store
  (même identité, signatures différentes)

## Étape 5 — Préparer les images (30 min)

- ☐ **4 à 6 captures d'écran** en PNG, **1920 × 1080** de préférence (au moins
  1366 × 768), prises avec Win + Maj + S ou Impr. écran :
  1. Tableau de bord avec l'aperçu de la caméra et la main détectée
  2. Gesture Studio (squelette de la main affiché)
  3. Clavier virtuel au-dessus du Bloc-notes
  4. Assistant de calibration
  5. Réglages (association des gestes)
- ☐ Vérifier qu'aucune information personnelle n'apparaît (notifications, onglets,
  noms de fichiers). Ton visage apparaît dans l'aperçu : cadre la caméra sur la main
  si tu préfères.
- ☐ Facultatif : une **courte vidéo** (30 à 60 s) ; le film de lancement de
  `promo/launch_film` peut servir de base.

## Étape 6 — Remplir la soumission dans Partner Center (1 h)

### Tarification et disponibilité
- ☐ Marchés : tous (ou au minimum France, Belgique, Suisse, Canada, Union européenne,
  États-Unis, Royaume-Uni)
- ☐ Visibilité : publique
- ☐ **Prix : 12,99 €** — Partner Center propose des paliers de prix ; choisir le
  palier le plus proche et vérifier le prix affiché pour la France
- ☐ **Essai gratuit : aucun.** La version gratuite de GitHub joue ce rôle ; un essai
  limité dans le temps demanderait du code en plus
- ☐ Publication : **manuelle** après certification (pour choisir le jour)

### Propriétés
- ☐ Catégorie : **Utilitaires et outils** (ou Productivité)
- ☐ URL de la politique de confidentialité :
  `https://github.com/Raphzaf/gestura/blob/main/PRIVACY.md`
- ☐ Site web : `https://github.com/Raphzaf/gestura`
- ☐ Contact du support : `https://github.com/Raphzaf/gestura/issues` (ou une adresse
  e-mail dédiée : elle sera publique)
- ☐ Configuration requise : **Caméra** en « minimum » ; souris et clavier non requis
- ☐ Ne **pas** cocher « testé pour respecter les règles d'accessibilité » sans test
  formel

### Classification par âge
- ☐ Questionnaire IARC : catégorie utilitaire ; aucune violence, aucun contenu
  généré par d'autres utilisateurs, aucun partage de position, aucun achat dans
  l'application → classification attendue : **3+**

### Paquets
- ☐ Envoyer `store\out\Gestura_0.3.0.0_x64.msix` (**le non signé**)
- ☐ Famille d'appareils : **Windows 10/11 Desktop** uniquement

### Fiches du Store (FR et EN)
- ☐ Copier description, description courte, fonctionnalités, nouveautés et termes
  de recherche depuis [`store/listing.md`](listing.md)
- ☐ Ajouter les captures de l'étape 5

### Options de soumission
- ☐ **Capacités restreintes** : coller la justification de `runFullTrust` depuis
  `store/listing.md`
- ☐ **Notes pour la certification** : coller le bloc prévu dans `store/listing.md`

### Envoi
- ☐ *Soumettre pour la certification*. Délai indicatif : jusqu'à quelques jours
  ouvrés. En cas de refus, Microsoft envoie un rapport qui indique la règle en cause :
  corriger, renvoyer.

## Étape 7 — Après la publication : rendre le tout le plus passif possible

- ☐ Ajouter le lien du Store dans le README (en haut, FR et EN)
- ☐ **Mises à jour sans intervention manuelle** : créer une application Microsoft
  Entra dans *Partner Center > Paramètres du compte > Gestion des utilisateurs*, puis
  renseigner les variables et secrets GitHub listés dans `store/README.md`. Ensuite,
  une mise à jour = changer la version dans `pyproject.toml` +
  *Actions > Microsoft Store > Run workflow* (cocher *submit*)
- ☐ Une fois par mois (15 min) : lire les avis et les rapports de plantage
  (*Partner Center > Santé*), répondre aux avis négatifs, mettre à jour
  `docs/TROUBLESHOOTING.md` pour les questions qui reviennent
- ☐ Une ou deux fois par an : mettre à jour les dépendances (MediaPipe, Qt, OpenCV),
  vérifier que tout fonctionne, publier une version
- ☐ Suivre les ventes : *Partner Center > Analyse > Acquisitions*. Objectif réaliste :
  1 à 4 k€ par an au début

## Récapitulatif

| Étape | Qui | Durée |
|---|---|---|
| 0. Paquet, textes, politique de confidentialité | ✅ fait | — |
| 1. Fusion dans `main`, dépôt public | Toi | 15 min |
| 2. Compte développeur, paiement, fiscalité | Toi | 30 min + vérification |
| 3. Réservation du nom, identité | ✅ fait | — |
| 4. Build (GitHub) et tests sur ton PC | Toi | 30 min |
| 5. Captures d'écran | Toi | 30 min |
| 6. Soumission | Toi | 1 h + certification |
| 7. Automatisation des mises à jour | Toi | 30 min |
