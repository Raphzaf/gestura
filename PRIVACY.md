# Politique de confidentialité — Gestura / Privacy policy — Gestura

*Dernière mise à jour / Last updated: 7 novembre 2026 / November 7, 2026*

[Français](#français) · [English](#english)

---

## Français

Gestura est un logiciel libre (GPL v3) qui permet de contrôler un ordinateur Windows
par des gestes de la main et des mouvements de la tête captés par la webcam.

**En résumé : Gestura ne collecte, n'enregistre et n'envoie aucune donnée personnelle.
Tout est traité sur votre ordinateur.**

### Ce que Gestura utilise, et ce qu'il en fait

| Donnée | Utilisation | Stockage | Envoi |
|---|---|---|---|
| **Images de la webcam** | Détecter la main et le visage pour reconnaître les gestes | **Aucun** : chaque image est analysée en mémoire puis effacée. Aucune photo ni vidéo n'est enregistrée | **Jamais** |
| **Points de repère de la main et du visage** (positions calculées à partir de l'image) | Reconnaître les gestes et déplacer le curseur | Aucun : en mémoire, pendant le fonctionnement | **Jamais** |
| **Réglages** (sensibilité, gestes, caméra choisie…) | Retrouver vos préférences | Fichier sur votre ordinateur, dans votre dossier d'application | **Jamais** |
| **Journal technique** (erreurs et avertissements) | Diagnostiquer un problème | Fichier sur votre ordinateur, limité à quelques mégaoctets. **Il ne contient ni images, ni texte tapé** | **Jamais**, sauf si vous choisissez de le joindre vous-même à un signalement |

- **Aucune connexion réseau** : Gestura ne se connecte à aucun serveur. Les modèles
  d'intelligence artificielle sont inclus dans l'application.
- **Aucun compte**, aucune publicité, aucune mesure d'audience, aucune télémétrie.
- **Aucun partage** avec des tiers.
- Le texte saisi avec le clavier virtuel est envoyé uniquement à l'application ouverte
  à l'écran, comme avec un clavier physique. Il n'est pas conservé par Gestura.

### Webcam
Windows vous demande l'autorisation d'utiliser la caméra. Vous pouvez la retirer à tout
moment dans *Paramètres Windows > Confidentialité et sécurité > Caméra*. Quand Gestura
utilise la caméra, Windows l'indique (voyant de la caméra, icône dans la barre des
tâches).

### Achat sur le Microsoft Store
Si vous achetez Gestura sur le Microsoft Store, le paiement et les informations de
votre compte Microsoft sont traités par Microsoft selon sa propre
[déclaration de confidentialité](https://privacy.microsoft.com/fr-fr/privacystatement).
L'éditeur de Gestura reçoit seulement ce que Microsoft fournit à tous les éditeurs :
des statistiques globales (nombre de ventes, pays, avis publiés) et, si Windows est
configuré pour les envoyer, des rapports de plantage techniques.

### Supprimer vos données
Désinstallez Gestura : les réglages et le journal installés par le Microsoft Store sont
supprimés avec l'application. Pour la version installée depuis GitHub, supprimez aussi
les dossiers `%APPDATA%\Gestura` et `%LOCALAPPDATA%\Gestura`.

### Enfants
Gestura ne collecte aucune donnée, y compris pour les enfants.

### Contact
Questions sur cette politique : ouvrez un ticket sur
<https://github.com/Raphzaf/gestura/issues>.

### Modifications
Toute modification de cette politique est publiée sur cette page, avec sa date. Le code
source étant public, chacun peut vérifier ce que fait le logiciel.

---

## English

Gestura is free software (GPL v3) that lets you control a Windows computer with hand
gestures and head movements captured by your webcam.

**In short: Gestura does not collect, store or send any personal data. Everything is
processed on your computer.**

### What Gestura uses, and what it does with it

| Data | Purpose | Storage | Sent anywhere |
|---|---|---|---|
| **Webcam images** | Detect your hand and face to recognise gestures | **None**: each frame is analysed in memory and discarded. No photo or video is ever saved | **Never** |
| **Hand and face landmarks** (positions computed from the image) | Recognise gestures and move the pointer | None: in memory while running | **Never** |
| **Settings** (sensitivity, gestures, selected camera…) | Remember your preferences | A file on your computer, in your application data folder | **Never** |
| **Technical log** (errors and warnings) | Troubleshooting | A file on your computer, capped at a few megabytes. **It contains no images and no typed text** | **Never**, unless you choose to attach it to a bug report yourself |

- **No network connection**: Gestura does not connect to any server. The AI models are
  bundled with the application.
- **No account**, no advertising, no analytics, no telemetry.
- **No sharing** with third parties.
- Text typed with the virtual keyboard goes only to the application on screen, as with
  a physical keyboard. Gestura does not keep it.

### Webcam
Windows asks for permission to use the camera. You can revoke it at any time in
*Windows Settings > Privacy & security > Camera*. Windows shows when the camera is in
use (camera light, taskbar icon).

### Microsoft Store purchases
If you buy Gestura from the Microsoft Store, payment and Microsoft account information
are handled by Microsoft under its own
[privacy statement](https://privacy.microsoft.com/privacystatement). The publisher only
receives what Microsoft provides to every publisher: aggregate statistics (number of
sales, countries, published reviews) and, if Windows is set to send them, technical
crash reports.

### Deleting your data
Uninstall Gestura: the settings and log of the Microsoft Store version are removed with
the app. For the version installed from GitHub, also delete the `%APPDATA%\Gestura` and
`%LOCALAPPDATA%\Gestura` folders.

### Children
Gestura collects no data from anyone, children included.

### Contact
Questions about this policy: open an issue at
<https://github.com/Raphzaf/gestura/issues>.

### Changes
Any change to this policy is published on this page with its date. The source code is
public, so anyone can check what the software does.
