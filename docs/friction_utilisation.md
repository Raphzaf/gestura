# Analyse des frictions d'utilisation de Gestura

*Rédigé le 7 novembre 2026 pour Gestura v0.3.0. La partie matérielle repose sur
des **mesures** faites avec le vrai moteur de Gestura (modèles MediaPipe, mode vidéo)
sur des photos dégradées artificiellement ; leurs limites sont décrites en 1.5.
La partie fatigue s'appuie sur la recherche publiée et sur l'inventaire des gestes de
Gestura. Aucun test avec de vrais utilisateurs n'a encore été mené : le protocole de
la partie 3 sert précisément à le faire.*

---

## Résumé

| Friction | Gravité | Ce qu'il faut retenir |
|---|---|---|
| Faible luminosité | **Bloquante** | À 50 % de la lumière normale, la main n'est plus détectée que 6 fois sur 10 et le curseur tremble 3 fois plus. En dessous de 20 %, Gestura devient inutilisable. |
| Distance à la caméra | **Bloquante pour certains usages** | Fiable jusqu'à environ 0,6 m, dégradé vers 1 m, inutilisable au-delà d'environ 1,5 à 2 m. Les usages « salon » et « présentation » sont compromis en l'état. |
| Qualité de la webcam | Faible | Une webcam bas de gamme (320 px, forte compression) suffit. La lumière compte bien plus que la caméra. |
| Puissance processeur | Moyenne | Environ ¾ de cœur de processeur en continu quand une main est suivie, 1 cœur avec la tête. Impact sur la batterie et le ventilateur des portables. |
| Fatigue des bras | **Élevée** | Les webcams intégrées obligent à lever les mains à hauteur du visage : c'est la posture la plus fatigante. Gestura convient à des sessions courtes, pas à une journée de travail. |
| Apprentissage | Moyenne | 16 gestes au total. Trois suffisent pour démarrer ; les autres (glisser, zoom, fenêtres) demandent un apprentissage progressif. |
| Saisie de texte | Élevée | Le clavier virtuel est une solution d'appoint : quelques mots par minute, contre 40 au clavier. |

---

## 1. Contraintes techniques matérielles

### 1.1 Méthode de mesure

Huit mains, extraites de sept photos réelles, ont été passées dans le moteur de Gestura
avec différentes dégradations. Chaque condition est jouée sur 20 images successives,
avec un bruit différent à chaque image, comme le ferait une webcam. On mesure :

- **Taux de détection** : part des images où la main est trouvée.
- **Erreur des points de repère** : écart moyen avec l'image propre, en % de la taille
  de la main.
- **Tremblement du bout de l'index** : déplacement moyen du point qui pilote le
  curseur, en pixels d'une image de 640 px de large. Avec les réglages par défaut, il
  est amplifié environ 4,7 fois à l'écran (zone active de 64 % du champ, écran de
  1 920 px), avant le lissage.
- **Concordance des postures** : part des images où la posture reconnue (pointer, deux
  doigts, poing…) est la même que sur l'image propre.

### 1.2 Faible luminosité — la principale cause d'échec

Deux cas sont simulés : la webcam compense l'obscurité en amplifiant le signal
(« gain automatique », cas le plus courant, qui amplifie aussi le bruit), ou l'image
reste sombre.

| Lumière | Gain automatique | Détection | Erreur des repères | Tremblement index | Postures identiques |
|---|---|---|---|---|---|
| 100 % (référence) | — | **100 %** | 0,6 % | 0,95 px | 89 % |
| 50 % | oui | **62 %** | 2,8 % | 3,1 px | 90 % |
| 20 % | oui | **15 %** | 20,4 % | 13,5 px | 75 % |
| 10 % | oui | **11 %** | 15,1 % | 11,5 px | 77 % |
| 5 % | oui | **0 %** | — | — | — |
| 20 % | non (image sombre) | **39 %** | 2,8 % | 0,9 px | 44 % |
| 10 % | non (image sombre) | **25 %** | 5,4 % | 35 px | 65 % |

*La concordance de référence n'est pas de 100 % : certaines mains des photos sont dans
des postures intermédiaires, à la limite entre deux catégories.*

**Ce que cela signifie :**
- Une pièce éclairée seulement par l'écran, ou un contre-jour (fenêtre derrière
  l'utilisateur), suffit à faire chuter la détection. L'utilisateur vit alors un curseur
  qui saute, des clics qui ne partent pas et des pauses intempestives : la cause la plus
  probable d'abandon.
- **Les webcams réduisent souvent leur cadence en faible lumière** (de 30 à 15 images
  par seconde) pour allonger l'exposition : le flou de mouvement augmente et le
  curseur répond plus lentement.
- Gestura affiche déjà la confiance de détection dans le Gesture Studio, mais
  **n'avertit pas** l'utilisateur d'un éclairage insuffisant. C'est l'amélioration la plus
  rentable : mesurer la luminosité de l'image et afficher « Éclairage insuffisant :
  allumez une lampe face à vous ».

### 1.3 Qualité de la webcam et flou

| Condition | Détection | Erreur des repères | Tremblement index | Postures identiques |
|---|---|---|---|---|
| Webcam 320 px, compression JPEG forte (qualité 40) | **100 %** | 1,9 % | 0,6 px | 85 % |
| Webcam 160 px, compression très forte (qualité 25) | **88 %** | 5,2 % | 1,6 px | 71 % |
| Flou léger (mise au point imparfaite) | **100 %** | 3,3 % | 0,5 px | 91 % |
| Flou fort (mouvement rapide, mise au point ratée) | **100 %** | 3,8 % | 4,5 px | 66 % |

**Ce que cela signifie :** une webcam d'entrée de gamme en 640 × 480 suffit. Acheter une
meilleure caméra n'améliore presque rien si l'éclairage est mauvais. Le flou fort
(mouvements très rapides) dégrade surtout la reconnaissance des postures : un geste
rapide peut être mal interprété. C'est une des raisons pour lesquelles Gestura exige
que chaque posture soit stable sur plusieurs images.

### 1.4 Distance entre la main et la caméra

On réduit la taille du sujet dans l'image pour simuler l'éloignement.

| Taille de la main dans l'image (640 px) | Distance estimée* | Détection |
|---|---|---|
| ~265 px | ~0,3 m | **100 %** |
| ~143 px | ~0,6 m | **88 %** |
| ~102 px | ~0,85 m | **75 %** |
| ~87 px | ~1 m | **63 %** |
| ~69 px | ~1,2 m | **38 %** |
| ~45 px | ~1,9 m | **0 %** |

\* *Estimation pour une webcam de champ horizontal d'environ 75° et une main d'environ
20 cm. La distance réelle dépend de la caméra.*

**Ce que cela signifie :**
- Assis devant un bureau (50–70 cm), Gestura fonctionne.
- **À plus d'un mètre, la détection devient aléatoire ; à 2 m, elle échoue.** Les usages
  « PC du salon » et « présentation sur estrade », mis en avant dans l'analyse de
  positionnement, **ne sont pas réalistes avec la configuration actuelle**.
- Augmenter la résolution de la caméra aide peu : le détecteur de paume de MediaPipe
  analyse une version réduite de l'image entière. Les solutions possibles sont un
  recadrage numérique autour de la dernière position de la main, ou un modèle conçu
  pour la longue portée — à tester avant de promettre ces usages.

### 1.5 Puissance processeur en arrière-plan

Mesures sur un processeur de serveur Intel Xeon à 2,1 GHz (4 cœurs logiques), moyenne
sur 150 images :

| Situation | Temps de calcul par image | Charge à 30 images/s | Charge à 15 images/s |
|---|---|---|---|
| Main suivie, mains seules | 24 ms | **0,73 cœur** | 0,37 cœur |
| Main suivie, mains + tête | 29–35 ms | **0,9 à 1 cœur** | 0,5 cœur |
| Aucune main dans le champ | 14–16 ms | **0,4 à 0,5 cœur** | 0,2 cœur |

- La résolution de la caméra (640 × 480 ou 1 280 × 720) ne change presque rien.
- Grâce au calcul en parallèle, le délai reste d'environ 24 ms par image, donc compatible
  avec 30 images par seconde.
- Sur un portable à 4 cœurs, Gestura occupe **environ 18 à 26 % du processeur en
  continu** : le ventilateur peut s'entendre et l'autonomie baisse. Un ordinateur ancien
  à 2 cœurs risque de descendre sous 20 images par seconde, avec un curseur moins fluide.
- Gestura désactive déjà le suivi de la tête quand aucune fonction ne l'utilise.
  **Manque :** un mode économie (15 images par seconde, et détection ralentie quand
  aucune main n'est visible depuis quelques secondes).

### 1.6 Autres frictions techniques

| Friction | Effet sur l'utilisateur |
|---|---|
| **Caméra partagée** : pendant une visioconférence, beaucoup de webcams ne peuvent être utilisées que par une application à la fois | Gestura ne peut pas tourner pendant un appel Teams ou Zoom, selon la webcam et le pilote |
| **Voyant de la caméra allumé en permanence** | Inquiétude sur la vie privée, même si rien n'est enregistré |
| **Contre-jour, arrière-plan chargé, autres personnes dans le champ** | Fausses détections, main d'une autre personne suivie |
| **Gants** (cuisine, atelier, laboratoire : cœur de cible) | **Non évalué**, ni par Gestura ni par la fiche du modèle MediaPipe : à tester en priorité |
| **Couleur de peau** | La fiche du modèle MediaPipe rapporte des écarts de précision modérés entre carnations ; à vérifier en test |
| **Fenêtres en mode administrateur, écran de connexion** | Windows empêche Gestura de les contrôler |
| **Plusieurs écrans** | Le curseur ne couvre que l'écran principal |
| **Avertissement SmartScreen** à l'installation | Méfiance dès le premier contact (résolu par le Microsoft Store) |

### 1.7 Limites de ces mesures
- Huit mains seulement, sur des photos et non des vidéos : les chiffres donnent des
  tendances, pas des valeurs précises.
- Le bruit de faible lumière est simulé sans le débruitage qu'appliquent les vraies
  webcams : les chiffres de faible lumière sont probablement **pessimistes**.
- Le processeur de mesure n'est pas celui d'un portable grand public.
- À confirmer avec le protocole de la partie 3, en notant la luminosité réelle (en lux,
  mesurée avec une application de téléphone).

---

## 2. Courbe d'apprentissage et fatigue physique

### 2.1 Le facteur décisif : la posture imposée par la webcam

La recherche sur les interactions « en l'air » a nommé ce problème le **« bras de
gorille »** (*gorilla arm*) : garder le bras levé devant soi fatigue les épaules en
quelques minutes. La mesure de référence, l'**endurance consommée** (Hincapié-Ramos et
al., 2014), montre que la fatigue est la plus faible **bras plié, main à mi-hauteur**, et
qu'elle est bien corrélée à l'échelle d'effort perçu Borg CR10.

**Or la webcam intégrée d'un portable vise le visage.** Pour que la main soit dans le
champ, l'utilisateur doit la lever à hauteur de poitrine ou de visage : c'est la
posture la plus fatigante. Les leviers :
- placer une **webcam externe plus bas** ou inclinée vers le bureau ;
- **baisser la zone active** (réglage Cursor › Active region) pour que la main travaille
  plus bas dans l'image ;
- **poser le coude** sur le bureau ou un accoudoir ;
- utiliser le **poing (débrayage)** et laisser retomber la main entre deux actions :
  Gestura ne fait rien quand la main sort du champ.

### 2.2 Inventaire des gestes : naturels ou fatigants ?

| Geste Gestura | Naturel ? | Effort | Remarque |
|---|---|---|---|
| Pointer de l'index (curseur) | Oui, immédiat | **Élevé dans la durée** (bras levé) | Le geste le plus utilisé est aussi le plus fatigant |
| Pincement pouce-index (clic) | Oui | Faible (doigts) | Avec le clic au relâchement, il faut ouvrir les doigts pour cliquer |
| Pincement maintenu (glisser-déposer) | Moyen | Moyen | Il faut tenir le pincement et déplacer le bras en même temps |
| Pouce-majeur (clic droit) | Peu intuitif | Faible | Confusion fréquente prévisible avec le clic gauche |
| Deux doigts haut/bas (défilement) | Assez | Moyen à élevé | Mouvement répétitif de tout le bras pour les longues pages |
| Trois doigts haut/bas (volume) | Moyen | Moyen | Distinguer deux et trois doigts demande de l'attention |
| Balayages (paume ou trois doigts) | Oui | Moyen | Gestes amples et rapides : répétés, ils fatiguent l'épaule |
| Paume ouverte immobile (pause) | Oui | Faible | Bon geste de sécurité |
| Poing (débrayage) | Concept nouveau | Faible | À expliquer : « lever la souris » |
| Deux mains écartées (zoom) | Oui (vu sur téléphone) | **Très élevé** | Les deux bras levés : à réserver aux usages ponctuels |
| Souris à deux mains | Demande un temps d'adaptation | Élevé | Gagne en précision, mais deux bras levés au lieu d'un |
| Tourner la tête (pages) | Oui | Faible à moyen | Rotations répétées du cou ; le retour au neutre doit être appris |
| Hochement double (Entrée) | Moyen | Faible | La double confirmation surprend au début |
| Clavier virtuel (pointer + pincer chaque touche) | Oui | **Très élevé** | Voir 2.4 |

### 2.3 Courbe d'apprentissage

- **16 gestes au total** (12 de la main, 4 de la tête). C'est beaucoup à mémoriser :
  les utilisateurs retiendront d'abord ceux qu'ils pratiquent dans les deux premières
  minutes.
- **Trois gestes suffisent pour 80 % des usages** : pointer, pincer, deux doigts pour
  défiler. La première expérience devrait se limiter à eux et dévoiler les autres
  progressivement.
- Concepts nouveaux à expliquer : le **clic au relâchement** (pas à la fermeture des
  doigts), la **pause du pincement** avant le glisser, le **débrayage au poing**, le
  **retour au neutre** de la tête avant le geste suivant.
- Le **mode test** et le **Gesture Studio** (jauges, journal des gestes) sont de bons
  outils d'apprentissage ; l'assistant de calibration en 6 étapes prend environ deux
  minutes, ce qui est acceptable.
- Estimation (à mesurer) : 2 à 5 minutes pour maîtriser curseur et clic ; plusieurs
  sessions pour les gestes avancés.

### 2.4 La saisie de texte

Les études sur les claviers virtuels manipulés en l'air mesurent environ **8 à 16 mots
par minute**, dans des casques de réalité virtuelle où l'on tape directement du doigt
sur les touches. Avec Gestura, chaque touche demande de déplacer le curseur puis de
pincer : la vitesse sera probablement plus basse (hypothèse : **4 à 8 mots par
minute**, à mesurer), contre environ 40 au clavier physique. Le clavier virtuel convient
à une recherche ou un mot de passe, pas à la rédaction. L'association avec la dictée
vocale de Windows est la piste la plus réaliste pour le texte long.

### 2.5 Recommandations pour réduire la fatigue et l'apprentissage

1. **Alerte d'éclairage** et **indicateur de distance** (« rapprochez-vous ») en direct.
2. **Mode économie** (15 images par seconde, détection ralentie au repos).
3. **Mode relatif** : de petits mouvements de main déplacent beaucoup le curseur, ce qui
   permet de garder le bras bas et le coude posé.
4. **Découverte progressive** : 3 gestes au premier lancement, puis un geste de plus
   chaque fois que le précédent est maîtrisé.
5. **Rappel de pause** après quelques minutes d'utilisation continue.
6. **Guide de placement** de la caméra dans l'assistant de calibration (caméra plus
   basse, lampe face à soi).

---

## 3. Protocole de test utilisateur de 15 minutes

### 3.1 Objectif
Mesurer le **taux d'abandon dû à la frustration** et identifier les gestes et conditions
qui le provoquent, avant tout effort commercial.

### 3.2 Définitions
- **Abandon d'une tâche** : le participant dit vouloir arrêter (« j'abandonne »,
  « laisse tomber »), **ou** reprend la souris ou le clavier physique, **ou** cesse
  d'essayer pendant plus de 15 secondes.
- **Échec** (différent de l'abandon) : la limite de temps de la tâche est atteinte alors
  que le participant essaie encore.
- **Abandon de session** : le participant demande à arrêter le test avant la fin.
- **Erreur** : action non voulue (clic au mauvais endroit, pause déclenchée par erreur,
  glisser au lieu de cliquer).

### 3.3 Participants et conditions
- **8 à 12 participants par segment visé** (par exemple : personnes aux mains occupées,
  personnes souffrant de TMS, personnes à motricité fine réduite). Cinq participants
  révèlent l'essentiel des problèmes d'utilisabilité, mais ne suffisent pas pour estimer
  un taux : avec 10 participants, un taux d'abandon mesuré de 30 % a une marge
  d'incertitude d'environ ± 25 points. Les chiffres serviront d'alerte, pas de statistique
  publiable.
- **Matériel** : portable courant avec sa webcam intégrée (le cas le plus fréquent),
  Gestura en mode réel, journal des gestes visible pour l'observateur seulement.
- **Lumière** : mesurée en lux au début du test. Idéalement, la moitié des sessions
  dans une lumière ordinaire de bureau, l'autre moitié en lumière faible (soirée, lampe
  d'appoint), pour mesurer l'effet réel de l'éclairage.
- **Aucune aide de l'observateur** pendant les tâches, sauf en cas de blocage total
  (compté comme abandon).

### 3.4 Déroulé minute par minute

| Temps | Étape | Ce qu'on mesure |
|---|---|---|
| 0:00–1:30 | Accueil, consentement, Borg CR10 de départ (effort du bras, de 0 à 10), mesure de la lumière | Lux, Borg initial |
| 1:30–3:30 | Assistant de calibration, sans aide | Durée, étapes échouées, abandon éventuel |
| 3:30–4:30 | Démonstration de trois gestes (pointer, pincer, deux doigts) puis essai libre en mode test | Questions posées |
| 4:30–11:30 | **Six tâches**, 70 secondes maximum chacune, réalisées en ordre variable d'un participant à l'autre | Réussite, temps, erreurs, abandons, frustration de 1 à 5 après chaque tâche |
| 11:30–13:00 | **Endurance** : 90 secondes de navigation libre sur un site d'actualités, sans pause | Borg CR10 juste après, perte de suivi |
| 13:00–15:00 | Questionnaire et entretien | Utilisabilité, intention de réutiliser, causes de frustration |

### 3.5 Les six tâches

| N° | Tâche | Gestes sollicités | Réussite si… |
|---|---|---|---|
| T1 | Cliquer sur 5 cibles de taille décroissante sur une page | Pointer, pincer | 5 cibles cliquées |
| T2 | Faire défiler une longue page pour trouver un mot affiché en rouge, puis cliquer dessus | Deux doigts, pointer, pincer | Mot cliqué |
| T3 | Ouvrir un dossier par double-clic | Double pincement | Dossier ouvert |
| T4 | Glisser un fichier dans ce dossier | Pincement maintenu | Fichier déplacé |
| T5 | Taper « Bonjour 2026 » dans une barre de recherche avec le clavier virtuel | Clavier virtuel | Texte exact |
| T6 | Monter le volume puis coller la fenêtre à droite de l'écran | Trois doigts, balayage | Les deux effets obtenus |

### 3.6 Grille d'observation (une ligne par tâche)
Heure de début et de fin · réussite / échec / abandon · nombre d'erreurs · pertes de
suivi de la main · verbatims de frustration (« il ne voit pas ma main », « ça a cliqué
tout seul ») · reprise de la souris (oui/non) · frustration de 1 à 5.

### 3.7 Questionnaire final (2 minutes)
1. **UMUX-Lite** (2 affirmations notées de 1 à 7) : « Les fonctions de Gestura
   répondent à mes besoins » ; « Gestura est facile à utiliser ».
2. **Borg CR10** de fin (effort ressenti dans le bras et l'épaule).
3. « Utiliseriez-vous Gestura dans votre quotidien ? Pour quelle situation ? »
4. « Quel moment vous a le plus agacé ? »
5. « Quel geste avez-vous trouvé le plus naturel ? Le plus pénible ? »

### 3.8 Indicateurs et seuils de décision

| Indicateur | Calcul | Seuil d'alerte |
|---|---|---|
| **Taux d'abandon par tâche** | abandons ÷ participants | > 20 % sur T1, T2 ou T3 (gestes de base) |
| **Taux d'abandon global** | participants ayant abandonné au moins une tâche ÷ participants | > 40 % |
| **Abandon de session** | participants ayant arrêté avant la fin ÷ participants | > 10 % |
| Taux de réussite des tâches de base (T1–T3) | réussites ÷ tentatives | < 70 % |
| Erreurs par tâche | moyenne | > 2 |
| Fatigue | Borg CR10 après l'endurance | ≥ 5 (« fort ») chez plus d'un tiers des participants |
| Frustration moyenne | moyenne des notes de 1 à 5 | > 3 |
| Utilisabilité | UMUX-Lite ramené sur 100 | < 68 (sous la moyenne des logiciels) |
| Effet de l'éclairage | comparer abandons en lumière ordinaire et faible | Écart > 20 points |

**Lecture des résultats :**
- Si les seuils d'alerte sont dépassés sur les tâches de base, corriger d'abord
  l'éclairage, la distance et les seuils de pincement avant toute promotion.
- Si l'abandon se concentre sur T4–T6, ce sont les gestes avancés qu'il faut repenser
  ou cacher au départ.
- Si la fatigue domine, prioriser le mode relatif et le guide de placement de la caméra.

### 3.9 Préparation recommandée dans Gestura
- Ajouter un **export local du journal de session** (gestes, commandes, pertes de suivi,
  images par seconde, luminosité moyenne), sans aucune image, pour exploiter les tests
  sans chronométrage manuel.
- Préparer les pages et fichiers des tâches à l'identique pour tous les participants.

---

## Sources

- Fatigue des bras : [Consumed Endurance — Hincapié-Ramos et al. (CHI 2014)](https://hci.cs.umanitoba.ca/publications/details/consumed-endurance-a-metric-to-quantify-arm-fatigue-of-mid-air-interactions), [article (PDF)](https://www.lri.fr/~anab/teaching/evaluation/papers/consumed-endurance.pdf), [NICER (2024)](https://arxiv.org/html/2406.08875v1)
- Saisie en l'air : [Adhikary et Vertanen — clavier en l'air et parole](https://www.keithv.com/pub/speechmidair), [placement du clavier en réalité mixte (2024)](https://arxiv.org/pdf/2410.04177), [Hirai et al. (Asian CHI 2021)](https://www.iplab.cs.tsukuba.ac.jp/~ikeda/pdf/asian_chi2021_hirai.pdf)
- Questionnaires : [MeasuringU — du SUS à l'UMUX-Lite](https://measuringu.com/umux-lite/), [comparaison SUS, UMUX-Lite, UEQ-S](https://uxpajournal.org/?p=6228)
- Modèle de suivi des mains : [fiche du modèle MediaPipe Hands avec équité (2021)](https://dcmpx.remotevs.com/com/googleapis/storage/SL/mediapipe-assets/Model%20Card%20Hand%20Tracking%20%28Lite_Full%29%20with%20Fairness%20Oct%202021.pdf), [MediaPipe Hands (article)](https://ar5iv.labs.arxiv.org/html/2006.10214)
- Mesures de robustesse et de charge processeur : scripts du dépôt, [`scripts/friction/`](../scripts/friction/)
