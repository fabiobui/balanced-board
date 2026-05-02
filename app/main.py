import argparse
import math
import threading
import time
from dataclasses import dataclass

import pygame

try:
    import serial
except Exception:
    serial = None


WIDTH, HEIGHT = 1100, 700
CENTER_Y = HEIGHT // 2
BG = (10, 12, 18)
GRID = (38, 45, 62)
PATH_COLOR = (84, 165, 255)
BAND_COLOR = (40, 110, 180)
POINT_OK = (80, 230, 130)
POINT_BAD = (255, 90, 90)
TEXT = (220, 230, 245)


@dataclass
class Pose:
    x: float = 0.0  # roll
    y: float = 0.0  # pitch


@dataclass
class TrainerConfig:
    scenario: str
    speed: float
    amplitude: float
    tolerance: float
    wavelength: float


class SerialReader:
    def __init__(self, port: str, baud: int):
        if serial is None:
            raise RuntimeError("pyserial non installato")
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.pose = Pose()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            try:
                raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                pitch_s, roll_s = raw.split(",")
                pitch = float(pitch_s)
                roll = float(roll_s)
                self.pose.x = max(-20.0, min(20.0, roll)) / 20.0
                self.pose.y = max(-20.0, min(20.0, pitch)) / 20.0
            except Exception:
                continue

    def close(self):
        self.running = False
        time.sleep(0.05)
        self.ser.close()


def y_target(x_px: float, scroll_px: float, cfg: TrainerConfig):
    phase = (x_px + scroll_px) * (2 * math.pi / cfg.wavelength)
    return CENTER_Y + cfg.amplitude * math.sin(phase)


def advanced_target(progress_px: float, scroll_px: float, cfg: TrainerConfig):
    phase = (progress_px + scroll_px) * (2 * math.pi / cfg.wavelength)
    x_amp = min(190.0, cfg.amplitude * 0.85)
    y_amp = cfg.amplitude
    x = (
        progress_px
        + x_amp * math.sin(phase * 0.72 + 0.8)
        + x_amp * 0.32 * math.sin(phase * 1.63 - 0.4)
    )
    y = (
        CENTER_Y
        + y_amp * math.sin(phase)
        + y_amp * 0.42 * math.sin(phase * 2.11 + 1.1)
        + y_amp * 0.18 * math.cos(phase * 0.49 - 0.6)
    )
    x = max(30.0, min(WIDTH - 30.0, x))
    y = max(30.0, min(HEIGHT - 30.0, y))
    return x, y


def sample_path(scroll_px: float, cfg: TrainerConfig, step: int = 6):
    points = []
    for progress in range(0, WIDTH + step, step):
        if cfg.scenario == "advanced":
            x, y = advanced_target(progress, scroll_px, cfg)
        else:
            x = float(progress)
            y = y_target(progress, scroll_px, cfg)
        points.append((x, y))
    return points


def point_to_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float):
    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.hypot(px - ax, py - ay)
    projection = ((px - ax) * dx + (py - ay) * dy) / denom
    projection = max(0.0, min(1.0, projection))
    closest_x = ax + projection * dx
    closest_y = ay + projection * dy
    return math.hypot(px - closest_x, py - closest_y)


def distance_to_path(px: float, py: float, points):
    if not points:
        return float("inf")
    best = math.hypot(px - points[0][0], py - points[0][1])
    for idx in range(len(points) - 1):
        ax, ay = points[idx]
        bx, by = points[idx + 1]
        best = min(best, point_to_segment_distance(px, py, ax, ay, bx, by))
    return best


def run(args):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    small = pygame.font.SysFont("Arial", 20)
    big = pygame.font.SysFont("Arial", 34)

    serial_reader = None
    if args.mode == "serial":
        serial_reader = SerialReader(args.port, args.baud)

    sim = Pose()
    cfg = TrainerConfig(
        scenario=args.scenario,
        speed=args.speed,
        amplitude=args.amplitude,
        tolerance=args.tolerance,
        wavelength=args.wavelength,
    )
    t0 = time.time()
    scroll_px = 0.0
    speed_factor = 1.0
    in_band_frames = 0
    total_frames = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    in_band_frames = 0
                    total_frames = 0
                    t0 = time.time()
                    scroll_px = 0.0
                    speed_factor = 1.0
                if event.key == pygame.K_TAB:
                    cfg.scenario = "advanced" if cfg.scenario == "practice" else "practice"
                # tuning runtime parametri
                if event.key == pygame.K_1:
                    cfg.speed = max(20.0, cfg.speed - 20.0)
                if event.key == pygame.K_2:
                    cfg.speed = min(800.0, cfg.speed + 20.0)
                if event.key == pygame.K_3:
                    cfg.amplitude = max(20.0, cfg.amplitude - 10.0)
                if event.key == pygame.K_4:
                    cfg.amplitude = min(280.0, cfg.amplitude + 10.0)
                if event.key == pygame.K_5:
                    cfg.tolerance = max(8.0, cfg.tolerance - 2.0)
                if event.key == pygame.K_6:
                    cfg.tolerance = min(130.0, cfg.tolerance + 2.0)
                if event.key == pygame.K_7:
                    cfg.wavelength = max(220.0, cfg.wavelength - 20.0)
                if event.key == pygame.K_8:
                    cfg.wavelength = min(1500.0, cfg.wavelength + 20.0)

        if args.mode == "keyboard":
            keys = pygame.key.get_pressed()
            speed = 1.2
            if keys[pygame.K_LEFT]:
                sim.x -= speed * dt
                speed_factor = max(0.2, speed_factor - 3.2 * dt)
            if keys[pygame.K_RIGHT]:
                sim.x += speed * dt
            if keys[pygame.K_UP]:
                sim.y -= speed * dt
            if keys[pygame.K_DOWN]:
                sim.y += speed * dt
            if not keys[pygame.K_LEFT]:
                speed_factor = min(1.0, speed_factor + 1.2 * dt)
            sim.x = max(-1.0, min(1.0, sim.x))
            sim.y = max(-1.0, min(1.0, sim.y))
            pose = sim
        else:
            pose = serial_reader.pose
            speed_factor = 1.0

        scroll_px += cfg.speed * speed_factor * dt

        px = WIDTH * 0.5 + pose.x * args.x_gain * 250
        py = HEIGHT * 0.5 + pose.y * args.y_gain * 250

        elapsed = time.time() - t0
        points_main = sample_path(scroll_px, cfg)
        inside = distance_to_path(px, py, points_main) <= cfg.tolerance

        total_frames += 1
        if inside:
            in_band_frames += 1
        accuracy = 100.0 * in_band_frames / max(1, total_frames)

        screen.fill(BG)
        for y in range(0, HEIGHT, 70):
            pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)
        for x in range(0, WIDTH, 100):
            pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT), 1)

        if len(points_main) > 1:
            for x, y in points_main:
                pygame.draw.circle(screen, BAND_COLOR, (int(x), int(y)), int(cfg.tolerance), 1)
            pygame.draw.lines(screen, PATH_COLOR, False, points_main, 3)

        pygame.draw.circle(screen, POINT_OK if inside else POINT_BAD, (int(px), int(py)), 14)

        label = font.render(f"Accuracy: {accuracy:5.1f}%", True, TEXT)
        mode = font.render(f"Mode: {args.mode}", True, TEXT)
        scenario = font.render(f"Scenario: {cfg.scenario}", True, TEXT)
        cfg_txt = font.render(
            f"speed={cfg.speed:.0f} brake={speed_factor:.2f} amp={cfg.amplitude:.0f} tol={cfg.tolerance:.0f} width={cfg.wavelength:.0f}",
            True,
            TEXT,
        )
        state = big.render("IN BANDA" if inside else "FUORI BANDA", True, POINT_OK if inside else POINT_BAD)
        help_txt = small.render(
            "TAB scenario  1/2 speed  3/4 ampiezza  5/6 tolleranza  7/8 larghezza",
            True,
            TEXT,
        )

        screen.blit(label, (20, 20))
        screen.blit(mode, (20, 50))
        screen.blit(scenario, (20, 80))
        screen.blit(cfg_txt, (20, 110))
        screen.blit(help_txt, (20, 140))
        screen.blit(state, (20, HEIGHT - 60))

        pygame.display.flip()

    if serial_reader:
        serial_reader.close()
    pygame.quit()


def parse_args():
    p = argparse.ArgumentParser(description="Balanced board sinusoid trainer")
    p.add_argument("--mode", choices=["keyboard", "serial"], default="keyboard")
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--scenario", choices=["practice", "advanced"], default="advanced")
    p.add_argument("--tolerance", type=float, default=35.0, help="Ampiezza banda tolleranza in pixel")
    p.add_argument("--amplitude", type=float, default=120.0, help="Ampiezza della sinusoide in pixel")
    p.add_argument("--wavelength", type=float, default=650.0, help="Larghezza sinusoide (lunghezza d'onda) in pixel")
    p.add_argument("--speed", type=float, default=250.0, help="Velocita di scorrimento in pixel/s")
    p.add_argument("--x-gain", type=float, default=1.0)
    p.add_argument("--y-gain", type=float, default=1.0)
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
