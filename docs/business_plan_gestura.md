# Business plan et modèle de monétisation — Gestura

*Document établi le 7 novembre 2026 pour Gestura v0.3.0. Il applique les conclusions du
[verdict commercial](verdict_commercial_gestura.md) : **B2B Accessibilité / Handicap
en priorité**, et **socle open source** autofinancé par le Microsoft Store. Les chiffres
de prix et de volumes viennent de la [stratégie économique](business_model_gestura.md) ;
les frictions mesurées viennent de l'[analyse de friction](friction_utilisation.md).*

*Les **faits** (réglementation, aides, statistiques) sont sourcés en section 9. Les
**prévisions** reposent sur des hypothèses écrites noir sur blanc : ce sont des ordres
de grandeur pour décider, pas des promesses.*

---

## 0. Résumé et condition préalable

| | |
|---|---|
| **Offre payante** | Édition Entreprise pour l'aménagement de poste : **290 € HT / poste / an** + **350 € HT / poste** d'installation, calibration et formation (obligatoire la 1ʳᵉ année) |
| **Offre gratuite / soutien** | GitHub : **0 €** · Microsoft Store : **9,99 à 12,99 € TTC**, même logiciel, payé pour le confort (installation en 1 clic, mises à jour automatiques) |
| **Qui paie** | L'employeur, avec l'aide de l'**Agefiph** (privé) ou du **FIPHFP** (public) quand le salarié est bénéficiaire de l'obligation d'emploi (RQTH…), ou le **budget de l'accord handicap** de l'entreprise |
| **Cible** | Entreprises de plus de 100 salariés ; salariés souffrant de **TMS de la main et du poignet** ou de **troubles de la motricité fine**, avec des bras mobiles et des épaules saines |
| **Chiffre d'affaires B2B** | **≈ 10 k€** (année 1, 15 postes) · **≈ 39 k€** (année 2, 70 postes) · **≈ 88 à 91 k€** (année 3, 180 postes) |
| **Point clé** | Rentable sur ses frais dès l'année 1 ; un salaire de fondateur n'est finançable qu'en année 3 |

> **Ce plan ne démarre qu'après le « GO » du verdict.** Les trois jalons restent
> obligatoires : corriger les frictions bloquantes (alerte d'éclairage, mode « bras
> bas », installateur MSI), réussir le test utilisateur de 15 minutes sur 10 à
> 12 personnes, puis transformer au moins 2 pilotes sur 3. Durée : 6 à 9 mois.
> **« Année 1 » désigne ici les 12 premiers mois après ce GO.** En cas de NO-GO, seul
> le volet open source (section 2.2) s'applique.

---

## 1. Proposition de valeur et segmentation

### 1.1 Qui est exclu de l'offre payante, et pourquoi

Le verdict a noté chaque canal sur 30 points. Seule l'accessibilité passe (22/30).

| Public | Note | Pourquoi il est exclu de l'offre payante | Ce qu'il reçoit |
|---|---|---|---|
| **Grand public** | — | Besoin faible : la souris suffit. Les frictions mesurées (lumière, fatigue du bras, distance) font abandonner au premier raté. Les clients à 13 € sont exigeants et coûteux en support. | La version **gratuite** de GitHub ou la version **Store** de soutien |
| **Développeurs / productivité** | 10/30 | Gestura est plus lent et plus fatigant que le clavier et la souris. Ceux qui ne peuvent plus taper utilisent Talon (voix) ou l'Accès vocal de Windows, gratuit. | Version gratuite |
| **Gaming** | 10/30 | Latence estimée à 60–100 ms, entrées simulées ignorées par beaucoup de jeux, et une niche accessible déjà servie gratuitement par Project Gameface (Google). | Version gratuite |

**Principe éthique :** une personne handicapée qui équipe son propre ordinateur ne paie
jamais pour une fonction d'accessibilité. Ce qui est vendu à l'entreprise, c'est le
**déploiement, l'accompagnement et la garantie de service**, pas le droit d'utiliser le
logiciel.

### 1.2 Proposition de valeur

> **Gestura remplace la souris par des gestes de la main devant une simple webcam, sur
> un poste Windows existant, sans aucune donnée qui quitte l'ordinateur. L'aménagement
> de poste est installé, calibré et suivi, et peut être financé par l'Agefiph ou le
> FIPHFP.**

| Pour qui | Ce qu'il gagne |
|---|---|
| **Le salarié** | Il continue à travailler sans saisir la souris, cause de douleur ; installation calibrée sur son poste et formation |
| **Le référent / la mission handicap** | Un aménagement rapide (webcam standard, pas de matériel spécial), un dossier de financement prêt à déposer, un salarié maintenu dans l'emploi |
| **L'ergonome, le médecin du travail** | Une alternative de plus à la souris ergonomique, qui supprime la préhension ; paramétrage adapté à la personne (sensibilité, gestes, mode bras bas) |
| **La DSI** | Traitement 100 % local, aucune connexion réseau, aucune image enregistrée, code source ouvert et auditable, installateur signé déployable à distance |

### 1.3 Profil du client idéal (B2B)

| Critère | Client idéal | Pourquoi |
|---|---|---|
| **Taille** | **Plus de 100 salariés**, en priorité **250 et plus** | L'obligation d'emploi de 6 % s'applique dès 20 salariés. Mais à partir de 250 salariés, un **référent handicap** est obligatoire : il y a un interlocuteur identifié et un budget. De 100 à 249 salariés, on passe par les RH et le service de santé au travail. |
| **Situation au regard des 6 %** | Taux inférieur à 6 % (contribution payée chaque année) **ou** accord handicap agréé (budget à dépenser) | Dans les deux cas, l'entreprise a une raison financière de maintenir ses salariés handicapés dans l'emploi (section 3) |
| **Activité** | Beaucoup de postes sur écran : sièges sociaux, banque et assurance, centres de relation client, administrations | Usage intensif de la souris, donc TMS du poignet fréquents ; postes Windows standardisés |
| **DSI** | Exigeante : pas de cloud, pas de collecte de données, logiciels signés, déploiement centralisé | Gestura est conçu pour ça : c'est un avantage face aux solutions en ligne |
| **Prescripteurs en place** | Ergonome (interne ou cabinet), médecin du travail, ergothérapeute, Cap emploi | Ce sont eux qui recommandent un aménagement ; l'avis du médecin du travail est exigé par l'Agefiph |

**Les quatre interlocuteurs d'une vente :**

1. **Mission handicap / référent handicap** (souvent le décideur et le porteur du dossier
   de financement) ;
2. **Médecin du travail et ergonome** (prescripteurs : sans leur avis, pas de vente) ;
3. **DSI / RSSI** (validation technique : sécurité, déploiement) ;
4. **Achats** (référencement du fournisseur), dans les grands groupes.

### 1.4 Pathologies cibles et contre-indications

| | Situations | Pourquoi Gestura convient |
|---|---|---|
| **Cible n° 1** | **TMS de la main et du poignet** : syndrome du canal carpien, tendinites du poignet et des doigts | La saisie de la souris et les clics répétés sollicitent précisément le poignet et les doigts. Avec Gestura, plus de préhension : on pointe et on pince en l'air. Les TMS représentent plus de 80 % des maladies professionnelles reconnues en France. |
| **Cible n° 2** | **Troubles de la motricité fine avec mobilité des bras conservée** : difficulté à saisir, à cliquer précisément ou à maintenir un bouton enfoncé | Les gestes sont amples, le curseur est lissé, la sensibilité et le clic se règlent ; le glisser-déposer ne demande pas de garder un bouton enfoncé |
| ⚠️ **À exclure** | **Pathologies de l'épaule** (tendinopathies de la coiffe des rotateurs), douleurs cervicales | Pointer en l'air sollicite l'épaule : Gestura pourrait **aggraver** ces troubles |
| ⚠️ **Pas encore** | Absence d'usage des membres supérieurs, tremblements importants | Il manque le pointeur à la tête et le clic par immobilité ; des tremblements perturbent la détection |

**Règle de vente :** Gestura n'est installé que **sur recommandation d'un ergonome, d'un
ergothérapeute ou du médecin du travail**, après vérification de l'absence de
contre-indication à l'épaule. C'est une protection pour l'utilisateur, et c'est aussi
la pièce exigée pour le financement Agefiph.

---

## 2. Stratégie de tarification

### 2.1 Offre B2B : Gestura Édition Entreprise

| Élément | Prix HT | Contenu |
|---|---|---|
| **Licence annuelle** | **290 € / poste / an** | Édition Entreprise : installateur MSI signé, déploiement silencieux (Intune, GPO), configuration verrouillable, mises à jour garanties, support par messagerie et visio (réponse sous 2 jours ouvrés), dossier sécurité et RGPD pour la DSI |
| **Pack installation, calibration, formation** | **350 € / poste**, **obligatoire la 1ʳᵉ année** | Installation à distance ; calibration sur le poste réel (éclairage, distance, placement de la webcam, mode bras bas, sensibilité) ; deux séances de formation de 45 min ; point de suivi à 30 jours ; compte rendu pour l'ergonome et le dossier de financement |
| **Coût 1ʳᵉ année** | **640 € / poste** | Licence + pack |
| **Coût années suivantes** | **290 € / poste / an** | Licence seule |
| **Coût sur 3 ans** | **1 220 € / poste** | Soit environ 34 € par mois |

**Pourquoi le pack est obligatoire la première année.** L'analyse de friction a montré
que l'expérience dépend du réglage : à 50 % de la lumière normale, la main n'est
détectée que 6 fois sur 10, et une webcam mal placée oblige à lever le bras (fatigue).
Un poste non calibré, c'est un utilisateur qui abandonne et une licence non renouvelée.
Le pack est aussi la partie la plus facile à justifier dans un dossier de financement :
c'est un service, pas un logiciel disponible gratuitement ailleurs.

**Attention à la licence GPL.** Le cœur de Gestura est sous GPL v3 : n'importe qui peut
le télécharger gratuitement. La « licence » vendue doit donc être présentée comme ce
qu'elle est : un **abonnement à l'Édition Entreprise et au service** (composants de
déploiement distincts, support, garanties). Un financeur pourrait refuser de payer
« un logiciel gratuit » : le devis doit détailler ce qui est spécifique.

**Option recommandée : licence de 3 ans prépayée** (870 € HT, plus le pack). Les aides
au poste sont en général accordées en une fois ; le financement des renouvellements
annuels n'est pas garanti. Une licence pluriannuelle intégrée au dossier initial
supprime ce risque pour le client. Les projections ci-dessous gardent la facturation
annuelle, plus prudente pour la trésorerie.

**Pilotes de l'année 1** : facturés au tarif normal (640 €), pour que le devis
présenté au financeur soit le même que celui de l'offre commerciale.

**Grille de volume** : à fixer après les pilotes. Pas de remise prévue dans le scénario
central.

### 2.2 Offre grand public / open source

| Version | Prix | Ce que l'utilisateur paie | Rôle |
|---|---|---|---|
| **GitHub** | **0 €** | Rien : code, installateur et documentation gratuits, sous GPL v3 | Éthique open source, vitrine technique, porte d'entrée des contributeurs et des prescripteurs (ergothérapeutes, écoles) |
| **Microsoft Store** | **9,99 à 12,99 € TTC** | Le confort : installation en un clic sans avertissement Windows, mises à jour automatiques, paquet signé par Microsoft | Couvrir les frais fixes |

**Le même logiciel, sans aucune fonction en plus.** C'est le modèle de Krita, autorisé
par Microsoft pour l'auteur du logiciel. Le paquet du Store est déjà prêt
(`store/build_store.py`).

**Revenu par vente** (commission Microsoft de 15 %, TVA à 20 %) :

| Prix TTC | Prix HT | Net après commission | Ventes pour 1 k€ | Ventes pour 4 k€ |
|---|---|---|---|---|
| 9,99 € | 8,33 € | **7,08 €** | 141 | 565 |
| 12,99 € | 10,83 € | **9,20 €** | 109 | 435 |

**Objectif : 1 à 4 k€ par an**, soit environ 110 à 570 ventes. Ce revenu couvre les
frais fixes du projet : outils et signature (0 à 150 € par an tant qu'il n'y a pas de
structure), puis une partie des frais de structure (comptabilité, assurance) une fois
le B2B lancé. **Ce n'est pas un modèle économique, c'est une ligne de financement des
frais fixes.**

**Recommandation : 12,99 €** au lancement (le précédent Krita montre que le public
accepte ce prix pour un logiciel gratuit ailleurs) ; 9,99 € en promotion ponctuelle.

---

## 3. Mécanismes de financement : comment l'employeur paie peu ou rien

### 3.1 Qui finance l'aménagement de poste

| Situation du salarié et de l'employeur | Qui finance | Ce qu'il faut |
|---|---|---|
| **Secteur privé**, salarié **bénéficiaire de l'obligation d'emploi** (RQTH, invalidité, accident du travail ou maladie professionnelle avec incapacité ≥ 10 %…) | **Agefiph** : aide à l'adaptation des situations de travail, qui couvre notamment les **logiciels spécifiques** | Devis ; **avis circonstancié du médecin du travail** sur la pertinence de l'aménagement ; demande avant l'achat |
| **Secteur privé, entreprise sous accord handicap agréé** | **Budget de l'accord** : l'entreprise y consacre l'équivalent de sa contribution, l'argent est déjà prévu | Accord interne ; accès éventuel aux aides Agefiph à vérifier au cas par cas |
| **Fonction publique** (État, collectivités, hôpitaux) | **FIPHFP** : aide à l'adaptation du poste de travail (catalogue des interventions 2026), ou convention de l'employeur avec le FIPHFP | Avis du médecin de prévention ; dossier sur la plateforme des aides |
| **Salarié souffrant de TMS sans reconnaissance** | **L'employeur seul** | L'employeur doit tout de même aménager le poste si le médecin du travail le préconise. Le médecin peut aussi orienter vers une demande de RQTH (auprès de la MDPH) |

**Ce que couvre l'aide Agefiph.** Elle finance le **surcoût lié à la compensation du
handicap**, c'est-à-dire la différence avec un équipement standard. Pour Gestura, il n'y
a pas d'équivalent standard (la souris est déjà sur le poste) : c'est la quasi-totalité
du coût qui relève de la compensation.

> ⚠️ **Correction par rapport à l'hypothèse de départ (« jusqu'à 100 % »).** Aucune
> source consultée ne confirme un taux de 100 % aujourd'hui. En 2024, l'Agefiph a
> **limité sa prise en charge à 90 % du surcoût**, présentée comme un ajustement
> budgétaire temporaire. Le montant est fixé **au cas par cas**. Le taux en vigueur doit
> être vérifié dans la fiche Agefiph de janvier 2026 (le site de l'Agefiph était
> inaccessible depuis l'environnement de rédaction).
>
> **Formulation commerciale à utiliser :** « un aménagement **finançable en grande
> partie, voire en totalité**, par l'Agefiph ou le FIPHFP ». Ne pas écrire « 100 %
> remboursé ».

**Exemple.** Un poste à 640 € HT la première année, financé à 90 % : reste à charge de
**64 € pour l'employeur**. Avec un accord agréé, le reste à charge est pris sur un
budget déjà prévu.

**Points de vigilance pour le dossier :**
- l'aide de l'Agefiph **ne dispense pas** l'employeur de son obligation d'aménager le
  poste, même en cas de refus ;
- les **renouvellements annuels** (290 €) ne sont pas forcément finançables : d'où
  l'option de licence de 3 ans (section 2.1) ;
- Gestura doit fournir un **modèle de devis et une fiche descriptive** (fonctions,
  public, contre-indications) prêts à joindre au dossier. C'est un argument de vente :
  on simplifie le travail du référent handicap.

### 3.2 Le levier financier : la contribution OETH

> ⚠️ **Correction par rapport à l'hypothèse de départ.** L'achat de Gestura **ne réduit
> pas automatiquement** la contribution Agefiph. Le vrai levier est le **maintien dans
> l'emploi** d'un salarié qui compte dans les 6 %. Il existe aussi une déduction directe,
> mais elle est limitée et ses règles ont changé en 2025–2026.

**Comment est calculée la contribution.** Une entreprise de 20 salariés ou plus qui
n'emploie pas 6 % de bénéficiaires paie, **pour chaque bénéficiaire manquant** :

| Effectif | Montant par bénéficiaire manquant | En 2026 (SMIC horaire à 12,02 €) |
|---|---|---|
| 20 à 249 salariés | 400 × SMIC horaire | **4 808 € par an** |
| 250 à 749 salariés | 500 × SMIC horaire | **6 010 € par an** |
| 750 salariés et plus | 600 × SMIC horaire | **7 212 € par an** |
| Aucune action pendant 3 ans (aucun bénéficiaire, aucun achat au secteur protégé, aucun accord) | 1 500 × SMIC horaire | **18 030 € par an** |

**Levier n° 1 — garder le salarié dans l'emploi (le plus important).** Un salarié
reconnu handicapé qui ne peut plus utiliser la souris risque l'inaptitude, puis le
licenciement. S'il part, l'entreprise perd une unité dans son taux d'emploi : sa
contribution augmente de **4 808 à 7 212 € par an**. Gestura coûte **640 € la première
année** (largement financés), puis 290 € par an.

*Exemple : entreprise de 300 salariés, obligation de 18 bénéficiaires, 15 employés.
Elle paie 3 × 6 010 = 18 030 € par an. Si un salarié souffrant d'un canal carpien
sévère doit partir faute d'aménagement, elle paie 24 040 €. Garder ce salarié avec
Gestura : 640 € la première année, financés à 90 % ou plus, pour éviter
**6 010 € par an** de contribution supplémentaire, sans compter le coût d'un
licenciement et d'un recrutement.*

Le salarié compte dans les 6 % qu'il utilise Gestura ou non : l'argument n'est pas que
le logiciel « rapporte » des points, mais qu'il rend le maintien dans l'emploi possible.

**Levier n° 2 — déduire le reste à charge (direct, mais plafonné).** Certaines dépenses
peuvent être déduites de la contribution brute, au prix HT, **dans la limite de 10 % de
la contribution**. D'après l'Agefiph (fiche de 2025), le reste à charge de l'employeur
sur une adaptation de poste peut être valorisé au titre du **maintien dans l'emploi**,
seulement pour la part qui n'est pas déjà financée par une aide. Mais la liste des
dépenses déductibles a été réduite au 1er janvier 2025, puis modifiée par un décret du
24 décembre 2025, et les sources ne sont pas d'accord sur ce qui reste déductible en
2026. **À faire confirmer** (Urssaf, Agefiph ou expert-comptable du client) avant de
s'en servir comme argument.

*Ordre de grandeur : pour une contribution brute de 18 030 €, le plafond de déduction est
de 1 803 € ; un reste à charge de 64 € par poste y tient largement.*

**Levier n° 3 — à étudier : sous-traiter à une entreprise adaptée.** Les achats auprès
d'entreprises adaptées (EA), d'ESAT ou de travailleurs indépendants handicapés se
déduisent de la contribution. Confier une partie de la prestation (installation sur
site, support de premier niveau) à une **entreprise adaptée du numérique** permettrait
au client de déduire une part de la facture. C'est une piste de partenariat, dont les
modalités sont à vérifier.

### 3.3 Le message pour l'employeur

> « Un salarié qui ne peut plus utiliser sa souris risque l'inaptitude. Le garder dans
> l'emploi évite **4 808 à 7 212 € de contribution par an**. Gestura coûte **640 €** la
> première année, **finançables en grande partie, voire en totalité, par l'Agefiph**.
> Nous préparons le devis et la fiche descriptive pour le dossier. »

---

## 4. Projections financières

### 4.1 Hypothèses

| Hypothèse | Valeur | Justification |
|---|---|---|
| Cycle de vente | **3 à 6 mois**, souvent 6 | Avis du médecin du travail, dossier de financement, validation DSI, référencement achats |
| Prix | 290 € de licence + 350 € de pack, **sans remise** | Tarif de la section 2 |
| Pack | Facturé une fois, sur chaque **nouveau** poste | Obligatoire la 1ʳᵉ année |
| Licence | Facturée chaque année sur chaque poste **actif** | Facturation annuelle |
| « Postes équipés » | **Cumul** des postes installés depuis le lancement | Objectifs du verdict |
| Non-renouvellement | 2 postes sur 15 en année 2 (≈ 13 %), 7 sur 68 en année 3 (≈ 10 %) | Départ du salarié, changement de poste, inadaptation. Taux inconnu : à mesurer |
| Taille moyenne d'un client | 4 à 5 postes en année 1, 5 à 6 ensuite | 15 postes chez 3 ou 4 entreprises partenaires |
| Revendeurs (année 3) | Achètent au tarif éditeur et ajoutent leur marge sur le devis du client final | À négocier ; voir la sensibilité en 4.4 |
| Microsoft Store | 2 k€ par an (milieu de la fourchette de 1 à 4 k€) | Verdict, scénario prudent |

### 4.2 Chiffre d'affaires B2B

| | **Année 1 — Pilote** | **Année 2 — Décollage** | **Année 3 — Croissance** |
|---|---|---|---|
| Postes équipés (cumul) | **15** | **70** | **180** |
| Nouveaux postes | 15 | 55 | 110 |
| Postes non renouvelés | 0 | 2 | 7 |
| Postes actifs (licences facturées) | 15 | 68 | 171 |
| Licences (× 290 €) | 4 350 € | 19 720 € | 49 590 € |
| Packs (× 350 €) | 5 250 € | 19 250 € | 38 500 € |
| **CA B2B** | **9 600 €** (≈ 10 k€) | **38 970 €** (≈ 39 k€) | **88 090 €** (≈ 88 k€) |
| Nouveaux clients (environ) | 3 à 4 entreprises partenaires | 6 à 8 | 10 à 12, dont une partie via les revendeurs |
| Canal principal | Pilotes avec ergonomes et missions handicap | Recommandations, vente directe | Revendeurs d'aides techniques + vente directe |

**Écart avec les cibles du verdict (10 / 38 / 90 k€) : moins de 3 %.** Sans aucun
non-renouvellement, l'année 3 atteindrait 90 700 €.

**À noter :** les packs pèsent environ **la moitié du chiffre d'affaires** tant que la
croissance est forte. Le revenu récurrent (licences) ne devient majoritaire qu'à partir
de l'année 3. C'est un point de fragilité : si les ventes nouvelles ralentissent, le
chiffre d'affaires baisse vite.

### 4.3 Compte de résultat simplifié

| | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| CA B2B | 9,6 k€ | 39,0 k€ | 88,1 k€ |
| Microsoft Store (net) | 2,0 k€ | 2,0 k€ | 2,0 k€ |
| **Total des produits** | **11,6 k€** | **41,0 k€** | **90,1 k€** |
| Structure, comptabilité, assurance RC pro | − 3,0 k€ | − 3,5 k€ | − 4,0 k€ |
| Signature de l'installateur MSI | − 0,1 k€ | − 0,1 k€ | − 0,1 k€ |
| Déplacements, salons, supports commerciaux | − 2,5 k€ | − 4,0 k€ | − 5,0 k€ |
| Outils (prospection, visio, CRM) *(estimation)* | − 1,0 k€ | − 1,0 k€ | − 1,0 k€ |
| Tests utilisateurs, pilotes | − 0,5 k€ | — | — |
| **Charges externes** | **− 7,1 k€** | **− 8,6 k€** | **− 10,1 k€** |
| **Résultat avant rémunération du fondateur** | **≈ + 4,5 k€** | **≈ + 32 k€** | **≈ + 80 k€** |

*Avant impôts, charges sociales et rémunération du fondateur. Les charges reprennent
les fourchettes de la stratégie économique.*

**Temps de travail nécessaire** (estimation : 3 h 30 par pack, 1 h de support par
poste actif et par an, hors prospection) :

| | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| Installation et formation | ≈ 50 h | ≈ 190 h | ≈ 385 h |
| Support | ≈ 15 h | ≈ 70 h | ≈ 170 h |
| **Total hors vente** | **≈ 65 h** | **≈ 260 h** | **≈ 555 h** (environ un tiers de temps plein) |

**Lecture :**
- **Année 1 :** le B2B couvre ses frais, **pas le temps du fondateur**. C'est une
  année de preuve, pas de revenu.
- **Année 2 :** environ 32 k€ avant rémunération : un **complément de revenu**, pas un
  salaire complet chargé.
- **Année 3 :** environ 80 k€ : de quoi **rémunérer un fondateur à temps plein**, pas
  encore une équipe. La vente et la prospection prennent alors au moins 40 % du temps.

### 4.4 Sensibilité

| Scénario | Année 2 | Année 3 | Effet |
|---|---|---|---|
| **Central** (ci-dessus) | 39,0 k€ | 88,1 k€ | — |
| Aucun non-renouvellement | 39,6 k€ | 90,7 k€ | + 3 % |
| **30 % de non-renouvellement** (renouvellements non financés par l'Agefiph) | 38,1 k€ | ≈ 83,5 k€ | − 5 % : la croissance compense à court terme, mais le revenu récurrent s'effondre ensuite |
| **Remise revendeur de 30 %** sur 40 % des nouveaux postes de l'année 3 (≈ 45 postes) | 39,0 k€ | ≈ 79,5 k€ | − 10 % : à négocier dès le premier contrat de revendeur |
| **Cycles de 9 mois au lieu de 3 à 6** *(estimation)* | ≈ 25 k€ | ≈ 65 k€ | Ventes décalées d'environ un semestre |
| **Échec du jalon 3** (pilotes non transformés) | 0 | 0 | NO-GO : seul le volet open source subsiste (Store : 1 à 4 k€) |

---

## 5. Canaux d'acquisition (go-to-market)

### 5.1 B2B indirect : les prescripteurs et les relais (priorité)

Dans l'accessibilité, **on ne vend pas à l'utilisateur : on est recommandé par un
professionnel.** Les prescripteurs sont peu nombreux et se connaissent : la réputation
compte plus que la publicité.

| Partenaire | Ce qu'il apporte | Ce que Gestura lui apporte | Modalité |
|---|---|---|---|
| **Cabinets d'ergonomie** (études de poste, intervenants en prévention) | Des recommandations dans leurs études de poste, l'accès aux entreprises clientes | Une solution de plus pour les TMS du poignet, une formation gratuite, une licence de démonstration | Partenariat de prescription ; commission d'apport possible (≈ 10 %), à décider |
| **Écoles et instituts de formation en ergothérapie** | **Les tests d'usage** (jalon 2), des mémoires d'étudiants, une crédibilité clinique ; à terme, de futurs prescripteurs | Un sujet d'étude, un outil open source gratuit pour l'enseignement | Convention de partenariat ; protocole de test de 15 minutes déjà rédigé |
| **Revendeurs de matériel adapté et d'aides techniques** | Un réseau commercial national, l'habitude des dossiers Agefiph, des clients existants | Un produit sans stock, bon marché, qui complète leur catalogue (souris et claviers ergonomiques) | Contrat de revente à partir de l'année 3 ; formation et certification des techniciens ; marge à négocier (voir 4.4) |
| **Services de santé au travail, Cap emploi** (conseillers en maintien dans l'emploi) | Le repérage des situations, l'avis du médecin du travail | Une fiche descriptive claire, des démonstrations | Information et démonstrations ; **pas de commission** (organismes publics ou associatifs) |
| **Entreprises adaptées du numérique** | Installation sur site, support de premier niveau | Une activité ; pour le client, un achat déductible de la contribution | Piste à étudier (section 3.2) |

**Séquence :**
1. **Mois −6 à 0 (validation) :** 1 ou 2 écoles d'ergothérapie pour le test utilisateur ;
   2 ou 3 cabinets d'ergonomie pour trouver les entreprises pilotes.
2. **Année 1 :** 3 ou 4 entreprises pilotes, toutes amenées par un ergonome ou un
   ergothérapeute.
3. **Année 2 :** études de cas publiées, puis élargissement à 5 à 10 cabinets
   partenaires.
4. **Année 3 :** premier contrat avec un revendeur d'aides techniques.

### 5.2 B2B direct : les missions handicap et QVT sur LinkedIn

**Cibles :** responsables de mission handicap, référents handicap, responsables QVT
(qualité de vie au travail) et santé-sécurité, ergonomes internes des entreprises de
plus de 250 salariés.

**Contenus (un par semaine environ) :**
- **Études de cas tirées des pilotes**, avec l'accord écrit de l'entreprise et du
  salarié : situation, aménagement réalisé, financement obtenu, résultat ;
- **Courtes vidéos** : un geste, une tâche réelle de bureau (classer des courriels,
  remplir un tableau) ;
- **Pédagogie du financement** : « comment monter un dossier Agefiph pour un logiciel
  d'aménagement de poste », « ce que coûte la perte d'un salarié reconnu handicapé » ;
- **Temps forts :** la Semaine européenne pour l'emploi des personnes handicapées
  (novembre), les salons des aides techniques et de l'emploi des personnes handicapées.

**Démarche :**
1. Liste de 200 entreprises cibles (plus de 250 salariés, activités de bureau, accord
   agréé ou taux d'emploi publié) ;
2. Prise de contact personnalisée, avec une étude de cas du même secteur ;
3. Démonstration de 20 minutes en visio ;
4. Pilote sur 1 à 3 postes, avec un ergonome ;
5. Déploiement et modèle de devis pour le dossier de financement.

**Entonnoir estimé** (hypothèses à mesurer dès les premiers mois) : environ **5 à
6 rendez-vous qualifiés pour un nouveau client**, soit environ 40 rendez-vous en
année 2 et 60 en année 3.

### 5.3 Règles de communication (à respecter)

| Règle | Pourquoi |
|---|---|
| **Ne jamais dire que Gestura « soigne » ou « soulage » une pathologie.** Dire : « une alternative à la souris pour l'aménagement de poste », « permet de travailler sans saisir la souris ». | Un logiciel destiné à « atténuer » une maladie ou à « compenser » un handicap peut relever du **règlement européen sur les dispositifs médicaux**. La formulation de la destination du produit décide de son statut : à faire valider par un spécialiste réglementaire **avant** toute communication sur les TMS. |
| **Ne pas promettre « 100 % financé ».** Dire « finançable en grande partie, voire en totalité ». | Le taux de l'Agefiph varie et se décide au cas par cas (section 3.1) |
| **Aucune donnée de santé dans les études de cas sans consentement écrit**, et anonymiser par défaut | Les données de santé sont des données sensibles au sens du RGPD |
| **Afficher les contre-indications** (épaule) sur chaque fiche produit | Protection des utilisateurs et crédibilité auprès des prescripteurs |

---

## 6. Risques et parades

| Risque | Probabilité | Impact | Parade |
|---|---|---|---|
| Le test utilisateur échoue (jalon 2) | Moyenne | Fort | Corriger et refaire une fois ; sinon NO-GO et volet open source seul |
| L'Agefiph refuse de financer un logiciel gratuit sur GitHub | Moyenne | Fort | Devis centré sur le service et l'Édition Entreprise ; obtenir un premier accord pendant les pilotes et s'en servir de modèle |
| Les renouvellements ne sont pas financés | Moyenne | Moyen | Licence de 3 ans prépayée ; montrer le coût évité de la contribution |
| Statut de dispositif médical | Faible à moyenne | Fort | Formulations prudentes (5.3) ; avis réglementaire avant le lancement |
| Aggravation d'une pathologie de l'épaule | Faible | Fort | Installation seulement sur prescription ; contre-indication écrite ; mode bras bas |
| Cycles de vente plus longs que prévu | Forte | Moyen | Plusieurs pilotes en parallèle ; le Store finance les frais fixes |
| Dépendance au fondateur (vente, installation, support) | Forte | Fort | Former les revendeurs et les entreprises adaptées dès l'année 3 |
| Concurrence gratuite (Accès vocal de Windows) ou établie (Tobii, Cephable) | Moyenne | Moyen | Se placer sur la niche « mains, webcam standard, 100 % local » |
| Fork du code sous GPL par un concurrent | Faible | Faible | La valeur vendue est le service et le réseau de prescripteurs, pas le code |

---

## 7. Indicateurs de pilotage

| Indicateur | Objectif | Fréquence |
|---|---|---|
| Rendez-vous qualifiés → pilotes | ≥ 30 % | Mensuelle |
| Pilotes → déploiement | ≥ 2 sur 3 (jalon 3) | À chaque pilote |
| Dossiers de financement acceptés | ≥ 80 % | Par dossier |
| Durée moyenne du cycle de vente | ≤ 6 mois | Trimestrielle |
| Renouvellement des licences | ≥ 85 % | Annuelle |
| Utilisation réelle à 30 jours (déclarée par le salarié au point de suivi) | ≥ 75 % des postes | Par poste |
| Ventes sur le Microsoft Store | 110 à 570 par an | Mensuelle |
| Temps passé par pack | ≤ 3 h 30 | Trimestrielle |

---

## 8. Prochaines étapes

| Quand | Action |
|---|---|
| **Maintenant** | Publication sur le Microsoft Store (paquet prêt) ; dépôt public sous GPL v3 ; contact avec 1 ou 2 écoles d'ergothérapie |
| Mois 1–3 | Alerte d'éclairage, mode bras bas, installateur MSI (jalon 1) ; fiche descriptive et modèle de devis pour l'Agefiph |
| Mois 2–3 | Avis réglementaire (dispositifs médicaux) ; vérifier le taux Agefiph 2026 et les règles de déduction 2026 ; structure juridique et assurance RC pro |
| Mois 4–5 | Test utilisateur (jalon 2) |
| Mois 5–9 | 3 ou 4 entreprises pilotes avec des ergonomes (jalon 3) ; premier dossier Agefiph |
| **GO** | Début de l'année 1 de ce plan |

---

## 9. Sources

**Documents internes :** [verdict commercial](verdict_commercial_gestura.md) ·
[stratégie économique](business_model_gestura.md) ·
[analyse de friction](friction_utilisation.md) ·
[analyse de positionnement](analyse_positionnement.md)

**Aides Agefiph à l'aménagement de poste :**
- [Agefiph — aide à l'adaptation des situations de travail (janvier 2026)](https://www.agefiph.fr/sites/default/files/medias/fichiers/2026-01/Agefiph-Aide-adaptation-situation-travail_2026-01.pdf)
- [Agefiph — aide à l'adaptation des situations de travail (octobre 2025)](https://www.agefiph.fr/sites/default/files/medias/fichiers/2025-10/Agefiph_aide-adaptation-situation-travail_2025-10.pdf)
- [les-aides.fr — fiche Agefiph (logiciels spécifiques, avis du médecin du travail)](https://les-aides.fr/aide/FIH9/agefiph.aide-a-l-adaptation-des-situations-de-travail.pdf)
- [Legisocial — aides Agefiph au 1er août 2024 (limite de 90 % du surcoût)](https://www.legisocial.fr/actualites-sociales/6863-aides-financieres-agefiph-situation-1er-aout-2024.html)
- [Informations handicap — calcul du surcoût](https://informations.handicap.fr/a--4157.php)
- [Mon Parcours Handicap — aides Agefiph aux employeurs](https://www.monparcourshandicap.gouv.fr/employeurs/les-aides-au-recrutement-et-lintegration-de-lagefiph)
- [Agefiph — sortie d'accord agréé (2023)](https://www.agefiph.fr/sites/default/files/medias/documents_presse/2023-06/CP_Sortie%20accord%20agreedocx.pdf)

**FIPHFP (fonction publique) :**
- [FIPHFP — catalogue des interventions 2026](https://www.fiphfp.fr/sites/default/files/2026-02/Catalogue%20des%20interventions%20VERSION%20DEFINITIVE%202026%20OKnewcouv_0.pdf)
- [FHF — les aides du FIPHFP (février 2026)](https://fichiers.fhf.fr/documents/Fiche-pratique-Handicap-Les-aides-du-FIPHFP-fev-2026.docx)

**Obligation d'emploi, contribution et déductions :**
- [Code du travail, article L5212-2 (obligation de 6 %)](https://code.travail.gouv.fr/code-du-travail/l5212-2)
- [Code du travail, article D5212-23 (dépenses déductibles, plafond de 10 %)](https://code.travail.gouv.fr/code-du-travail/d5212-23)
- [Agefiph — fiche OETH n° 5, dépenses déductibles (décembre 2025)](https://www.agefiph.fr/sites/default/files/medias/fichiers/2026-01/Agefiph_OETH-Fiche5-depenses-deductibles_2025-12.pdf)
- [Agefiph — fiche OETH n° 6, contribution](https://www.agefiph.fr/sites/default/files/medias/fichiers/2023-02/OETH_FICHE6_CONTRIBUTION.pdf)
- [Lefebvre Dalloz — nouveautés DOETH 2026](https://open.lefebvre-dalloz.fr/actualites/droit-social/nouveautes-doeth-2026_f8349f538-d41c-49dd-8dda-98ceea3d6301)
- [Centre Inffo — dépenses de partenariat à nouveau déductibles](https://www.centre-inffo.fr/?p=505975)
- [Weblex — dépenses déductibles en 2025](https://www.weblex.fr/weblex-actualite/obligation-d-emploi-des-travailleurs-handicapes-des-changements-en-2025)
- [Éditions Tissot — montants du SMIC au 1er janvier 2026](https://www.editions-tissot.fr/actualite/droit-du-travail/telechargement/smic-synthese-des-montants-applicables-a-compter-du-1er-janvier-2026)
- [MSA — aide au calcul de l'OETH](https://msa.fr/lfp/documents/11566/96828499/Aide+au+calcul+de+l'OETH)

**TMS :**
- [INRS — statistiques des TMS](https://www.inrs.fr/risques/tms-troubles-musculosquelettiques/statistiques.html)
- [Santé publique France — sous-déclaration des TMS (2009–2015)](https://www.santepubliquefrance.fr/maladies-liees-au-travail/maladies-a-caractere-professionnel/article/estimation-de-la-sous-declaration-des-tms-en-france-evolution-entre-2009-et-2015)

**Microsoft Store, Krita, prix de marché :** voir la section 9 de la
[stratégie économique](business_model_gestura.md#9-sources).

### Points à vérifier avant usage commercial

1. **Le taux de prise en charge de l'Agefiph en 2026** (90 % du surcoût en 2024, et non
   100 % selon les sources trouvées) et la prise en charge des renouvellements annuels.
2. **L'accès des entreprises sous accord agréé aux aides de l'Agefiph** (les sources
   récentes et anciennes divergent).
3. **La liste des dépenses déductibles en 2026** après le décret du 24 décembre 2025.
4. **Le statut réglementaire** au regard du règlement européen sur les dispositifs
   médicaux, selon la formulation retenue pour la destination du produit.
5. **La valeur du SMIC horaire** au 31 décembre de l'année de calcul de la contribution.

*Le site de l'Agefiph était inaccessible depuis l'environnement de rédaction : les
informations le concernant proviennent des résultats de recherche et de sites
relais.*
