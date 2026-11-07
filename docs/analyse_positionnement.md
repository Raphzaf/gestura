# Analyse de positionnement — Gestura face aux solutions existantes

*Recherche web réalisée le 7 novembre 2026. Les prix proviennent de revendeurs et de
sites tiers : ils varient selon les sources et doivent être revérifiés avant toute
communication publique. Les sites officiels de Talon et de Cephable n'ont pas pu être
consultés directement (accès réseau bloqué pendant la recherche) ; les informations
les concernant viennent de sources secondaires, signalées comme telles.*

---

## 1. Résumé

Le marché du contrôle « mains libres » de l'ordinateur est déjà bien couvert pour
**la tête, les yeux et la voix** : les outils natifs de Windows et macOS sont gratuits,
Talon domine la voix pour les utilisateurs avancés, Tobii domine l'oculométrie, et
plusieurs logiciels gratuits (Camera Mouse, eViacam, Project Gameface, Cephable)
transforment une webcam en souris pilotée par la tête ou le visage.

Le créneau beaucoup moins occupé est **le contrôle complet du bureau par les gestes des
mains avec une simple webcam**, sans matériel dédié. Les seules alternatives sont soit
anciennes (NPointer, 2012–2013), soit des projets de démonstration sur GitHub, soit
du matériel spécifique (Ultraleap, ~140–220 $).

**Proposition de valeur unique de Gestura :**

> Gestura est la seule application qui remplace la souris et le clavier par des gestes
> naturels des mains — déplacer, cliquer, glisser-déposer, faire défiler, zoomer, régler
> le volume, gérer les fenêtres, taper — avec la webcam que vous avez déjà, complétée par
> la navigation à la tête, entièrement en local, gratuitement, et avec des garde-fous de
> sécurité (mode test, arrêt d'urgence, confirmations).

Gestura ne doit **pas** se présenter comme une alternative aux solutions d'accessibilité
pour les handicaps moteurs sévères des membres supérieurs (oculométrie, voix, souris
à la tête restent meilleures pour ce public). Son cœur de cible est l'**usage sans
contact** : mains occupées, sales ou stériles, utilisation à distance de l'écran,
et personnes qui peuvent bouger les bras mais ont du mal avec une souris.

---

## 2. Panorama des solutions

### 2.1 Tableau comparatif

| Solution | Entrée | Matériel requis | Prix | Plateformes | Code ouvert |
|---|---|---|---|---|---|
| **Gestura** | Mains (+ tête, clavier virtuel) | Webcam standard | Gratuit | Windows (code Python, portable) | Oui (GPL v3) |
| Talon Voice | Voix, bruits (« pop », « hiss »), oculométrie | Micro ; Tobii 4C/5 pour les yeux | Gratuit ; bêta « Talon+ » via Patreon (~25 $/mois selon une source secondaire) | Windows, macOS, Linux (X11) | Non (scripts utilisateur ouverts) |
| Cephable | Tête, expressions du visage, voix | Webcam + micro existants | Formule Basic gratuite pour les particuliers ; formules payantes Plus/Pro (prix non affichés) | Windows, macOS (+ appli compagnon iOS/Android) | Non |
| Tobii Eye Tracker 5 + Contrôle oculaire Windows | Regard | Barre Tobii (~285–500 $ chez les revendeurs) | Logiciel Windows gratuit, matériel payant | Windows | Non |
| Accès vocal Windows 11 (Voice Access) | Voix | Micro | Gratuit (intégré) | Windows 11 ; anglais, français, allemand, espagnol, italien | Non |
| Pointeur tête macOS (Head Pointer) + actions par expressions | Tête, expressions du visage | Caméra intégrée ou externe | Gratuit (intégré depuis macOS Catalina) | macOS | Non |
| Camera Mouse (Boston College) | Tête (suivi d'un point du visage) | Webcam | Gratuit | Windows | Non |
| Enable Viacam (eViacam) | Tête | Webcam | Gratuit | Windows, Linux | Oui (GPL v3) |
| Google Project Gameface | Tête + expressions du visage | Webcam | Gratuit | Windows (2023), Android (2024) | Oui |
| NPointer (Neurotechnology) | Mains | Webcam | Gratuit | Windows XP/Vista/7 (pages de 2012–2013) | Non |
| Projets GitHub « hand mouse » (MediaPipe) | Mains | Webcam | Gratuit (HandMouse Pro : à partir de 2,49 $) | Variable | Souvent oui |
| Ultraleap Leap Motion Controller 2 | Mains (capteur infrarouge) | Capteur dédié | ~139–219 $ | Windows 10+, macOS annoncé | Non |
| Origin HeadMouse Nano | Tête (pastille cible infrarouge) | Capteur dédié + pastilles | ~995–1 770 $ selon les revendeurs | Toutes (se comporte comme une souris USB) | Non |

### 2.2 Analyse détaillée

#### Talon Voice
- **Forces :** référence absolue pour coder et piloter un ordinateur à la voix ; très
  scriptable ; combine voix, bruits de bouche et oculométrie ; multiplateforme ; version
  de base gratuite ; communauté active.
- **Faiblesses :** courbe d'apprentissage importante (alphabet phonétique, commandes à
  mémoriser) ; inadapté aux environnements bruyants ou partagés (open space, cuisine,
  atelier) ; contrôle du pointeur fin nécessite un oculomètre Tobii ; meilleures
  fonctions réservées à la bêta payante.
- **Face à Gestura :** complémentaire plutôt que concurrent. Talon gagne pour la saisie
  de texte longue et les utilisateurs experts ; Gestura gagne pour le pointage direct,
  le silence, et la prise en main immédiate.

#### Cephable
- **Forces :** le concurrent le plus proche dans l'esprit (webcam seule, traitement
  local, contrôle par la tête et le visage, voix) ; profils, boutons virtuels, appli
  compagnon ; présent dans les programmes d'aménagement de poste et d'accessibilité
  au jeu vidéo.
- **Faiblesses :** centré sur la tête et le visage, pas sur les mains ; logiciel
  propriétaire ; fonctions avancées payantes (tarifs peu transparents : une source
  indique 300 $ pour une version professionnelle).
- **Face à Gestura :** Cephable est meilleur pour les personnes qui ne peuvent pas
  utiliser leurs mains ; Gestura propose un vocabulaire de gestes de la main plus riche
  (glisser-déposer, zoom à deux mains, défilement, volume, fenêtres) et un code ouvert.

#### Tobii Eye Tracker 5 + Contrôle oculaire Windows
- **Forces :** pointage le plus rapide et le moins fatigant pour les personnes
  paralysées ; intégré à Windows (souris, clavier, synthèse vocale à l'écran) ; produit
  mature.
- **Faiblesses :** matériel spécifique à acheter (environ 285–500 $) ; calibration
  sensible à la position et à l'éclairage ; précision limitée sur les petites cibles ;
  Windows uniquement pour le contrôle oculaire natif.
- **Face à Gestura :** clientèles différentes. Le regard sert les handicaps lourds ;
  Gestura vise ceux qui ont l'usage de leurs bras mais pas d'une souris à ce moment-là.

#### Outils natifs : Accès vocal Windows et Pointeur tête macOS
- **Forces :** gratuits, préinstallés, maintenus par Microsoft/Apple, en français pour
  l'Accès vocal Windows, sans installation ni risque de sécurité ; le Pointeur tête de
  macOS gère clic, clic droit et glisser-déposer par expressions du visage.
- **Faiblesses :** la voix est inutilisable dans le bruit ou en présence d'autres
  personnes et lente pour le pointage ; le Pointeur tête n'existe que sur Mac et
  repose sur des mouvements de tête soutenus, fatigants sur la durée ; aucun des deux
  n'utilise les gestes des mains.
- **Face à Gestura :** l'argument « c'est déjà intégré » est le principal obstacle à
  l'adoption. Gestura doit justifier l'installation par ce que le natif ne fait pas :
  les gestes des mains, le contrôle sans voix sous Windows, et les commandes rapides
  (volume, zoom, fenêtres) en un geste.

#### Souris à la tête gratuites : Camera Mouse, eViacam, Project Gameface
- **Forces :** gratuites, webcam seule ; eViacam et Gameface sont open source ;
  Gameface (Google) repose sur la même pile technique que Gestura (MediaPipe,
  PyAutoGUI) et prouve sa viabilité.
- **Faiblesses :** pointage uniquement par la tête ; clic par immobilité (Camera Mouse)
  ou par expressions faciales ; peu ou pas de gestes avancés (pas de clic droit natif
  pour Camera Mouse) ; Gameface est orienté jeu vidéo et peu promu côté bureautique.
- **Face à Gestura :** Gestura est plus complet pour les tâches de bureau, mais ces
  outils sont meilleurs pour les personnes sans usage des mains. Gestura n'a
  aujourd'hui **pas de pointeur à la tête** (sa tête sert seulement à la navigation),
  ce qui est un vrai manque pour ce public.

#### Contrôle par les mains : NPointer, projets GitHub, Ultraleap
- **NPointer :** l'idée de Gestura (webcam + gestes des mains) existait en 2012, mais
  le produit semble abandonné (pages datant de Windows XP/7).
- **Projets GitHub (MediaPipe) :** nombreux prototypes de « souris à la main », mais
  ce sont des démonstrations : pas d'interface, de calibration, de sécurité,
  d'installateur ni de maintenance.
- **Ultraleap :** suivi des mains de très haute qualité, mais capteur à acheter (139–
  219 $) et orienté réalité virtuelle et bornes interactives.
- **Face à Gestura :** c'est sur ce terrain que Gestura est le plus différenciant :
  un produit fini, installable, sans matériel, là où il n'existe que des prototypes ou
  du matériel dédié.

---

## 3. Forces et faiblesses de Gestura (état v0.3.0)

### Forces
1. **Vocabulaire de gestes de la main le plus riche** parmi les solutions webcam :
   curseur, clic, double-clic, clic droit, glisser-déposer, défilement, volume,
   multimédia, zoom à deux mains, ancrage des fenêtres, pause.
2. **Souris à deux mains** : une main déplace, l'autre clique — le curseur ne bouge pas
   au moment du clic, problème classique des souris gestuelles.
3. **Multimodal dans une seule application** : mains + tête (navigation) + clavier
   virtuel AZERTY/QWERTY qui ne vole pas le focus.
4. **Aucun matériel, aucun abonnement, aucun cloud** : tout le traitement est local,
   rien n'est enregistré.
5. **Sécurité intégrée** : mode test par défaut, arrêt d'urgence (bouton, raccourci
   global, coin de l'écran), confirmation des actions sensibles, relâchement garanti des
   boutons — rare dans les outils gratuits.
6. **Personnalisable** : chaque geste peut être réaffecté, chaque seuil réglé, avec un
   assistant de calibration.
7. **Francophone** : interface du clavier AZERTY, documentation en français.

### Faiblesses (à assumer ou corriger)
1. **Fatigue des bras** (« gorilla arm ») : garder la main levée devant la caméra est
   fatigant au-delà de quelques minutes. Gestura convient mal à une journée entière
   de travail.
2. **Inadapté aux handicaps sévères des membres supérieurs** : pas de pointeur à la tête,
   pas de clic par immobilité, pas de commande vocale.
3. **Windows uniquement** et application **non signée** (avertissement SmartScreen).
4. **Pas encore validé par des utilisateurs réels** à grande échelle ; seuils réglés en
   grande partie sur photos et simulations.
5. ~~Pas de licence open source définie~~ — **réglé** : Gestura est sous GPL v3
   (7 novembre 2026).
6. **Dépendance à l'éclairage et au cadrage** de la webcam, comme toutes les
   solutions à caméra.

---

## 4. Pourquoi un utilisateur choisirait Gestura

| Profil | Pourquoi Gestura plutôt qu'une autre option |
|---|---|
| **Mains occupées ou sales** (cuisine, atelier, garage, bricolage, peinture) | Pas de contact avec l'ordinateur ; plus rapide et plus discret que la voix ; aucun matériel |
| **Environnements stériles ou d'hygiène** (laboratoire, cabinet médical, salle de soins, consultation d'images) | Contrôle sans contact avec une simple webcam, là où les solutions sans contact passent souvent par du matériel dédié |
| **Écran à distance** (présentation, PC multimédia du salon, borne) | Volume, lecture/pause, défilement, zoom et navigation d'un geste, depuis le canapé ou l'estrade |
| **Douleurs liées à la souris** (TMS, tendinite, canal carpien) | Permet d'alterner avec la souris sans acheter de matériel ; gestes amples plutôt que micro-mouvements répétitifs |
| **Difficultés de motricité fine mais bras mobiles** | Gestes larges, seuils réglables, souris à deux mains, clavier virtuel — à valider avec des ergothérapeutes |
| **Environnement bruyant ou partagé** (open space, famille) | Alternative silencieuse aux commandes vocales |
| **Utilisateurs Windows attachés à la vie privée** | Traitement 100 % local, sans compte, sans cloud |

**Quand recommander autre chose (honnêteté du positionnement) :**
- Paralysie ou absence d'usage des membres supérieurs → Tobii + Contrôle oculaire,
  Cephable, Camera Mouse, eViacam, Pointeur tête macOS.
- Saisie de texte intensive ou programmation → Talon, Accès vocal Windows.
- Utilisateurs Mac → Pointeur tête natif ou Cephable, en attendant un portage.

---

## 5. Recommandations pour renforcer le positionnement

Par ordre d'impact estimé :

1. **Choisir une licence open source** (MIT ou GPL v3) et le dire clairement : c'est un
   différenciateur fort face à Cephable, Talon et Tobii, et une condition d'adoption par
   les associations et structures d'accessibilité.
2. **Ajouter un pointeur à la tête avec clic par immobilité** (le « mode tête seule »
   déjà envisagé) : Gestura deviendrait la seule solution webcam qui combine mains
   *et* tête comme pointeurs, et s'ouvrirait au public des handicaps moteurs.
3. **Réduire la fatigue** : position de repos détectée automatiquement, mode relatif
   (petits mouvements de main = grands déplacements), main posée sur le bureau.
4. **Signer l'application** et viser le Microsoft Store pour lever l'obstacle de
   l'installation face aux outils natifs.
5. **Profils par application** (lecteur multimédia, navigateur, présentation) pour
   capitaliser sur les usages « à distance » où Gestura est le plus convaincant.
6. **Tests utilisateurs** avec des ergothérapeutes et dans les cas d'usage cibles
   (cuisine, atelier, présentation) ; publier les résultats.
7. **Interopérer plutôt que concurrencer la voix** : documenter l'usage conjoint
   Gestura + Accès vocal Windows (gestes pour pointer, voix pour dicter).
8. **Portage macOS** à moyen terme (PySide6, MediaPipe et PyAutoGUI sont
   multiplateformes ; l'injection d'entrée et le focus du clavier sont à adapter).

---

## 6. Sources

- Talon : [documentation](https://talonvoice.com/docs/), [wiki communautaire — bêta](https://www.github.com/Samikay/talonwiki/blob/main/beta_talon.md), [LumeVoice — alternatives](https://lumevoice.com/blog/talon-voice-alternatives/), [LumeVoice (es) — Talon+ et Patreon](https://lumevoice.com/es/blog/alternativas-a-talon-voice/), [IEEE Spectrum](https://spectrum.ieee.org/amp/programming-by-voice-may-be-the-next-frontier-in-software-development-2652903656)
- Cephable : [contrôles par caméra](https://cephable.com/key-features/camera-based-controls/), [formules](https://cephable.com/plans/), [Neil Squire](https://www.neilsquire.ca/cephable-an-accessible-control-app/), [Closing the Gap](https://closingthegap.com/?p=117758), [AbleGamers](https://ablegamers.org/?p=13130)
- Tobii / Contrôle oculaire : [ShopSavvy — Tobii Eye Tracker 5](https://shopsavvy.com/products/tobii-eye-tracker-5), [eWeek](https://www.eweek.com/de/pc-hardware/microsoft-eye-control-makes-accessibility-widely-available-to-disabled/), [Microsoft — accessibilité Windows](https://www.microsoft.com/en-us/windows/accessibility-features?r=1), [guide Windows 11 24H2](https://laptops251.com/how-to-set-up-use-eye-tracker-in-windows-11-24h2-like-a-pro)
- Accès vocal Windows : [FAQ Microsoft](https://support.microsoft.com/en-us/accessibility/windows/voice-access/voice-access-frequently-asked-questions-faqs), [configuration](https://support.microsoft.com/en-us/accessibility/windows/voice-access/set-up-voice-access), [nouveautés](https://support.microsoft.com/topic/57a5e801-f741-40d2-a508-d84821ee0f53), [mise à jour de février 2024](https://support.microsoft.com/topic/aa44c0db-02a3-4161-bf06-e3c03a5f162e)
- macOS : [How-To Geek](https://www.howtogeek.com/788217/how-to-use-your-head-and-face-to-control-your-mac/), [thoughtbot](https://thoughtbot.com/blog/an-introduction-to-macos-head-pointer), [AbilityNet — macOS 14](https://mcmw.abilitynet.org.uk/how-to-control-your-computer-with-head-movement-in-macos-14-sonoma), [Apple Support](https://support.apple.com/en-lk/guide/mac-help/mchl654a7cc7/14.0/mac)
- Camera Mouse : [Betanews](https://betanews.com/article/control-your-pc-with-a-webcam-via-camera-mouse-2015), [SEN Teacher](https://senteacher.org/app/windows/11/Free-Camera-Mouse-Disabilities.html)
- eViacam : [site officiel](https://eviacam.sourceforge.net), [SourceForge](https://sourceforge.net/projects/eviacam/), [Linux Master Club](https://linuxmasterclub.com/eviacam)
- Project Gameface : [GitHub](https://github.com/google/project-gameface), [Google Developers Blog (2023)](https://developers.googleblog.com/en/project-gameface-makes-gaming-accessible-to-everyone/), [lancement Android (2024)](https://developers.googleblog.com/en/project-gameface-launches-on-android/), [Engadget](https://www.engadget.com/googles-project-gameface-hands-free-mouse-launches-on-android-123029158.html?src=rss)
- Contrôle par les mains : [NPointer — PR Newswire](https://prnewswire.com/news-releases/npointer-from-neurotechnology-uses-hand-gestures-to-control-and-navigate-computer-programs-without-a-mouse-or-touchpad-166732076.html), [MakeUseOf](https://www.makeuseof.com/tag/npointer-control-mouse-with-hand-gestures/), [hamoco (PyPI)](https://pypi.python.org/pypi/hamoco), [HandMouse Pro](https://eclipse-dev256.itch.io/handmousepro)
- Ultraleap : [page produit](https://www.Ultraleap.Com/product/leap-2/), [Notebookcheck](https://www.notebookcheck.com/Leap-Motion-2-steuert-PC-und-VR-per-Hand-Tracking-ist-30-kleiner-und-verspricht-breiteren-Software-Support.722746.0.html)
- HeadMouse Nano : [Origin Instruments](https://orin.com/access/headmouse/), [Bridges Canada](https://www.bridges-canada.com/products/headmouse-nano), [Closing the Gap](https://www.closingthegap.com/featured-product-origin-instruments/)
