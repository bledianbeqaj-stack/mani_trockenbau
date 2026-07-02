"""Bauarbeiter-Runner mit Pygame."""

from __future__ import annotations

import random
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).parent
ASSETS = BASE_DIR / "assets" / "game"
DATA = BASE_DIR / "data"
WIDTH, HEIGHT = 1000, 420
GROUND = 330
FPS = 60
GRAVITY = 0.85
JUMP_SPEED = -15
START_SPEED = 8
OBSTACLE_SIZES = [(82, 54), (92, 60), (54, 76), (118, 52), (92, 82), (74, 54), (115, 95)]


def load_image(name: str, size: tuple[int, int]) -> pygame.Surface:
    """Lädt ein Bild und skaliert es auf eine feste Größe."""
    image = pygame.image.load(str(ASSETS / name)).convert_alpha()
    return pygame.transform.smoothscale(image, size)


class Score:
    """Verwaltet Punkte und gespeicherten Highscore."""

    def __init__(self, path: Path = DATA / "highscore.txt") -> None:
        self.path = path
        self.points = 0
        self.highscore = self.load()

    def load(self) -> int:
        """Lädt den gespeicherten Highscore aus einer Textdatei."""
        try:
            return int(self.path.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, ValueError):
            return 0

    def update(self) -> None:
        """Erhöht den Score und aktualisiert den Highscore."""
        self.points += 1
        self.highscore = max(self.highscore, self.points)

    def reset_points(self) -> None:
        """Setzt nur den aktuellen Punktestand zurück."""
        self.points = 0

    def save(self) -> None:
        """Speichert den besten Punktestand dauerhaft."""
        DATA.mkdir(exist_ok=True)
        self.path.write_text(str(self.highscore), encoding="utf-8")


class Player:
    """Bauarbeiter mit Lauf-, Sprung- und Trefferbild."""

    def __init__(self) -> None:
        # Die Spielfigur nutzt unterschiedliche Bilder für Start, Laufen, Springen und Treffer.
        self.run_images = [load_image("worker_run1.png", (76, 88)), load_image("worker_run2.png", (76, 88))]
        self.start_image = load_image("worker_start.png", (76, 88))
        self.jump_image = load_image("worker_jump.png", (68, 82))
        self.hurt_image = load_image("worker_hurt.png", (92, 92))
        self.x, self.y, self.vy = 90, GROUND - 88, 0.0
        self.jumping = self.dead = False
        self.frame = 0
        self.rect = pygame.Rect(self.x + 14, self.y + 10, 48, 74)

    def jump(self) -> None:
        """Löst einen Sprung aus, wenn die Figur am Boden ist."""
        if not self.jumping and not self.dead:
            self.vy = JUMP_SPEED
            self.jumping = True

    def update(self) -> None:
        """Aktualisiert Sprungbewegung, Animation und Kollisionsrechteck."""
        if self.jumping:
            self.vy += GRAVITY
            self.y += self.vy
            if self.y >= GROUND - 88:
                self.y, self.vy, self.jumping = GROUND - 88, 0, False
        self.frame = (self.frame + 1) % 18
        self.rect.topleft = (self.x + 14, int(self.y) + 10)

    def image(self, started: bool) -> pygame.Surface:
        """Wählt abhängig vom Zustand das passende Bild."""
        if self.dead:
            return self.hurt_image
        if self.jumping:
            return self.jump_image
        if not started:
            return self.start_image
        return self.run_images[0 if self.frame < 9 else 1]

    def draw(self, screen: pygame.Surface, started: bool) -> None:
        """Zeichnet die Figur auf den Bildschirm."""
        img = self.image(started)
        y_offset = 6 if self.jumping else 0
        screen.blit(img, (self.x, int(self.y) + y_offset))


class Obstacle:
    """Ein Hindernis, das nach links läuft."""

    def __init__(self, image: pygame.Surface, speed: int) -> None:
        self.image = image
        self.speed = speed
        self.rect = self.image.get_rect()
        self.rect.x = WIDTH + random.randint(40, 190)
        self.rect.bottom = GROUND + 3
        self.hitbox = self.rect.inflate(-12, -10)

    def update(self) -> None:
        """Bewegt das Hindernis und aktualisiert die Hitbox."""
        self.rect.x -= self.speed
        self.hitbox.topleft = (self.rect.x + 6, self.rect.y + 5)

    def draw(self, screen: pygame.Surface) -> None:
        """Zeichnet das Hindernis."""
        screen.blit(self.image, self.rect)


class Game:
    """Steuert Spielzustand, Kollision, Punkte und Zeichnen."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Bauarbeiter Runner")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.score = Score()

        # Die Hindernisse werden einmal geladen und später zufällig ausgewählt.
        self.obstacle_images = [load_image(f"obstacle{i}.png", size) for i, size in enumerate(OBSTACLE_SIZES, 1)]
        self.reset()

    def reset(self) -> None:
        """Setzt das Spiel für einen neuen Versuch zurück."""
        self.player = Player()
        self.obstacles: list[Obstacle] = []
        self.started = self.game_over = False
        self.score.reset_points()
        self.speed, self.spawn_timer = START_SPEED, 80

    def handle_events(self) -> bool:
        """Verarbeitet Tastatur- und Schließen-Ereignisse."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self.reset()
                    self.started = True
                    self.player.jump()
        return True

    def update(self) -> None:
        """Aktualisiert Spieler, Hindernisse, Kollision und Punkte."""
        if not self.started or self.game_over:
            return
        self.player.update()
        self.spawn_timer -= 1

        # Neue Hindernisse erscheinen in zufälligen Abständen.
        if self.spawn_timer <= 0:
            self.obstacles.append(Obstacle(random.choice(self.obstacle_images), self.speed))
            self.spawn_timer = random.randint(75, 135)

        for obstacle in self.obstacles:
            obstacle.speed = self.speed
            obstacle.update()
        self.obstacles = [o for o in self.obstacles if o.rect.right > 0]

        # Bei einer Kollision endet die Runde und der Highscore wird gespeichert.
        if any(self.player.rect.colliderect(o.hitbox) for o in self.obstacles):
            self.player.dead = self.game_over = True
            self.score.save()
            return

        self.score.update()
        if self.score.points % 320 == 0:
            self.speed += 1

# RGB-Farben: Zeichnen Hintergrund, Bodenlinien und Textfarben.
    def draw(self) -> None:
        """Zeichnet Boden, Hindernisse, Spieler und Punktestand."""
        self.screen.fill((247, 247, 247))
        pygame.draw.line(self.screen, (45, 45, 45), (0, GROUND + 4), (WIDTH, GROUND + 4), 3)
        pygame.draw.line(self.screen, (180, 180, 180), (0, GROUND + 16), (WIDTH, GROUND + 16), 1)
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        self.player.draw(self.screen, self.started)

        # HUD mit aktuellem Punktestand und gespeichertem Highscore.
        self.screen.blit(self.font.render(f"Punkte: {self.score.points}", True, (20, 20, 20)), (WIDTH - 180, 25))
        self.screen.blit(self.font.render(f"Highscore: {self.score.highscore}", True, (20, 20, 20)), (WIDTH - 220, 60))
        if not self.started:
            text = self.font.render("Leertaste zum Starten und Springen", True, (20, 20, 20))
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 120)))
        if self.game_over:
            text = self.font.render("Getroffen! Leertaste für Neustart", True, (20, 20, 20))
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, 120)))
        pygame.display.flip()

# Klassischer Game-Loop: Events verarbeiten, Logik aktualisieren, Bild zeichnen.
    def run(self) -> None:
        """Startet die Hauptschleife des Spiels."""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self.score.save()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
