import random
from pathlib import Path

import pygame


WIDTH = 1100
HEIGHT = 320
GROUND_Y = 260
FPS = 60
GRAVITY = 0.9

ACTION_NAMES = {0: "NEUTRAL", 1: "JUMP", 2: "DUCK"}
OBSTACLE_ENCODING = {
    "CACTUS": 0,
    "BIRD_LOW": 1,
    "BIRD_MID": 2,
    "BIRD_HIGH": 3,
}
FEATURE_NAMES = [
    "distance_x",
    "vitesse_jeu",
    "time_to_impact",
    "largeur_obstacle",
    "pos_y_obstacle",
    "type_obstacle_label",
    "is_jumping",
]


class Robot:
    def __init__(self) -> None:
        self.x = 100
        self.width = 44
        self.stand_height = 48
        self.duck_height = 30
        self.y = GROUND_Y - self.stand_height
        self.vel_y = 0.0
        self.on_ground = True
        self.is_ducking = False

    @property
    def height(self) -> int:
        return self.duck_height if self.is_ducking and self.on_ground else self.stand_height

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, int(self.y), self.width, self.height)

    def jump(self) -> None:
        if self.on_ground:
            self.vel_y = -16.0
            self.on_ground = False

    def update(self, duck: bool) -> None:
        self.is_ducking = duck
        if self.on_ground:
            self.y = GROUND_Y - self.height
            self.vel_y = 0.0
        self.vel_y += GRAVITY
        self.y += self.vel_y
        if self.y + self.height >= GROUND_Y:
            self.y = GROUND_Y - self.height
            self.vel_y = 0.0
            self.on_ground = True


class Obstacle:
    def __init__(self, obstacle_type: str, x: float) -> None:
        self.type_name = obstacle_type
        self.x = x
        if obstacle_type == "CACTUS":
            self.width = random.choice([24, 32, 42])
            self.height = random.choice([42, 50, 58])
            self.y = GROUND_Y - self.height
        else:
            self.width = 46
            self.height = 30
            self.y = {
                "BIRD_LOW": GROUND_Y - 34,
                "BIRD_MID": GROUND_Y - 68,
                "BIRD_HIGH": GROUND_Y - 102,
            }[obstacle_type]

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, speed: float) -> None:
        self.x -= speed


class LogisticRegressionController:
    def __init__(self, model_path: Path) -> None:
        try:
            import joblib
        except ImportError as error:
            raise RuntimeError(
                "Dépendances absentes. Lancez : python -m pip install -r requirements.txt"
            ) from error

        if not model_path.is_file():
            raise FileNotFoundError(f"Modèle logistique introuvable : {model_path}")

        self.model = joblib.load(model_path)
        model_features = getattr(self.model, "feature_names_in_", None)
        self.feature_names = list(model_features) if model_features is not None else None
        self.feature_count = getattr(self.model, "n_features_in_", 6)
        if self.feature_count == len(FEATURE_NAMES) - 1:
            self.feature_order = FEATURE_NAMES[:-1]
        elif self.feature_count == len(FEATURE_NAMES):
            self.feature_order = FEATURE_NAMES
        else:
            raise ValueError(
                f"Le modèle attend {self.feature_count} features ; "
                f"le jeu sait en fournir {len(FEATURE_NAMES)} ou {len(FEATURE_NAMES) - 1}."
            )

    def predict(self, features: dict[str, float | int]) -> tuple[str, float | None]:
        names = self.feature_names or self.feature_order
        values = [features[name] for name in names]
        prediction = int(self.model.predict([values])[0])
        if prediction not in ACTION_NAMES:
            raise ValueError(f"Classe prédite inconnue : {prediction} (attendu : 0, 1 ou 2)")

        confidence = None
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba([values])[0]
            classes = list(self.model.classes_)
            confidence = float(probabilities[classes.index(prediction)])
        return ACTION_NAMES[prediction], confidence


def spawn_obstacle() -> Obstacle:
    kind = random.choices(
        ["CACTUS", "BIRD_LOW", "BIRD_MID", "BIRD_HIGH"],
        weights=[0.55, 0.20, 0.17, 0.08],
    )[0]
    return Obstacle(kind, WIDTH + random.randint(0, 120))


def draw_robot(screen: pygame.Surface, robot: Robot) -> None:
    body = robot.rect
    pygame.draw.rect(screen, (42, 119, 128), body, border_radius=5)
    pygame.draw.rect(
        screen,
        (157, 224, 203),
        (body.right - 15, body.y + min(body.height // 3, 13), 7, 5),
        border_radius=2,
    )
    pygame.draw.line(screen, (42, 119, 128), (robot.x + 9, body.y), (robot.x + 9, body.y - 8), 3)
    pygame.draw.circle(screen, (224, 159, 66), (robot.x + 9, body.y - 10), 3)
    leg_y = body.bottom
    pygame.draw.line(screen, (30, 72, 79), (robot.x + 8, leg_y), (robot.x + 5, leg_y + 7), 4)
    pygame.draw.line(
        screen,
        (30, 72, 79),
        (body.right - 8, leg_y),
        (body.right - 5, leg_y + 7),
        4,
    )


def main() -> None:
    model_path = Path(__file__).resolve().parent / "models" / "dino_model_logreg.pkl"
    controller = LogisticRegressionController(model_path)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino Run - Robot autonome (regression logistique)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)

    robot = Robot()
    obstacles: list[Obstacle] = []
    score = 0
    speed = 8.0
    spawn_timer = 0
    running = True
    crashed = False

    while running:
        clock.tick(FPS)
        score += 1
        speed = min(23.0, 8.0 + score / 1200)
        spawn_timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if spawn_timer >= random.randint(45, 95):
            obstacles.append(spawn_obstacle())
            spawn_timer = 0

        for obstacle in obstacles:
            obstacle.update(speed)
        obstacles = [obstacle for obstacle in obstacles if obstacle.x + obstacle.width >= 0]

        upcoming = [obstacle for obstacle in obstacles if obstacle.x + obstacle.width >= robot.x]
        nearest = min(upcoming, key=lambda obstacle: obstacle.x) if upcoming else None
        action = "NEUTRAL"
        confidence = None
        if nearest is not None:
            distance = max(nearest.x - (robot.x + robot.width), 0.0)
            features = {
                "distance_x": round(distance, 3),
                "vitesse_jeu": round(speed, 3),
                "time_to_impact": round(distance / speed, 4),
                "largeur_obstacle": nearest.width,
                "pos_y_obstacle": int(nearest.y),
                "type_obstacle_label": OBSTACLE_ENCODING[nearest.type_name],
                "is_jumping": int(not robot.on_ground),
            }
            action, confidence = controller.predict(features)

        if action == "JUMP":
            robot.jump()
        robot.update(duck=action == "DUCK")

        if any(robot.rect.colliderect(obstacle.rect) for obstacle in obstacles):
            crashed = True
            running = False

        screen.fill((247, 247, 247))
        pygame.draw.line(screen, (80, 80, 80), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        draw_robot(screen, robot)
        for obstacle in obstacles:
            color = (0, 140, 0) if obstacle.type_name == "CACTUS" else (170, 30, 30)
            pygame.draw.rect(screen, color, obstacle.rect)

        confidence_text = f"{confidence:.0%}" if confidence is not None else "n/a"
        hud = f"score={score}  vitesse={speed:.2f}  action={action}  confiance={confidence_text}"
        screen.blit(font.render(hud, True, (20, 20, 20)), (20, 20))
        screen.blit(font.render("BOT LOGREG ACTIF | fermer la fenetre pour quitter", True, (20, 20, 20)), (20, 48))
        pygame.display.flip()

    pygame.quit()
    result = "collision" if crashed else "fermeture"
    print(f"Partie terminee ({result}). Score : {score}")


if __name__ == "__main__":
    main()