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


def y_target(x_px: float, t: float, amplitude: float, wavelength: float, speed: float):
    phase = (x_px + speed * t) * (2 * math.pi / wavelength)
    return CENTER_Y + amplitude * math.sin(phase)


def run(args):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)
    big = pygame.font.SysFont("Arial", 34)

    serial_reader = None
    if args.mode == "serial":
        serial_reader = SerialReader(args.port, args.baud)

    sim = Pose()
    t0 = time.time()
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

        if args.mode == "keyboard":
            keys = pygame.key.get_pressed()
            speed = 1.2
            if keys[pygame.K_LEFT]:
                sim.x -= speed * dt
            if keys[pygame.K_RIGHT]:
                sim.x += speed * dt
            if keys[pygame.K_UP]:
                sim.y -= speed * dt
            if keys[pygame.K_DOWN]:
                sim.y += speed * dt
            sim.x = max(-1.0, min(1.0, sim.x))
            sim.y = max(-1.0, min(1.0, sim.y))
            pose = sim
        else:
            pose = serial_reader.pose

        # mapping board tilt to visual point
        px = WIDTH * 0.5 + pose.x * args.x_gain * 250
        py = HEIGHT * 0.5 + pose.y * args.y_gain * 250

        elapsed = time.time() - t0
        target_y = y_target(px, elapsed, args.amplitude, args.wavelength, args.speed)
        inside = abs(py - target_y) <= args.tolerance

        total_frames += 1
        if inside:
            in_band_frames += 1
        accuracy = 100.0 * in_band_frames / max(1, total_frames)

        screen.fill(BG)

        for y in range(0, HEIGHT, 70):
            pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)
        for x in range(0, WIDTH, 100):
            pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT), 1)

        points_main = []
        points_hi = []
        points_lo = []
        for x in range(0, WIDTH, 6):
            yy = y_target(x, elapsed, args.amplitude, args.wavelength, args.speed)
            points_main.append((x, yy))
            points_hi.append((x, yy - args.tolerance))
            points_lo.append((x, yy + args.tolerance))

        if len(points_main) > 1:
            pygame.draw.lines(screen, BAND_COLOR, False, points_hi, 2)
            pygame.draw.lines(screen, BAND_COLOR, False, points_lo, 2)
            pygame.draw.lines(screen, PATH_COLOR, False, points_main, 3)

        pygame.draw.circle(screen, POINT_OK if inside else POINT_BAD, (int(px), int(py)), 14)

        label = font.render(f"Accuracy: {accuracy:5.1f}%", True, TEXT)
        mode = font.render(f"Mode: {args.mode}", True, TEXT)
        cfg = font.render(f"tol={args.tolerance}px amp={args.amplitude}px", True, TEXT)
        state = big.render("IN BANDA" if inside else "FUORI BANDA", True, POINT_OK if inside else POINT_BAD)
        screen.blit(label, (20, 20))
        screen.blit(mode, (20, 50))
        screen.blit(cfg, (20, 80))
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
    p.add_argument("--tolerance", type=float, default=35.0)
    p.add_argument("--amplitude", type=float, default=120.0)
    p.add_argument("--wavelength", type=float, default=650.0)
    p.add_argument("--speed", type=float, default=250.0)
    p.add_argument("--x-gain", type=float, default=1.0)
    p.add_argument("--y-gain", type=float, default=1.0)
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
