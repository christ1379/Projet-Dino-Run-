# Projet : Conception d'un Bot Autonome pour "Dino Run"

L'objectif est de créer une intelligence artificielle capable de surpasser les réflexes humains sur le célèbre jeu du Dino de Chrome, en utilisant des modèles de Machine Learning entraînés par apprentissage supervisé.

## 1. Comprendre l'Environnement : Le Jeu Dino Run

Le "Dino Run" est un jeu de type infinite runner à défilement latéral.

- **Objectif** : Parcourir la plus longue distance possible sans percuter d'obstacle.
- **Mécanique** : La vitesse du jeu augmente progressivement, réduisant le temps de réaction du joueur.
- **Commandes** : Le joueur peut Sauter (Flèche Haut), Se baisser (Flèche Bas) ou Rester neutre.

### Les Obstacles et Actions Associées

Pour que le bot soit efficace, il doit identifier la nature du danger pour choisir la bonne parade :

| Obstacle | Description | Action Attendue |
|---|---|---|
| Cactus | Obstacles au sol de tailles variables. | Sauter |
| Oiseau Bas | Vole au ras du sol. | Sauter |
| Oiseau Milieu | Vole à hauteur de la tête du Dino. | Se baisser |
| Oiseau Haut | Vole au-dessus du Dino. | Rien faire (économise l'énergie/risque) |

## 2. Capture des Logs : Anatomie des "Features"

C'est l'étape la plus déterminante. Pour chaque instant du jeu, nous allons enregistrer un "cliché" numérique de la situation. Voici les variables choisies et la raison de leur présence :

- **distance_x (Distance horizontale)** : C'est l'indicateur d'urgence. Plus elle est petite, plus l'action doit être immédiate.
- **vitesse_jeu** : Cruciale, car un cactus situé à 100 pixels ne demande pas le même timing si le jeu va à 5 km/h ou à 20 km/h.
- **largeur_obstacle** : Permet au modèle de savoir s'il doit effectuer un saut long ou court (très utile pour les groupes de cactus).
- **pos_y_obstacle (Altitude)** : C'est la variable qui permet de distinguer les trois types d'oiseaux et les cactus. Sans elle, le bot est "aveugle" à la hauteur du danger.
- **type_obstacle (Catégorie)** : Aide les modèles d'arbres à créer des règles logiques simples (ex: "Si Oiseau ET Hauteur=Milieu alors Duck").

> **Note** : La "Target" (y) enregistrée sera l'action effectuée (0, 1 ou 2) face à ces variables.

## 3. Préparation des Données (Feature Engineering)

On ne donne pas les données brutes telles quelles aux modèles :

- **Calcul du Temps d'Impact** : Création d'une variable $T_{impact} = \frac{distance\_x}{vitesse\_jeu}$. C'est la "Golden Feature" qui simplifie énormément le travail des algorithmes.
- **Encodage** : Utilisation du One-Hot Encoding pour la Régression Logistique (pour éviter une hiérarchie artificielle entre les obstacles) et du Label Encoding pour les modèles d'arbres.
- **Scaling** : Normalisation des données pour que la vitesse et la distance soient sur la même échelle (essentiel pour la LogReg).

## 4. Compétition de Modèles (Training & Benchmark)

Nous allons entraîner et comparer deux "cerveaux" différents pour déterminer le plus apte :

1. **Régression Logistique** : Pour tester la séparation linéaire simple.
2. **Modèle KNN (K-Nearest Neighbors)** : Pour prédire l'action à partir des situations les plus proches observées.

## 5. Inférence : Le Bot en Action

Une fois le meilleur modèle identifié (via le meilleur score de précision et de rappel), nous l'intégrons dans une boucle de contrôle :

1. Lecture des paramètres de l'écran en temps réel.
2. Prédiction de l'action par le modèle choisi.
3. Exécution de la touche clavier correspondante.

## Lancer le bot

Le robot utilise le modèle KNN `dino_model_knn.pkl` placé à la racine du projet. Installe les dépendances puis lance le jeu :

```powershell
python -m pip install -r requirements.txt
python dino_run_robot_knn.py
```

Le robot joue automatiquement et affiche son action ainsi que la confiance du modèle. Ferme la fenêtre pour quitter. Pour enregistrer de nouvelles données de jeu manuellement, lance `python dino_env_logger.py`.
