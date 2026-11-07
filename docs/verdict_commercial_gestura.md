# Verdict commercial — Gestura

*Rapport final, 7 novembre 2026, établi à partir de trois documents :
[analyse de positionnement](analyse_positionnement.md),
[frictions d'utilisation](friction_utilisation.md) et
[stratégie économique](business_model_gestura.md). Il porte sur Gestura v0.3.0.*

---

## 1. La réponse courte

> **Faut-il commercialiser Gestura ?**
>
> **Pas aujourd'hui, et jamais auprès du grand public comme activité principale.**
>
> **Oui, d'ici 6 à 9 mois, auprès des employeurs, sur le canal Accessibilité / Handicap**,
> à condition que trois jalons de validation soient atteints (section 4).
>
> **En attendant — et si la validation échoue —** Gestura reste un projet open source
> qui **ne coûte rien** et peut même s'autofinancer modestement grâce au Microsoft Store
> (section 5).

| Canal | Verdict | En une phrase |
|---|---|---|
| **Accessibilité / Handicap** | ✅ **Prioritaire** | Le seul canal où le besoin est assez fort pour accepter les frictions, et où quelqu'un paie (l'employeur, aidé par l'Agefiph). |
| Développeurs / Productivité | ❌ Non | Gestura y est plus lent et plus fatigant que le clavier et la souris, face à Talon et à la dictée gratuite de Windows. |
| Gaming | ❌ Non | Trop de latence pour le jeu, entrées simulées souvent ignorées par les jeux, et une niche accessible déjà servie gratuitement (Project Gameface). |

---

## 2. Pourquoi ne pas vendre maintenant

Trois constats, issus des analyses, empêchent une commercialisation immédiate :

1. **Le produit n'a pas encore été testé par de vrais utilisateurs.** Les seuils de
   reconnaissance ont été réglés sur photos et simulations. Votre propre usage est
   encourageant, mais un seul utilisateur n'est pas une preuve.
2. **Deux frictions mesurées touchent le cœur de l'expérience :**
   - **La lumière** : à 50 % de la lumière normale, la main n'est détectée que 6 fois sur
     10 ; à 20 %, 15 % du temps. Une pièce le soir ou un contre-jour suffit à rendre
     Gestura frustrant, et rien n'avertit encore l'utilisateur.
   - **La fatigue** : la webcam d'un portable oblige à lever la main à hauteur du visage,
     la posture la plus fatigante identifiée par la recherche (« bras de gorille »).
3. **Deux promesses du positionnement ne tiennent pas en l'état :**
   - **Le contrôle à distance** (salon, présentation) : la détection tombe à 63 % vers
     1 m et à 0 % vers 2 m.
   - **Le public des handicaps moteurs lourds** : sans pointeur à la tête ni clic par
     immobilité, Gestura ne sert que les personnes qui peuvent bouger les bras.

À cela s'ajoutent des prérequis non techniques : pas de licence définie, pas de
structure pour facturer, application non signée.

**Vendre maintenant, ce serait vendre une promesse à des clients exigeants**
(entreprises, personnes en situation de handicap) **avant d'avoir mesuré si le produit
la tient.** Le risque n'est pas seulement de perdre des ventes, mais d'abîmer la
réputation du projet auprès des prescripteurs, qui sont peu nombreux et se parlent.

---

## 3. Choix du canal d'acquisition

### 3.1 Grille de comparaison

Notes de 1 (défavorable) à 5 (favorable), justifiées par les trois analyses.

| Critère | Développeurs / Productivité | **Accessibilité / Handicap** | Gaming |
|---|---|---|---|
| **Force du besoin** (sans Gestura, l'utilisateur est-il bloqué ?) | 1 — souris et clavier suffisent | **5** — souris inutilisable ou douloureuse | 2 — sauf joueurs handicapés |
| **Tolérance aux frictions** (lumière, fatigue, apprentissage) | 1 — abandon au premier raté | **4** — l'alternative est souvent pire | 1 — exigence de précision maximale |
| **Capacité et volonté de payer** | 2 — outils gratuits partout | **4** — employeur + aide Agefiph, prix de marché de plusieurs centaines d'euros par poste | 2 — attente de gratuité |
| **Concurrence gratuite** | 1 — Talon, Accès vocal Windows | 3 — outils gratuits pour la tête et la voix, mais pas pour les mains | 1 — Project Gameface (Google, gratuit) |
| **Adéquation du produit actuel** | 2 — saisie de texte lente | 3 — bonne pour les personnes qui bougent les bras, insuffisante pour les autres | 1 — latence, compatibilité des jeux |
| **Accès au client** | 3 — en ligne, mais public volatil | 3 — via des prescripteurs (ergonomes, missions handicap), cycles longs | 3 — en ligne (vidéos, communautés) |
| **Total sur 30** | **10** | **22** | **10** |

### 3.2 Pourquoi pas les développeurs et la productivité
- Pour quelqu'un qui peut utiliser une souris, Gestura est **plus lent et plus
  fatigant** : rien ne justifie de supporter les frictions.
- Les développeurs qui ne peuvent plus taper utilisent **Talon** (voix, scripts,
  oculométrie), bien plus efficace pour le code. Le clavier virtuel de Gestura
  (probablement quelques mots par minute) ne rivalise pas.
- Le segment « mains occupées » (cuisine, atelier) est réel mais **peu disposé à
  payer** pour un usage ponctuel. Il fera un bon public pour la **version gratuite**,
  pas un marché.

### 3.3 Pourquoi pas le gaming
- **Latence** : traitement d'environ 24 ms, plus l'acquisition de la caméra et le
  lissage du curseur, soit vraisemblablement **60 à 100 ms** au total (estimation), contre
  quelques millisecondes pour une souris de jeu.
- **Compatibilité** : beaucoup de jeux (entrées brutes, anti-triche) **ignorent les
  entrées simulées** ; Project Gameface a dû recourir à une bibliothèque dédiée aux jeux.
- **Fatigue** : sessions longues incompatibles avec un bras levé.
- **Concurrence** : le jeu accessible est déjà servi gratuitement par Project Gameface
  et soutenu par des associations qui privilégient les solutions gratuites.

### 3.4 Pourquoi l'accessibilité, et par quel sous-segment commencer
- **La demande est portée par la loi** (obligation d'emploi de 6 % pour environ 108 000
  entreprises) et **financée** (l'Agefiph finance les « logiciels spécifiques »
  d'aménagement de poste).
- **Les TMS représentent plus de 80 % des maladies professionnelles** reconnues en
  France.
- **Le traitement 100 % local** répond aux exigences des DSI et des délégués à la
  protection des données.

**Attention à ne pas viser tous les TMS.** Pointer en l'air sollicite l'épaule : Gestura
pourrait **aggraver** une pathologie de l'épaule. Le premier segment doit être, **sur
prescription d'un ergonome ou d'un ergothérapeute** :
1. les **TMS de la main et du poignet** (canal carpien, tendinites du poignet), quand la
   souris est douloureuse mais l'épaule saine ;
2. les **difficultés de motricité fine** (préhension difficile) avec des bras mobiles.

Le public des handicaps moteurs plus lourds ne viendra qu'**après** l'ajout du pointeur
à la tête et du clic par immobilité.

---

## 4. Conditions pour passer à la vente (« go / no-go »)

Ces jalons s'enchaînent sur 6 à 9 mois. **Tant qu'ils ne sont pas atteints, on ne vend
pas.**

| Jalon | Critère de réussite | Échéance |
|---|---|---|
| **1. Corriger les frictions bloquantes** | Alerte d'éclairage, indicateur de distance, mode économie, mode relatif (bras bas, coude posé) ; installateur MSI déployable en entreprise | Mois 3 |
| **2. Test utilisateur (protocole de 15 minutes)** avec 10 à 12 personnes du segment cible, en conditions réelles | Abandon ≤ 20 % sur les gestes de base ; abandon global ≤ 40 % ; effort du bras (Borg) < 5 chez au moins deux tiers des participants ; facilité d'utilisation (UMUX-Lite) ≥ 68/100 | Mois 4–5 |
| **3. Pilotes payants** avec des employeurs, via des ergonomes ou ergothérapeutes, financés si possible par l'Agefiph | Au moins 2 pilotes sur 3 transformés en licences | Mois 6–9 |
| Prérequis administratifs (en parallèle) | Licence GPL v3, structure juridique, assurance RC professionnelle, application signée | Avant le jalon 3 |

- **Si les trois jalons sont atteints : GO.** Lancer l'offre B2B décrite dans la
  stratégie économique (290 € HT par poste et par an, 350 € d'installation et de
  calibration), en visant un revendeur d'aides techniques comme relais. Prévision
  centrale : environ **10 k€ la première année, 38 k€ la deuxième, 90 k€ la troisième**
  sur ce seul canal.
- **Si le test utilisateur échoue (jalon 2) :** corriger et refaire **une** fois. En cas
  de second échec, **NO-GO** : on passe au plan de la section 5 sans regret, l'essentiel
  du travail restant utile à la communauté.
- **Si les pilotes ne se transforment pas (jalon 3) :** le besoin existe peut-être, mais
  pas la disposition à payer. **NO-GO** commercial, plan de la section 5.

**Coût de cette validation :** quelques centaines d'euros (assurance, signature,
déplacements) et surtout du temps. C'est un pari peu coûteux pour savoir si un vrai
marché existe.

---

## 5. Le plan open source durable — sans perdre d'argent

C'est le **socle par défaut**, appliqué dès maintenant, que la commercialisation B2B
se fasse ou non.

### 5.1 Ramener les coûts à zéro

| Poste | Solution gratuite |
|---|---|
| Hébergement du code et des versions | GitHub et ses pages de versions (gratuits) |
| Construction et tests automatiques | GitHub Actions : déjà en place ; **gratuit et illimité si le dépôt devient public** (quota limité tant qu'il est privé) |
| Signature de l'application | Distribution par le **Microsoft Store**, qui signe l'application ; inscription gratuite pour les particuliers. Des programmes gratuits de signature pour l'open source existent aussi (à vérifier) |
| Documentation | Déjà dans le dépôt ; publiable gratuitement en site web |
| Mises à jour de dépendances | Outils automatiques gratuits sur GitHub (alertes et propositions de mise à jour) |
| Support | Tickets GitHub et FAQ, pas de support individuel promis |

**Coût résiduel : 0 à 150 € par an.**

### 5.2 Couvrir ces coûts sans faire payer l'accessibilité
1. **Version payante sur le Microsoft Store (9,99 à 12,99 €)**, identique à la version
   gratuite de GitHub : on paie pour l'installation en un clic, la signature et les
   mises à jour automatiques. C'est le modèle de Krita, autorisé par Microsoft pour
   l'auteur du logiciel. Prévision prudente : **1 à 4 k€ par an**, assez pour couvrir
   les coûts.
2. **Dons** : GitHub Sponsors ou Open Collective, mis en avant dans l'application.
3. **Subventions** : programmes européens de financement de l'open source (le programme
   NGI Zero géré par NLnet en est un exemple, à vérifier), fondations et appels à projets
   sur le handicap.
4. **Partenariats de recherche** : laboratoires d'interaction humain-machine et écoles
   d'ergothérapie, qui peuvent mener les tests utilisateurs et contribuer au code.

### 5.3 Rester utile sans s'épuiser
- **Rendre le dépôt public** sous **GPL v3**, avec un accord de contribution léger :
  cela garde la porte du B2B ouverte.
- **Budget temps plafonné** (par exemple 4 heures par semaine) : corrections, mises à
  jour de sécurité, une version mineure par trimestre.
- **Périmètre resserré** : Windows uniquement ; pas de portage macOS sans contributeur
  volontaire.
- **Faciliter les contributions** : tickets « bon premier ticket », guide de
  développement (déjà présent), tests automatiques (déjà plus de 130).
- **Diffuser par les relais de l'accessibilité** (associations, ergothérapeutes,
  fablabs) plutôt que par la publicité.

---

## 6. Feuille de route recommandée

| Période | Action | Plan |
|---|---|---|
| **Maintenant** | Licence GPL v3, dépôt public, publication sur le Microsoft Store, page de dons | Socle open source |
| Mois 1–3 | Alerte d'éclairage, indicateur de distance, mode économie, mode relatif, installateur MSI | Les deux |
| Mois 4–5 | Test utilisateur de 15 minutes avec 10–12 personnes (TMS main/poignet, motricité fine) | **Décision n° 1** |
| Mois 5–9 | Si positif : 3 pilotes avec ergonomes et employeurs, dossier Agefiph type | **Décision n° 2** |
| Mois 9+ | GO : offre B2B, revendeur ; pointeur à la tête pour élargir le public. NO-GO : maintenance légère et subventions | Selon décision |

---

## 7. Conclusion

Gestura est techniquement abouti et répond à un vrai manque : **personne ne propose
aujourd'hui un contrôle complet de l'ordinateur par les gestes des mains avec une
simple webcam.** Mais un manque n'est pas un marché.

- Pour le **grand public, les développeurs et les joueurs**, les frictions mesurées
  (lumière, fatigue, distance, latence) sont trop fortes au regard d'un besoin trop
  faible : ce ne sont pas des marchés.
- Pour l'**accessibilité**, le besoin est assez fort et le financement existe. C'est le
  seul canal qui mérite un essai commercial, **ciblé, prudent et conditionné à des
  preuves.**
- Dans tous les cas, Gestura peut **rester un projet open source utile qui ne coûte
  rien**, et dont la version du Microsoft Store couvre les frais.

**Décision recommandée : open source dès maintenant, validation de l'accessibilité
B2B en 6 à 9 mois, et la vente seulement si les utilisateurs et les pilotes le
confirment.**
