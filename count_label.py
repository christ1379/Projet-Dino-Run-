import csv
from collections import Counter

csv_path = "dataset/dino_run_logs.csv"

try:
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        compteur_actions = Counter()
        compteur_obstacles = Counter()
        total_lignes = 0
        
        for row in reader:
            compteur_actions[row['action_label']] += 1
            compteur_obstacles[row['type_obstacle']] += 1
            total_lignes += 1
            
    label_mapping = {"0": "Neutre (0)", "1": "Saut (1)", "2": "Baisse (2)"}
    
    print("=== RÉPARTITION DES ACTIONS ===")
    for val in sorted(compteur_actions.keys()):
        count = compteur_actions[val]
        nom_label = label_mapping.get(val, f"Inconnu ({val})")
        pourcentage = (count / total_lignes) * 100
        print(f"{nom_label:<12} : {count:>5} lignes ({pourcentage:.1f}%)")
        
    print("\n=== RÉPARTITION DES OBSTACLES ===")
    # Tri par quantité décroissante
    for obstacle, count in compteur_obstacles.most_common():
        pourcentage = (count / total_lignes) * 100
        print(f"{obstacle:<12} : {count:>5} lignes ({pourcentage:.1f}%)")
        
    print(f"\nTotal des lignes : {total_lignes}")

except FileNotFoundError:
    print(f"Erreur : Le fichier {csv_path} est introuvable.")