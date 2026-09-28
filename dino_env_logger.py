import csv
import random
from pathlib import Path

import pygame


WIDTH = 1100
HEIGHT = 320
GROUND_Y = 260
FPS = 60
GRAVITY = 0.9
NEUTRAL_LOG_EVERY = 6
JUMPING_LOG_EVERY = 2
ACTION_OVERSAMPLE_FACTOR = 3
HIGH_URGENCY_TTI = 1.1


ACTION_ENCODING = {
    "NEUTRAL": 0,
    "JUMP": 1,
    "DUCK": 2,
}


OBSTACLE_ENCODING = {
    "CACTUS": 0,
    "BIRD_LOW": 1,
    "BIRD_MID": 2,
    "BIRD_HIGH": 3,
}


class Dino:
    def __init__(self) -> None:
        self.x = 100
        self.stand_height = 48
        self.duck_height = 30
        self.width = 44
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

    def update(self, want_duck: bool) -> None:
        self.is_ducking = want_duck
        self.vel_y += GRAVITY
        self.y += self.vel_y

        dino_bottom = self.y + self.height
        if dino_bottom >= GROUND_Y:
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
            bird_y = {
                "BIRD_LOW": GROUND_Y - 34,
                "BIRD_MID": GROUND_Y - 68,
                "BIRD_HIGH": GROUND_Y - 102,
            }
            self.y = bird_y[obstacle_type]

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, game_speed: float) -> None:
        self.x -= game_speed

    def is_off_screen(self) -> bool:
        return self.x + self.width < 0


class DataLogger:
    HEADER = [
        "distance_x",
        "vitesse_jeu",
        "time_to_impact",
        "largeur_obstacle",
        "pos_y_obstacle",
        "type_obstacle",
        "type_obstacle_label",
        "is_jumping",
        "action_label",
    ]

    def __init__(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a"
        write_header = False

        if not output_path.exists() or output_path.stat().st_size == 0:
            write_header = True
        else:
            with output_path.open("r", newline="", encoding="utf-8") as existing_file:
                reader = csv.reader(existing_file)
                existing_header = next(reader, [])
            if existing_header != self.HEADER:
                legacy_path = output_path.with_name(f"{output_path.stem}_legacy{output_path.suffix}")
                output_path.replace(legacy_path)
                mode = "w"
                write_header = True

        self.file = output_path.open(mode, newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        if write_header:
            self.writer.writerow(self.HEADER)
        self.rows = 0

    def log(self, feature_row: list[float | int | str]) -> None:
        self.writer.writerow(feature_row)
        self.rows += 1

    def close(self) -> None:
        self.file.close()


def spawn_obstacle() -> Obstacle:
    kind = random.choices(
        population=["CACTUS", "BIRD_LOW", "BIRD_MID", "BIRD_HIGH"],
        weights=[0.55, 0.20, 0.17, 0.08],
    )[0]
    return Obstacle(kind, WIDTH + random.randint(0, 120))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino Environment Logger")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)

    dino = Dino()
    obstacles: list[Obstacle] = []
    logger = DataLogger(Path("dataset") / "dino_run_logs.csv")

    score = 0
    game_speed = 8.0
    spawn_timer = 0
    frame_count = 0
    running = True

    while running:
        clock.tick(FPS)
        score += 1
        frame_count += 1
        game_speed = min(23.0, 8.0 + score / 1200)
        spawn_timer += 1

        action = "NEUTRAL"
        want_duck = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_SPACE):
                    dino.jump()
                    action = "JUMP"

        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN]:
            want_duck = True
            if action == "NEUTRAL":
                action = "DUCK"

        dino.update(want_duck=want_duck)

        if spawn_timer >= random.randint(45, 95):
            obstacles.append(spawn_obstacle())
            spawn_timer = 0

        for obstacle in obstacles:
            obstacle.update(game_speed)

        obstacles = [obs for obs in obstacles if not obs.is_off_screen()]

        nearest = None
        nearest_dist = float("inf")
        for obs in obstacles:
            distance = obs.x - (dino.x + dino.width)
            if distance >= -obs.width and distance < nearest_dist:
                nearest = obs
                nearest_dist = distance

        if nearest is not None:
            distance_x = round(max(nearest_dist, 0.0), 3)
            time_to_impact = round(distance_x / game_speed, 4) if game_speed > 0 else 0.0
            is_jumping = int(not dino.on_ground)
            row = [
                distance_x,
                round(game_speed, 3),
                time_to_impact,
                nearest.width,
                int(nearest.y),
                nearest.type_name,
                OBSTACLE_ENCODING[nearest.type_name],
                is_jumping,
                ACTION_ENCODING[action],
            ]

            should_log = False
            repetitions = 1
            if action != "NEUTRAL":
                should_log = True
                repetitions = ACTION_OVERSAMPLE_FACTOR
            elif is_jumping == 1:
                should_log = frame_count % JUMPING_LOG_EVERY == 0
            elif time_to_impact <= HIGH_URGENCY_TTI:
                should_log = True
            else:
                should_log = frame_count % NEUTRAL_LOG_EVERY == 0

            if should_log:
                for _ in range(repetitions):
                    logger.log(row)

        for obs in obstacles:
            if dino.rect.colliderect(obs.rect):
                running = False
                break

        screen.fill((247, 247, 247))
        pygame.draw.line(screen, (80, 80, 80), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        pygame.draw.rect(screen, (45, 45, 45), dino.rect)

        for obs in obstacles:
            color = (0, 140, 0) if obs.type_name == "CACTUS" else (170, 30, 30)
            pygame.draw.rect(screen, color, obs.rect)

        hud = (
            f"score={score}  speed={game_speed:.2f}  rows={logger.rows}  "
            f"y_label={ACTION_ENCODING[action]}"
        )
        screen.blit(font.render(hud, True, (20, 20, 20)), (20, 20))
        screen.blit(
            font.render("UP/SPACE=jump | DOWN=duck | close window=save+exit", True, (20, 20, 20)),
            (20, 48),
        )
        pygame.display.flip()

    logger.close()
    pygame.quit()
    print(f"Saved {logger.rows} rows to dataset/dino_run_logs.csv")


if __name__ == "__main__":
    main()
