# Stratégie économique de Gestura — comparaison de trois modèles

*Document rédigé le 7 novembre 2026, à partir de la version 0.3.0 de Gestura.
Les **faits** sont sourcés (section 9). Les **prévisions** reposent sur des hypothèses
explicites (section 8) : ce sont des ordres de grandeur pour décider, pas des
promesses. Aucune étude de marché primaire (entretiens, sondage) n'a encore été menée.*

---

## 1. Résumé et recommandation

| | Modèle 1 — Store payant | Modèle 2 — Licence B2B accessibilité | Modèle 3 — Open-core |
|---|---|---|---|
| Revenu annuel à 3 ans (scénario central) | **~17 k€** | **~90 k€** | **~12 k€** |
| Délai avant le premier euro | 1 à 2 mois | 6 à 12 mois | 6 à 9 mois |
| Investissement initial | Très faible | Élevé (fonctionnalités, structure, vente) | Moyen (développement Pro) |
| Adéquation au produit actuel | Bonne (Windows) | Partielle (manquent le pointeur tête, le déploiement entreprise) | Bonne |
| Peut financer un salaire | Non | Oui, si l'effort commercial suit | Seulement en cas de forte audience |
| Risque principal | Revenu marginal | Cycles de vente longs | Conversion trop faible |

**Recommandation : ne pas choisir un seul modèle, mais les enchaîner.**

1. **Tout de suite — Modèle 1 sur le Microsoft Store** (Windows uniquement, 12,99 €) :
   coût quasi nul, il règle au passage le problème d'avertissement Windows
   (application signée par le Store) et apporte un petit revenu et de la visibilité.
2. **Objectif principal à 12–24 mois — Modèle 2 (B2B)** : c'est le seul qui peut
   financer le projet. Il faut d'abord combler trois manques : pointeur à la tête avec
   clic par immobilité, déploiement en entreprise, preuves d'usage (pilotes).
3. **Open-core orienté entreprise plutôt que grand public** : les fonctions payantes
   sont celles utiles aux organisations (déploiement, profils gérés, support). Pour un
   particulier en situation de handicap, toutes les fonctions d'accessibilité restent
   gratuites — c'est à la fois plus éthique et plus cohérent commercialement.

**Prévision combinée (scénario central) : ~14 k€ la 1ʳᵉ année, ~50 k€ la 2ᵉ, ~115 k€
la 3ᵉ.** Un revenu équivalent à un salaire n'est réaliste qu'en 3ᵉ année, et
uniquement si l'activité B2B décolle.

---

## 2. Point de départ : ce que permet le produit aujourd'hui

- **Windows uniquement.** Pas de version macOS.
- **Pas de licence open source définie.** Le code est consultable sur GitHub, mais sans
  licence il n'est ni réutilisable ni « open source » au sens juridique. Le choix de
  licence conditionne les trois modèles (section 7).
- **Application non signée** : avertissement SmartScreen au téléchargement.
- **Public servi :** personnes qui peuvent bouger les bras (mains occupées, sales,
  douleurs à la souris, motricité fine réduite). **Pas encore** les personnes sans usage
  des membres supérieurs : pas de pointeur à la tête ni de clic par immobilité.
- **Aucune donnée d'usage réelle** (nombre d'utilisateurs, rétention) : à mesurer.

---

## 3. Modèle 1 — Gratuit sur GitHub, payant (9 à 19 €) sur les stores

### Principe
Le code et l'installateur restent gratuits sur GitHub. Le même logiciel est vendu sur
le Microsoft Store pour ceux qui veulent une installation en un clic, signée, avec
mises à jour automatiques. C'est le modèle de **Krita**, logiciel de dessin libre vendu
9,95 $ puis 19,95 $ sur les stores alors qu'il est gratuit sur son site.

### Ce que disent les faits
- **Autorisé par Microsoft :** en 2022, une règle du Store a brièvement interdit de
  vendre des logiciels libres disponibles gratuitement ailleurs ; Microsoft l'a retirée
  après protestation, pour ne viser que les copies faites par des tiers. L'auteur
  d'un logiciel peut donc le vendre.
- **Commission Microsoft :** 15 % via le système de paiement du Store ; 0 % si
  l'application utilise son propre système de paiement.
- **Inscription développeur :** gratuite pour les particuliers depuis 2025 (selon une
  seule source, à vérifier dans l'Espace partenaires).
- **Mac App Store : bloqué en l'état.** Le bac à sable obligatoire des applications du
  Mac App Store interdit d'injecter des événements souris et clavier (CGEventPost),
  ce qui est le cœur de Gestura ; des applications ont été refusées pour ce motif.
  Sur Mac, la seule voie réaliste est une **vente directe** d'une application
  notarisée (hors Store), après un portage macOS qui reste à faire.

### Prix et revenu unitaire
- Prix conseillé : **12,99 € TTC** (entre le bas de la fourchette et un prix qui ne
  paraît pas « gadget »).
- Revenu net par vente : 12,99 € − TVA 20 % = 10,83 € HT ; − 15 % de commission
  ≈ **9,20 € par vente**.

### Prévisions (ventes Microsoft Store uniquement)

| Scénario | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| Pessimiste | 100 ventes · 0,9 k€ | 200 · 1,8 k€ | 300 · 2,8 k€ |
| **Central** | **400 · 3,7 k€** | **1 000 · 9,2 k€** | **1 800 · 16,6 k€** |
| Optimiste (vidéo virale, presse tech) | 2 500 · 23 k€ | 5 000 · 46 k€ | 7 000 · 64 k€ |

*Hypothèses : application de niche, découverte surtout par la recherche dans le Store
et quelques vidéos de démonstration ; pas de budget publicitaire ; croissance portée
par les avis et les nouvelles fonctions.*

### Coûts
- Quasi nuls : inscription gratuite, signature assurée par le Store (pas de certificat
  à acheter pour ce canal).
- Temps de support : 2 à 4 h par semaine (webcams, éclairage, demandes de
  remboursement).
- Mac (plus tard) : portage de 2 à 3 mois, compte Apple Developer (99 $/an), plateforme
  de paiement pour la vente directe (de l'ordre de 5 % par transaction).

### Forces et faiblesses
- ✅ Démarrage en quelques semaines, sans risque financier.
- ✅ Résout l'avertissement SmartScreen pour les acheteurs du Store.
- ✅ Compatible avec un code ouvert (précédent Krita).
- ❌ Revenu faible : complément, pas un modèle économique.
- ❌ Clients grand public exigeants pour 13 € (matériel varié, remboursements).
- ❌ Pas de Mac App Store possible.

---

## 4. Modèle 2 — Licence commerciale B2B (postes de travail PMR / accessibilité)

### Principe
Vendre aux employeurs une solution d'aménagement de poste : licence par poste,
installation et calibration, formation, support. L'acheteur n'est pas l'utilisateur :
c'est la mission handicap, le service RH ou le service de santé au travail, souvent
sur recommandation d'un ergonome ou d'un ergothérapeute.

### Pourquoi c'est le modèle le plus prometteur
- **Une obligation légale crée la demande :** les entreprises de 20 salariés ou plus
  doivent employer 6 % de travailleurs handicapés. Environ 107 900 entreprises sont
  concernées (628 800 travailleurs handicapés employés en 2021).
- **Un financeur existe :** l'aide Agefiph à l'adaptation des situations de travail
  couvre notamment les **logiciels spécifiques**, sur devis, après avis du médecin du
  travail. Gestura peut ainsi être financé sans peser sur le budget de l'employeur.
- **Les TMS représentent plus de 80 % des maladies professionnelles reconnues**
  (40 000 TMS indemnisés par an au seul titre du tableau 57, 1 milliard d'euros de frais
  en 2021). Un outil qui remplace la souris s'adresse à ce besoin massif, sans attendre
  le pointeur à la tête.
- **Prix de marché élevés :** Dragon Professional (dictée vocale) coûte 699,99 $ en
  licence individuelle, environ 1 100 à 1 500 $ par utilisateur en édition entreprise ;
  Tobii Communicator à partir de 449 £. Un prix de quelques centaines d'euros par poste
  est donc crédible.
- **Le traitement 100 % local** est un argument fort auprès des DSI et délégués à la
  protection des données (aucune image ne quitte le poste).

### Offre proposée
| Élément | Prix HT indicatif |
|---|---|
| Licence par poste et par an (mises à jour + support) | 290 € |
| Installation, calibration et formation à distance (par poste) | 350 € |
| Licence site (jusqu'à 50 postes) | 4 900 €/an |
| Pilote de 3 mois (1 à 3 postes, accompagnement inclus) | 2 500 € |

### Prérequis avant de vendre (6 à 12 mois)
1. **Fonctionnels :** pointeur à la tête + clic par immobilité (pour ouvrir le public
   PMR) ; mode « repos » contre la fatigue des bras.
2. **Entreprise :** installateur MSI signé, déploiement silencieux (Intune, GPO),
   configuration centralisée, aucune connexion requise.
3. **Juridiques et administratifs :** structure juridique pour facturer, assurance
   responsabilité civile professionnelle, conditions générales de licence et de support,
   dossier RGPD (traitement local).
4. **Preuves :** 3 à 5 pilotes documentés avec des ergothérapeutes ou ergonomes ;
   témoignages ; mesures (temps de prise en main, réduction de l'usage de la souris).
5. **Signature de code :** Azure Artifact Signing à 9,99 $/mois (la réputation
   SmartScreen se construit progressivement).

### Canaux de vente
- Missions handicap des grands groupes et de la fonction publique.
- Ergonomes, ergothérapeutes, services de prévention et de santé au travail
  (prescripteurs).
- Revendeurs et intégrateurs d'aides techniques (commission de 25 à 35 %).
- Salons et réseaux de l'emploi des personnes handicapées.

**Cycle de vente :** 3 à 9 mois, avec presque toujours un pilote préalable.

### Prévisions (postes actifs en fin d'année, revenus de l'année)

| Scénario | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| Pessimiste (pas de partenaire, vente directe seule) | 1 pilote gratuit · ~0 k€ | 20 postes · 8 k€ | 40 postes · 15 k€ |
| **Central** | **2 pilotes payants + 15 postes · ~10 k€** | **80 postes · ~38 k€** | **220 postes · ~90 k€** |
| Optimiste (un revendeur national ou un grand compte) | 50 postes · 25 k€ | 300 postes · ~110 k€ | 800 postes · ~280 k€ |

*Calcul central année 3 : 220 postes × 290 € ≈ 64 k€ de licences + ~100 nouvelles
installations × 250 € (après remises) ≈ 25 k€ de services.*

### Coûts annuels
- Structure, comptabilité, assurance : 2 à 3,5 k€.
- Signature de code : ~120 €.
- Déplacements, salons, supports commerciaux : 2 à 5 k€.
- **Temps du fondateur :** au moins 40 % consacré à la vente et au support. C'est le
  vrai coût de ce modèle.

### Forces et faiblesses
- ✅ Seul modèle capable de financer un emploi à 3 ans.
- ✅ Demande portée par la loi et financée par l'Agefiph.
- ✅ Compatible avec un cœur open source (on vend le service, le déploiement, le support).
- ❌ Produit pas encore prêt pour le public PMR le plus large.
- ❌ Cycles longs, besoin de preuves, responsabilité envers des utilisateurs vulnérables.
- ❌ Concurrence d'outils gratuits intégrés (Accès vocal Windows) et d'acteurs installés
  (Tobii, Cephable).

---

## 5. Modèle 3 — Open-core (base gratuite, fonctions avancées payantes)

### Principe
Toutes les fonctions actuelles restent gratuites et ouvertes. Une édition **Pro**
payante ajoute des fonctions avancées, distribuées dans un module séparé.

### Contenu Pro envisagé
- **Macros :** une suite d'actions (touches, texte, clics) sur un seul geste.
- **Gestes personnalisés :** enregistrer ses propres gestes.
- **Profils par application :** changement automatique (navigateur, lecteur
  multimédia, présentation).
- **Intégrations :** mode présentation (PowerPoint), actions façon Stream Deck,
  domotique par webhooks locaux.
- **Gestion multi-utilisateurs et export/import de configuration.**

**Prix :** 39 €/an ou 79 € en licence à vie (clé de licence signée, vérifiée hors
ligne, sans compte ni télémétrie).

### Prévisions

Le revenu dépend directement de l'audience. Repères de conversion du gratuit vers
le payant : 1 à 4 % pour un freemium large, 2 à 5 % en moyenne.

| Scénario | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| Pessimiste | 500 actifs · 1 % · ~0,2 k€ | 1 500 · 1 % · ~0,6 k€ | 3 000 · 1,5 % · ~1,8 k€ |
| **Central** | **1 250 actifs · 2 % · ~1 k€** | **4 000 · 3 % · ~4,7 k€** | **10 000 · 3 % · ~11,7 k€** |
| Optimiste (forte viralité) | 6 000 · 3 % · ~7 k€ | 20 000 · 4 % · ~31 k€ | 40 000 · 4 % · ~62 k€ |

*« Actifs » = utilisateurs qui se servent de Gestura au moins une fois par mois,
estimés à environ 25 % des téléchargements cumulés. Revenu = payants × 39 €.*

### Coûts
- Développement des fonctions Pro : 2 à 4 mois.
- Maintenance de deux éditions, système de licences hors ligne.
- Plateforme de paiement : de l'ordre de 5 % par transaction.
- Accord de contribution (CLA) pour pouvoir publier les contributions externes sous
  plusieurs licences.

### Forces et faiblesses
- ✅ Garde une base gratuite large (adoption, communauté, réputation).
- ✅ Les fonctions Pro servent aussi le B2B.
- ❌ Revenu faible tant que l'audience est petite ; la mesurer suppose de la télémétrie,
  en tension avec la promesse « rien ne quitte votre ordinateur ».
- ❌ Faire payer des fonctions d'accessibilité à des personnes handicapées, souvent à
  revenus modestes, est délicat éthiquement et en termes d'image.
- ❌ Si le cœur est sous licence copyleft, une communauté peut réimplémenter les
  fonctions Pro dans un fork.

---

## 6. Comparaison détaillée

| Critère | Modèle 1 — Store | Modèle 2 — B2B | Modèle 3 — Open-core |
|---|---|---|---|
| Revenu à 3 ans (central) | 16,6 k€ | ~90 k€ | 11,7 k€ |
| Revenu à 3 ans (optimiste) | 64 k€ | ~280 k€ | ~62 k€ |
| Temps avant le premier euro | 1–2 mois | 6–12 mois | 6–9 mois |
| Travail de développement préalable | Empaquetage MSIX | Pointeur tête, MSI, admin | Fonctions Pro, licences |
| Effort commercial | Faible | Très élevé | Moyen (communauté) |
| Dépendance à l'audience grand public | Forte | Faible | Très forte |
| Revenus récurrents | Non (achat unique) | Oui (licence annuelle) | Oui (abonnement) |
| Compatibilité avec un cœur open source | Oui (précédent Krita) | Oui | Oui, par conception |
| Risque d'image (faire payer l'accessibilité) | Faible (gratuit sur GitHub) | Faible (l'employeur paie) | Moyen |

---

## 7. Licence et cadre juridique : une décision à prendre en premier

- **Recommandation : cœur sous GPL v3**, comme Krita. La GPL autorise la vente sur le
  Microsoft Store, protège contre les copies propriétaires, et rassure associations et
  institutions.
- **Module entreprise ou Pro sous licence propriétaire**, dans un composant séparé.
- **Accord de contribution (CLA)** pour les contributions externes, afin de garder la
  possibilité de double licence.
- **Structure juridique** pour facturer (micro-entreprise au départ, société dès que le
  B2B démarre) et **assurance RC professionnelle** avant tout pilote.
- *À faire valider par un juriste spécialisé en logiciel avant la publication de la
  licence.*

---

## 8. Hypothèses et limites des prévisions

- Les volumes de ventes, de téléchargements et de postes sont des **estimations**,
  non issues d'une étude de marché ; ils doivent être remplacés par des mesures réelles
  dès les premiers mois.
- Aucune donnée publique n'a été trouvée sur la part des travailleurs pour lesquels un
  contrôle par gestes serait adapté ; le marché B2B accessible est donc inconnu.
- Les prix des concurrents proviennent de sites tiers et de revendeurs.
- Le scénario central suppose un fondateur à temps plein dès l'année 2, consacrant une
  part importante de son temps à la vente.
- Montants hors charges sociales et impôts.

### Prévision combinée recommandée (scénario central)

| | Année 1 | Année 2 | Année 3 |
|---|---|---|---|
| Microsoft Store | 3,7 k€ | 9,2 k€ | 16,6 k€ |
| B2B accessibilité | 10 k€ | 38 k€ | 90 k€ |
| Fonctions Pro (vendues surtout aux entreprises) | 0 | 3 k€ | 8 k€ |
| **Total** | **~14 k€** | **~50 k€** | **~115 k€** |

### Feuille de route sur 12 mois et indicateurs à suivre

| Période | Actions | Indicateurs |
|---|---|---|
| Mois 1–2 | Choix de la licence, publication sur le Microsoft Store, page de présentation, vidéo de démonstration | Ventes Store, note moyenne, demandes de support |
| Mois 2–6 | Pointeur tête + clic par immobilité, mode repos, installateur MSI | Rétention à 30 jours, temps de prise en main |
| Mois 4–9 | 3 à 5 pilotes avec ergothérapeutes et missions handicap, dossier Agefiph type | Pilotes convertis en licences, retours qualitatifs |
| Mois 9–12 | Offre B2B formalisée, partenariat avec un revendeur d'aides techniques | Postes vendus, cycle de vente moyen, coût d'acquisition |

---

## 9. Sources

- Microsoft Store : [PC Gamer — 0 % de commission hors jeux](https://www.pcgamer.com/windows-store-devs-can-keep-100-of-their-revenue-unless-theyre-making-games), [Windows Report — inscription gratuite](https://windowsreport.com/you-wont-have-to-pay-a-fee-to-publish-apps-to-microsoft-store/), [Engadget](https://www.engadget.com/microsoft-zero-percent-cut-doesnt-extend-to-games-090514788.html)
- Politique Store et logiciels libres : [Computing — retour en arrière de Microsoft](https://www.computing.co.uk/news/4053399/microsoft-reverts-store-policy-allow-sale-open-source-apps), [TechRadar](https://www.techradar.com/news/microsoft-reverses-ban-on-open-source-software-sales), [The Register](https://www.theregister.com/2022/07/08/microsoft_store_open_source_webkit/)
- Krita : [Krita sur le Windows Store](https://krita.org/en/posts/2017/krita-available-from-the-windows-store/), [hausse des prix sur les stores](https://krita.org/en/posts/2021/bumping-the-store-prices-for-krita-5-0/), [documentation d'installation](https://docs.krita.org/Installation)
- Mac App Store et bac à sable : [Apple Developer Forums 789896](https://developer.apple.com/forums/thread/789896), [Apple Developer Forums 103992](https://developer.apple.com/forums/thread/103992), [DEV Community](https://dev.to/quicopy/shipping-global-keyboard-shortcuts-on-macos-sandbox-the-part-apple-doesnt-document-57no), [refus guideline 2.4.5](https://developer.apple.com/forums/thread/820594)
- Signature de code : [Microsoft Learn — options de signature](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options), [Azure Artifact Signing](https://azure.microsoft.com/products/trusted-signing), [devclass (2026)](https://devclass.com/2026/01/14/code-signing-windows-apps-may-be-easier-and-more-secure-with-new-azure-artifact-service/)
- Agefiph : [fiche aide à l'adaptation des situations de travail (janvier 2026)](https://www.agefiph.fr/sites/default/files/medias/fichiers/2026-01/Agefiph-Aide-adaptation-situation-travail_2026-01.pdf), [les-aides.fr](https://les-aides.fr/aide/FIH9/agefiph/aide-a-l-adaptation-des-situations-de-travail.html)
- Obligation d'emploi : [Code du travail L5212-2](https://code.travail.gouv.fr/code-du-travail/l5212-2), [Vie publique](https://www.vie-publique.fr/en-bref/287047-travailleurs-handicapes-le-taux-demploi-minimal-nest-pas-atteint), [CNSA — fiche insertion professionnelle](https://www.cnsa.fr/sites/default/files/2025-01/Fiche-ressources_Insertion-professionnelle.pdf), [Hello Work Place via CHEOPS (2026)](https://www.cheops-ops.org/assets/files/cheops/national/publications/revue%20de%20presse/20260605-hello-work-place-10-chiffres-a-connaitre-sur-lemploi-et-le-handicap-en-2026.pdf)
- TMS : [INRS — statistiques](https://www.inrs.fr/risques/tms-troubles-musculosquelettiques/statistiques.html)
- Prix des logiciels comparables : [Voibe — prix Dragon 2026](https://www.getvoibe.com/resources/dragon-pricing/), [LumeVoice — prix Dragon](https://lumevoice.com/blog/dragon-pricing/), [AskSARA — Tobii Communicator 5](https://livingmadeeasy.org.uk/category/communicating/communication-devices/communication-apps-and-software/product/communicator-5)
- Conversion freemium : [Lenny's Newsletter](https://lennysnewsletter.com/p/what-is-a-good-free-to-paid-conversion), [Userpilot](https://userpilot.com/blog/freemium-saas/), [Lago](https://getlago.com/blog/freemium-pricing)
- Analyse concurrentielle de Gestura : [analyse_positionnement.md](analyse_positionnement.md)
