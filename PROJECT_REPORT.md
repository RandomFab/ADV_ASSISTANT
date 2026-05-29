# Rapport de conduite de projet — AI Engineering

## SteelBot / ADV_ASSISTANT — Agent ADV intelligent pour l'industrie métallurgique

> **Auteur :** Fabien BARDOUIL
> **Formation :** AI Engineer — projet de fin de formation
> **Dépôt :** `RandomFab/ADV_ASSISTANT` — version livrée `v1.0.0`
> **Période de réalisation :** 25/05/2026 → 29/05/2026
> **Public cible de la démonstration :** direction de l'entreprise

---

## 1. Contexte et analyse des besoins

### 1.1 Présentation (organisation et contexte)

Le projet s'inscrit dans le secteur de la **transformation métallurgique** : une entreprise de taille intermédiaire qui produit et commercialise des coils (bobines d'acier, d'inox, d'aluminium), des tubes soudés et des tôles découpées. L'activité repose sur des opérations de refendage et de parachèvement, avec des références produits définies par leur nuance (S235, S355, 304, 316L…), leur épaisseur et, pour les tubes, leur diamètre.

L'**Administration des Ventes (ADV)** est au cœur de la relation client : suivi des bons de commande (BDC), des bons de livraison (BL), des délais de fabrication, des niveaux de stock et des non-conformités (réclamations). Les commerciaux et l'ADV sollicitent en permanence le système d'information pour répondre aux clients : « où en est ma commande ? », « a-t-on du stock ? », « quel est le délai ? ».

**Niveau de maturité IA / MLOps :** faible à inexistant au démarrage. L'entreprise dispose d'un ERP « métier » classique mais n'a pas d'usage opérationnel de l'IA générative, ni de chaîne MLOps. Le projet vise donc à la fois à démontrer une valeur métier concrète **et** à poser des fondations d'industrialisation (conteneurisation, CI/CD, monitoring) crédibles aux yeux de la direction.

**Contraintes structurantes :**
- **Sécurité / confidentialité des données :** les données ADV (clients, prix, marges implicites via les montants de commande) sont sensibles. Le POC s'appuie volontairement sur des **données synthétiques** générées localement, sans jamais exposer de données réelles.
- **Infrastructure :** environnement Windows côté poste de développement ; cible de déploiement conteneurisée (Docker) pour garantir la reproductibilité.
- **Scalabilité :** le besoin immédiat est un POC mono-instance ; l'architecture doit néanmoins rester extensible (ajout d'outils, voire d'un second serveur connecté à l'ERP réel).
- **Coût d'inférence :** l'usage d'un LLM via API a un coût récurrent à maîtriser.

### 1.2 Collecte et analyse du besoin métier

**Parties prenantes impliquées :**
- **Métier :** direction commerciale, équipe ADV, commerciaux (utilisateurs finaux, expression du besoin).
- **IT / SI :** responsable de l'ERP et de l'infrastructure (contraintes d'intégration et de sécurité).
- **Direction générale :** commanditaire de la démonstration, juge de la valeur.

**Recueil du besoin :** le besoin a été cadré à partir des cas d'usage récurrents de l'ADV, traduits en cinq questions types qui constituent le fil conducteur du POC et de la démo :
1. « Où en est la commande CMD-2024-0847 ? » (suivi de commande)
2. « Fais-moi un résumé complet du client Durand Construction » (fiche client à 360°)
3. « A-t-on du coil inox 304 en stock ? » (disponibilité produit)
4. « Quel est le délai de livraison estimé pour cette commande ? » (estimation logistique)
5. « Quelles réclamations en cours pour ce client ? » (qualité / non-conformités)

**Objectif technique et business visé :** mettre à disposition un **assistant conversationnel** capable de répondre instantanément à ces questions en interrogeant lui-même les données, sans que l'utilisateur ait à naviguer dans plusieurs écrans de l'ERP. Le gain attendu est un **gain de temps ADV** et une **réduction de la charge cognitive** sur des recherches répétitives.

**Contraintes réglementaires / éthiques / de sécurité :**
- Pas de données personnelles réelles dans le POC (RGPD respecté par construction grâce aux données synthétiques).
- Exigence d'**anti-hallucination** : l'assistant ne doit jamais inventer un chiffre. Cette contrainte est inscrite dans le *system prompt* (« utilise les outils systématiquement, ne jamais inventer ») et garantie par une température LLM fixée à 0.
- Secret commercial : les données sensibles ne transitent que vers l'API du fournisseur LLM, point à arbitrer pour une mise en production (hébergement souverain ou modèle on-premise envisageable).

**Hiérarchisation des besoins (matrice impact / effort) :**

| Cas d'usage | Impact métier | Effort technique | Priorité |
| ----------- | ------------- | ---------------- | -------- |
| Suivi de commande (statut) | Élevé | Faible | **P0** |
| Disponibilité stock | Élevé | Faible | **P0** |
| Résumé client 360° (multi-outils) | Élevé | Moyen | **P0** |
| Estimation de délai de livraison | Moyen | Moyen | **P1** |
| Suivi des réclamations | Moyen | Faible | **P1** |

Les cinq cas ont été retenus pour le POC ; ils couvrent à la fois des appels d'outil simples (un seul outil) et des **chaînages d'outils** (résumé client = informations client + réclamations), ce qui permet de démontrer la capacité d'**agent** (et non de simple workflow).

---

## 2. Audit de la solution data existante (ou proposée)

### 2.1 Solution actuelle ou proposée

**Situation de départ :** absence de solution d'IA conversationnelle. Les informations existent dans l'ERP mais leur consultation est manuelle et fragmentée (plusieurs écrans, plusieurs requêtes). Il n'existe ni couche d'accès standardisée pour un LLM, ni outil de self-service intelligent.

**Solution proposée (architecture cible du POC) :** une chaîne complète articulée autour de cinq composants.

```
Commercial / ADV
      │  (navigateur)
      ▼
Interface Streamlit  ── HTTP ──►  API FastAPI (gateway, logging structuré)
                                        │
                                        ▼
                                Agent LLM (LangGraph, pattern ReAct)
                                        │  MCP (Model Context Protocol)
                                        ▼
                          Serveur MCP (FastMCP) — 5 outils métier
                                        │  SQLAlchemy ORM
                                        ▼
                              PostgreSQL (clients, produits,
                              commandes, lignes, réclamations)

Transverse : Monitoring (Evidently + logs JSON) → Alertes GitHub Issues
```

**Outils / technologies retenus :**

| Composant | Technologie |
| --------- | ----------- |
| Agent LLM | LangGraph + LangChain (pattern ReAct via `create_react_agent`) |
| Modèle | `mistral-large-latest` (température 0) |
| Serveur d'outils | FastMCP (implémentation Python de MCP) |
| API / gateway | FastAPI (pattern `lifespan`, middleware de logging) |
| Interface | Streamlit |
| Base de données | PostgreSQL 16 + SQLAlchemy 2.0 (ORM, syntaxe `Mapped[...]`) |
| Génération de données | Faker (locale `fr_FR`), seed déterministe |
| Monitoring | Evidently AI (rapports qualité) + logs JSON Lines |
| Alerting | API GitHub Issues (création automatique) |
| Conteneurisation | Docker (Dockerfile multi-stage) + Docker Compose (4 services) |
| CI/CD | GitHub Actions (lint + build) |
| Tests | pytest (174 tests, SQLite in-memory) |
| Versioning | Git + GitHub, workflow Git Flow, tags SemVer |

### 2.2 Évaluation de l'adéquation aux besoins

**Critères d'analyse :**

| Critère | Évaluation de la solution proposée |
| ------- | ---------------------------------- |
| **Performance** | Latence de quelques secondes par requête simple, jusqu'à 15-20 s sur un chaînage de 3-4 outils. Acceptable pour un usage ADV interactif. |
| **Robustesse** | Gestion des erreurs à chaque couche (sessions SQLAlchemy en `try/finally`, dégradation gracieuse si token GitHub absent, gestion des timeouts côté UI). |
| **Sécurité** | Données synthétiques, secrets en variables d'environnement jamais commitées, ports bindés sur `127.0.0.1` uniquement. |
| **Coût** | Coût d'inférence LLM non négligeable (modèle « large »), à arbitrer en production. |
| **Maintenance** | Code découpé par responsabilité, instance MCP centralisée, schémas Pydantic isolés. |
| **Monitoring** | Logs métier structurés persistés, métriques agrégées, alertes automatiques. |

**Écarts et limites identifiés (assumés pour un POC) :**
- **Pas de mémoire conversationnelle** : chaque question est traitée indépendamment (les questions ADV sont majoritairement autonomes ; amélioration documentée mais non implémentée).
- **Tests sur SQLite in-memory** plutôt que PostgreSQL : tests rapides et isolés, mais SQLite ne reproduit pas à 100 % le comportement de PostgreSQL (types ENUM, `ILIKE`, JSON). Compromis légitime pour un POC, à nommer explicitement.
- **Données synthétiques 2024** : certaines estimations de livraison sur des commandes anciennes renvoient des dates passées — comportement normal sur jeu de données figé.
- **Coût LLM** : choix d'un modèle puissant pour la qualité du raisonnement multi-outils, au prix d'un coût d'inférence supérieur.

**Visualisation des flux :** voir le schéma d'architecture du § 2.1 et du § 3.

---

## 3. Identification d'une solution technique cible

### Comparatif d'approches techniques

| Choix | Option retenue | Alternatives écartées | Justification |
| ----- | -------------- | --------------------- | ------------- |
| **Paradigme d'orchestration** | Agent autonome (LangGraph / ReAct) | Workflow déterministe (if/else codé en dur) | Un agent choisit lui-même quels outils appeler et dans quel ordre ; ajouter un outil ne nécessite pas de modifier le code de l'agent. C'est le différenciateur central du projet. |
| **Connexion LLM ↔ données** | MCP (serveur custom FastMCP) | Function calling « classique » intégré au code | MCP standardise l'exposition des outils, **découvrables au runtime** par le LLM. Architecture extensible : on pourrait brancher un second serveur MCP (ERP réel) sans toucher à l'agent. |
| **Modèle** | `mistral-large-latest` | `mistral-small-latest` | Le « small » exécute les outils mais ne synthétise pas correctement les résultats multi-outils ; le « large » raisonne **et** formule. Fiabilité justifiée par l'usage métier. |
| **Température** | 0 | > 0 | Réponses reproductibles et non créatives — indispensable sur des données chiffrées (commandes, stocks) pour éviter toute hallucination. |
| **API** | FastAPI | Flask, Django REST | Asynchrone natif (adapté à un agent async), doc Swagger auto-générée, validation Pydantic intégrée. |
| **Base de données** | PostgreSQL + SQLAlchemy ORM | SQLite en prod, requêtes SQL brutes | PostgreSQL pour le réalisme « production » ; ORM pour la sécurité (pas d'injection SQL), la lisibilité et les jointures typées. |
| **Conteneurisation** | Docker multi-stage + Compose | Déploiement manuel | « Un seul `docker compose up` et tout marche » : reproductibilité totale, effet démonstratif fort. |
| **Monitoring / alertes** | Evidently + logs JSON + GitHub Issues | Datadog, Prometheus/Grafana, PagerDuty | Stack légère sans infrastructure externe, suffisante pour un POC et déjà « production-aware ». |

### Schéma d'architecture cible

L'architecture est en couches, chaque couche n'ayant qu'une seule responsabilité (séparation des préoccupations) :

1. **Présentation** — Streamlit : zone de chat, panneau « raisonnement de l'agent » (outils appelés, latence), indicateurs de statut, boutons de questions exemples. Aucune logique métier.
2. **Gateway** — FastAPI : endpoints `POST /chat`, `GET /health`, `GET /monitoring/check`, `GET /monitoring/report`. Logging structuré à deux niveaux (HTTP infra dans le terminal, métier dans `interactions.jsonl`).
3. **Raisonnement** — Agent LangGraph : reçoit la question + la description des outils, applique le cycle ReAct (Reason → Act → Observe), choisit et chaîne les outils, synthétise la réponse.
4. **Outils** — Serveur MCP (FastMCP) : 5 outils métier (`get_order_status`, `get_client_info`, `get_stock_level`, `get_delivery_estimate`, `search_reclamations`), chacun interrogeant PostgreSQL via SQLAlchemy avec `joinedload` (anti-N+1).
5. **Données** — PostgreSQL : 5 tables (`Client`, `Produit`, `Commande`, `LigneCommande`, `Reclamation`) peuplées de données synthétiques réalistes (40 clients, 20 produits, 600 commandes saisonnalisées, ~60 réclamations).

**Sécurité de la communication :** secrets en variables d'environnement, communication inter-services par nom de service Docker sur réseau interne, ports exposés uniquement en loopback.

### Méthodologie d'identification, d'évaluation et de priorisation des cas d'usage

L'identification s'est faite par **cartographie des tâches ADV récurrentes** : les questions posées le plus souvent par les commerciaux à l'ADV. Chaque cas a ensuite été évalué selon le couple **valeur métier / effort d'implémentation** (matrice du § 1.2). La priorisation a privilégié les cas à fort impact et faible effort (suivi commande, stock) comme socle, complétés par un cas illustrant le chaînage d'outils (résumé client) pour prouver la dimension « agent ». Le backlog résultant a structuré la roadmap des 8 jours.

---

## 4. Stratégie de mise en œuvre et d'industrialisation

### 4.1 Proposition de démarche projet

**Roadmap de mise en œuvre (8 jalons) :**

| Jour | Phase | Livrable principal | Outils |
| ---- | ----- | ------------------ | ------ |
| J1 | Données | BDD PostgreSQL + modèles SQLAlchemy + seed synthétique | Docker, SQLAlchemy, Faker |
| J2 | Outils | Serveur MCP avec 5 outils métier testés | FastMCP |
| J3 | Agent | Agent LangGraph autonome connecté au MCP | LangGraph, langchain-mcp-adapters |
| J4 | API | API FastAPI + logging structuré JSON | FastAPI, Pydantic |
| J5 | Interface | Front Streamlit conversationnel | Streamlit |
| J6 | Monitoring | Métriques + alertes GitHub Issues + rapport Evidently | Evidently, API GitHub |
| J7 | Industrialisation | Dockerisation multi-services + CI/CD | Docker Compose, GitHub Actions |
| J8 | Livraison | Tests, README, démo, tag `v1.0.0` | pytest, Git/SemVer |

**Découpage par étapes :**
- **Développement** : implémentation couche par couche, du socle données vers l'interface (bottom-up), pour que chaque couche s'appuie sur une fondation déjà validée.
- **Tests** : suite pytest de 174 tests (unitaires sur les outils MCP et le monitoring, fonctionnels sur l'API, les modèles, le middleware et le graphe agent), avec base SQLite in-memory, mock de l'agent (pas d'appel LLM réel) et mock de l'API GitHub.
- **Conteneurisation** : Dockerfile backend multi-stage (base commune, deux targets `mcp` et `fastapi`), Dockerfile frontend dédié.
- **Intégration / orchestration** : Docker Compose à 4 services avec `depends_on` + `condition: service_healthy` pour garantir l'ordre de démarrage `postgres → mcp → fastapi → streamlit`.
- **Déploiement** : un seul `docker compose up --build` depuis un clone frais.
- **Monitoring** : check sur seuils + génération de rapports à la demande via endpoints dédiés.

**Workflow Git :** Git Flow simplifié — `develop` (intégration), `main` (états livrables uniquement), branches `feature/**`. Versionnement en SemVer, première version livrée taguée `v1.0.0` (tag annoté posé sur `main`).

### 4.2 Aide à la prise de décision

**Synthèse des risques et opportunités :**

| Risque | Niveau | Levier d'atténuation |
| ------ | ------ | -------------------- |
| Hallucination du LLM sur des chiffres | Élevé | Température 0 + system prompt anti-hallucination + outils obligatoires ; toute donnée vient de la BDD, jamais du modèle. |
| Coût d'inférence | Moyen | Suivi des tokens dans les logs ; possibilité de basculer sur un modèle intermédiaire ; mise en cache envisageable. |
| Confidentialité (données vers API tierce) | Moyen | POC sur données synthétiques ; pour la prod, arbitrage hébergement souverain / modèle on-premise. |
| Latence sur requêtes complexes | Faible/Moyen | Seuil d'alerte > 10 s ; `joinedload` pour limiter les requêtes SQL. |
| Dérive de qualité non détectée | Moyen | Logs métier + rapports Evidently + alertes automatiques. |
| « Works on my machine » (casse de fichiers, env) | Faible | CI sous Linux qui révèle les écarts d'environnement. |

**Scénarios budgétaires (ordre de grandeur, à affiner) :**
- **Infrastructure** : un POC tourne sur une seule machine / un petit VPS conteneurisé (coût mensuel modeste). Une mise en production multi-utilisateurs nécessiterait un dimensionnement supérieur.
- **Inférence LLM** : coût à l'usage proportionnel au volume de requêtes et au modèle choisi (le « large » coûte sensiblement plus que le « small »).
- **DevOps** : GitHub Actions gratuit dans les quotas d'un dépôt de cette taille.

**Indicateurs de succès (KPI) :**

| Type | KPI | Cible POC |
| ---- | --- | --------- |
| Business | Temps de réponse à une question ADV | < quelques secondes vs navigation manuelle ERP |
| Business | Taux de questions traitées sans intervention humaine | Démontré sur les 5 cas d'usage |
| Technique | Latence moyenne | < 10 s (seuil d'alerte) |
| Technique | Taux d'erreur | < 5 % |
| Technique | Taux de requêtes sans outil appelé | < 20 % (détection d'hallucination/incompréhension) |
| Technique | Couverture de tests | 174 tests, pipeline vert |

**Impacts potentiels et atténuation :** impacts légaux/RGPD (neutralisés en POC par les données synthétiques), biais (faible enjeu sur des données transactionnelles factuelles), faille de sécurité (secrets externalisés, ports en loopback), latence (monitorée). Ces points sont intégrés aux recommandations du § 6.

---

## 5. Contrôle et suivi du projet

### 5.1 Tableau de bord de pilotage

**Indicateurs de suivi projet :**
- **Délais :** roadmap en 8 jalons, chacun avec une checklist de livrables cochée en fin de session (cf. comptes rendus de session).
- **Livrables :** suivis via les états « livrables Jour X » de chaque CR ; tous cochés à la livraison `v1.0.0`.
- **Qualité du code :** lint Ruff (version épinglée), formatage automatique, 174 tests.
- **Qualité des données :** rapports Evidently sur la distribution des latences, la répartition des outils appelés et la longueur des réponses.
- **Performances :** latence et taux d'erreur loggés à chaque interaction.

**Méthodologie de gestion :** approche **itérative et incrémentale** (un jalon = une couche fonctionnelle livrable et démontrable), proche d'un Kanban léger, avec une discipline DevOps (branches, PR, CI, tags). Règle du *good enough* assumée : chaque fonctionnalité est fonctionnelle et démontrable, pas « parfaite ».

### 5.2 Outils et process de suivi

**Outils de suivi en production / exploitation :**
- **Logs métier structurés** : chaque requête `/chat` écrit une ligne JSON dans `interactions.jsonl` (`request_id`, question, outils appelés, latence, statut, longueur de réponse).
- **Agrégation de métriques** (`logger.py`) : latence moyenne/max, taux d'erreur, fréquence des outils, taux de requêtes sans outil, réponses anormalement courtes/longues.
- **Alerting** (`alerting.py`) : dépassement de seuil → création automatique d'une **Issue GitHub** (labels `alert`, `monitoring`, corps avec métriques et recommandations), avec dégradation gracieuse si le token est absent.
- **Rapports Evidently** (`evidently_reports.py`) : rapport HTML de qualité de données généré à la demande via `GET /monitoring/report`.

**Méthodologie de test et d'évaluation :**
- **Tests unitaires** : logique métier des 5 outils MCP (ex. `stock_net == stock_disponible − stock_reserve`), agrégation des métriques, seuils d'alerte, schémas Pydantic.
- **Tests fonctionnels** : modèles SQLAlchemy, endpoints `/chat`, `/health`, `/monitoring/*`, middleware, graphe agent.
- **Infrastructure de test** : SQLite in-memory recréée par test (isolation, rapidité, sans Docker), monkeypatching des sessions, mock de l'agent (zéro coût LLM) et de l'API GitHub.
- **Tests API manuels** : Swagger UI auto-générée sur `/docs`.
- **Validation de bout en bout** : `docker compose up --build` depuis un clone frais.

---

## 6. Conclusion & recommandations

### Résumé des choix clés

SteelBot démontre, sur un périmètre métier réel (l'ADV en métallurgie), qu'un **agent IA autonome** peut interroger lui-même un système de données et répondre en langage naturel. Les choix structurants sont : un **vrai agent** (LangGraph/ReAct) plutôt qu'un workflow figé ; le protocole **MCP** pour exposer des outils découvrables au runtime ; une **chaîne entièrement conteneurisée** lançable en une commande ; et une posture **production-ready** (monitoring, alertes automatiques, CI/CD, 174 tests, versioning SemVer).

### Perspectives d'évolution

- **Mémoire conversationnelle** : ajout de `MemorySaver` + `thread_id` (LangGraph) pour les dialogues multi-tours.
- **RAG sur la documentation technique** : interroger fiches matières, normes et certificats produits.
- **Intégration à l'ERP réel** : brancher un second serveur MCP sur les données de production, sans modifier l'agent.
- **Multimodal** : analyse de photos de défauts pour qualifier les non-conformités.
- **Souveraineté / coût** : évaluer un modèle on-premise ou un hébergement souverain pour traiter des données réelles.

---

## 7. Annexes

- **Dépôt GitHub :** `RandomFab/steelbot-mcp-sales-agent` — version `v1.0.0` ([repo](https://github.com/RandomFab/steelbot-mcp-sales-agent)). 
- **README.md** du projet (pitch, architecture, quickstart `docker compose up`, stack, monitoring, perspectives).
- **Scripts de lancement / démonstration :**
  - `docker compose up --build` (lance les 4 services).
  - `seed.py` (génération des données synthétiques, seed déterministe).
  - Boucles interactives de test : `manual_test_mcp.py`, `manual_test_agent.py`.
- **Diagrammes :** schéma d'architecture cible (§ 2.1 et § 3), graphe d'états de l'agent (cycle ReAct).
- **Suite de tests :** 174 fonctions pytest réparties en `tests/unit/` et `tests/functional/`.
- **Comptes rendus de session :** sessions 01 à 07 (BDD, MCP, agent, API, Streamlit, monitoring, livraison) + CR CI/CD & Tests.
- **Captures d'écran à joindre :** interface Streamlit (chat + panneau raisonnement), rapport Evidently HTML, Issue GitHub d'alerte, pipeline CI/CD vert, Swagger UI.

---