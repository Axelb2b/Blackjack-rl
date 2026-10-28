# Analyse du projet Blackjack AI — note pour portfolio et entretiens

Cette note explique ce que démontre le projet, les simulations que nous avons exécutées et les limites identifiées. Elle est distincte du code original.

## 1. Problème et démarche

L'objectif est d'étudier des stratégies de blackjack à partir d'un environnement simulé : implémentation d'un moteur de règles et d'un sabot, élaboration de stratégies de référence, puis apprentissage et comparaison sur des manches simulées.

Le dépôt contient **deux approches d'apprentissage distinctes** :

- Un agent de **Q-learning tabulaire** et son environnement simplifié (`Proj/src/rl/`). Celui-ci ne propose que `hit` et `stand`.
- Un agent **Monte Carlo de première action** (`train_q_learning.py`, nom historique trompeur). Il estime la récompense finale de la première décision — `hit`, `stand`, `double` ou `split` — avec une politique fixe pour terminer la manche après cette décision. C'est ce second modèle qui est évalué dans les résultats ci-dessous.

### Représentation d'état de l'agent MC

`(total joueur, carte visible du croupier, main souple ou non, rang éventuel de la paire)`.

Le modèle sélectionné provient de l'archive et contient **340 entrées d'état**, après un entraînement enregistré à **1 million d'épisodes**. Cela ne signifie pas que les 340 états ont été observés le même nombre de fois, ni que toutes les décisions ont la même fiabilité statistique.

## 2. Benchmark exécuté

Deux séries de **200 000 manches par politique**, avec `seed=42` puis `seed=2026`. Les quatre stratégies sont testées avec les règles par défaut et le même nombre de manches. Les trajectoires et décisions ne sont pas appariées exactement d'une politique à l'autre.

| Stratégie | Payout net moyen par manche | IC 95 % approximatif |
|---|---:|---:|
| Aléatoire | −0,44888 | [−0,45296 ; −0,44481] |
| Naïve | −0,05074 | [−0,05396 ; −0,04752] |
| Référence basée sur des règles | −0,00378 | [−0,00737 ; −0,00019] |
| Agent Monte Carlo | −0,00481 | [−0,00829 ; −0,00133] |

**Conclusion prudente :** l'agent MC présente des performances voisines de la stratégie de référence dans cet environnement. Ces deux méthodes dépassent largement la politique aléatoire. La différence moyenne entre MC et référence est trop faible, au regard de l'incertitude de simulation, pour parler d'une victoire convaincante de l'une sur l'autre.

Une unité représente **une mise initiale**. Le payout peut être ±2 avec un double ou augmenter en valeur absolue à la suite d'un split. Les résultats **ne sont pas** des taux de victoire ni des rendements réels garantis.

Les intervalles sont une approximation gaussienne sur des manches traitées comme indépendantes. En réalité, plusieurs manches successives partagent le même sabot : il faudra à terme utiliser des réplications par sabot ou par session. Les données sources sont disponibles dans `reports/`.

## 3. Trois limites techniques intéressantes

### Apprentissage limité à la première décision

Le modèle MC apprend `Q(s0, a0)` pour une décision initiale, puis laisse une politique fixe terminer les mains. En simulation, la classe `RLStrategy` peut à nouveau choisir dans la table après une première action `hit` ou après un split. Cela **n'est pas exactement la politique évaluée à l'entraînement**.

**Piste :** créer un wrapper *first action + continuation fixe*, puis le comparer à un vrai agent séquentiel qui apprend chaque décision.

### Distributions de cartes différentes

Pendant l'entraînement MC, chaque épisode démarre souvent avec un sabot neuf et sa seed. Pendant l'évaluation, plusieurs manches se déroulent avec le même sabot jusqu'à la cut card. C'est un écart de distribution qui peut changer les estimations de gain.

**Piste :** imposer des règles de sabot cohérentes et évaluer sur plusieurs séries indépendantes.

### Règles partiellement codées

Plusieurs paramètres existent dans `BlackjackRules` sans être encore appliqués de bout en bout. Deux tests attendus en échec montrent l'absence de restriction `double_on_hard_9_10_11_only` et le cas des As splittés qui ne devraient recevoir qu'une carte. Surrender et assurance ne sont pas pris en charge dans les actions jouables.

**Piste :** vérifier systématiquement l'application de chaque règle avant d'utiliser le simulateur pour conclure à l'optimalité des stratégies.

## 5. Quelques décisions concrètes

| Main | Croupier | Référence | Monte Carlo |
|---|---|---|---|
| 10, 2 | 4 | Stand | Stand |
| 6, 5 | 6 | Double | Double |
| A, A | 6 | Split | Split |
| 10, 6 | 10 | Hit | Stand |
| 8, 8 | 6 | Split | Stand |
| A, 7 | 3 | Double | Hit |

Les désaccords sont utiles à analyser : états rarement visités, estimation bruitée, qualité de la représentation, ou différence entre la politique d'entraînement et celle de test. Les choix de la référence ne constituent pas une preuve d'optimalité.

## 6. Formulation adaptée à un CV

> Conception d'un simulateur de Blackjack en Python et développement d'agents d'apprentissage tabulaire (Q-learning, Monte Carlo) ; entraînement d'une politique sur 1 million d'épisodes et comparaison de quatre stratégies sur 400 000 manches par politique, avec tests, analyse des performances et reproductibilité.

Ne pas écrire « agent battant la stratégie optimale » : ce n'est pas démontré par les mesures.

## 7. Pour reproduire

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
python3 -m scripts.benchmark --rounds 200000 --seed 42 --output reports/benchmark_200k_seed42.json
python3 -m scripts.benchmark --rounds 200000 --seed 2026 --output reports/benchmark_200k_seed2026.json
python3 -m scripts.summarize_benchmarks reports/benchmark_200k_seed42.json reports/benchmark_200k_seed2026.json
```

Les tests ajoutés donnent **10 réussites et 2 échecs attendus (`xfail`)**. Les scripts d'expérimentation anciens peuvent exiger des calculs beaucoup plus longs et ne sont pas tous soumis à cette suite de tests.
