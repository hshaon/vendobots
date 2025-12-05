#!/usr/bin/env python3
import pygame
import roslibpy
import math
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
ROBOT_IP = "192.168.2.115"
ODOM_TOPIC = "/odom"
PLAN_TOPIC = "/move_base/TebLocalPlannerROS/local_plan"

SCALE = 200          # pixels per meter
MAX_DIST = 2.5       # meters ahead
PATH_THICKNESS = 50  # thick visible path
ARROW_SPEED = 0.1    # how fast arrow moves along the path

FLIP_HORIZONTAL = False


# -----------------------------
# Utility Functions
# -----------------------------
def yaw_from_quat(q):
    x, y, z, w = q['x'], q['y'], q['z'], q['w']
    siny = 2 * (w*z + x*y)
    cosy = 1 - 2 * (y*y + z*z)
    return math.atan2(siny, cosy)


def transform_to_robot_frame(px, py, rx, ry, ryaw):
    dx = px - rx
    dy = py - ry
    xr = dx * math.cos(ryaw) + dy * math.sin(ryaw)
    yr = -dx * math.sin(ryaw) + dy * math.cos(ryaw)
    return xr, yr


def angle_between_points(p1, p2):
    dx = p2[0] - p1[0]
    dy = p1[1] - p2[1]
    return math.degrees(math.atan2(dy, dx))


# -----------------------------
# Projector Class
# -----------------------------
class Projector:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()

        self.w, self.h = self.screen.get_size()
        self.cx, self.cy = self.w // 2, self.h // 2

        self.font = pygame.font.SysFont("Segoe UI", 32)
        self.smallfont = pygame.font.SysFont("Segoe UI", 26)

        # robot state
        self.rx = 0.0
        self.ry = 0.0
        self.ryaw = 0.0
        self.future = []

        # rotation calibration mode
        self.rotation_angle = 0

        # arrow animation
        self.arrow_progress = 0.0
        self.arrow_size = 70  # size of red arrow in pixels

    # ROS callbacks
    def update_odom(self, msg):
        pos = msg['pose']['pose']['position']
        ori = msg['pose']['pose']['orientation']
        self.rx = pos['x']
        self.ry = pos['y']
        self.ryaw = yaw_from_quat(ori)

    def update_plan(self, msg):
        pts = []
        for p in msg['poses']:
            pos = p['pose']['position']
            pts.append((pos['x'], pos['y']))
        self.future = pts

    # -----------------------------
    # Render loop
    # -----------------------------
    def render(self):

        # Handle keyboard input
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    quit()

                if event.key == pygame.K_1:
                    self.rotation_angle = 0
                if event.key == pygame.K_2:
                    self.rotation_angle = 270  # 90 CW
                if event.key == pygame.K_3:
                    self.rotation_angle = 180
                if event.key == pygame.K_4:
                    self.rotation_angle = 90   # 90 CCW (your mounting alignment)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.quit()
                quit()

        # Rendering surface
        temp = pygame.Surface((self.w, self.h))
        temp.fill((0, 0, 0))

        screen_pts = []

        # -----------------------------
        # Draw predicted TEB path
        # -----------------------------
        if len(self.future) > 1:
            last = None
            for (x, y) in self.future:
                xr, yr = transform_to_robot_frame(x, y, self.rx, self.ry, self.ryaw)

                if xr < 0 or math.hypot(xr, yr) > MAX_DIST:
                    continue

                sx = int(self.cx + xr * SCALE)
                sy = int(self.cy - yr * SCALE)
                screen_pts.append((sx, sy))

                if last:
                    pygame.draw.line(temp, (0, 220, 255), last, (sx, sy), PATH_THICKNESS)

                last = (sx, sy)

        # -----------------------------
        # Draw MOVING RED ARROW
        # -----------------------------
        if len(screen_pts) > 2:

            self.arrow_progress += ARROW_SPEED
            if self.arrow_progress > 1.0:
                self.arrow_progress = 0.0

            total = len(screen_pts)
            index = int(self.arrow_progress * (total - 1))

            if index < total - 1:
                p1 = screen_pts[index]
                p2 = screen_pts[index + 1]
                angle = angle_between_points(p1, p2)

                # Construct vector arrow polygon
                L = self.arrow_size
                W = self.arrow_size * 0.5

                base_shape = [
                    (0, -W/2),
                    (L * 0.7, -W/2),
                    (L * 0.7, -W),
                    (L, 0),
                    (L * 0.7, W),
                    (L * 0.7, W/2),
                    (0, W/2)
                ]

                rad = math.radians(angle)
                sin_a = math.sin(rad)
                cos_a = math.cos(rad)

                arrow_poly = []
                for (x, y) in base_shape:
                    rx = x * cos_a - y * sin_a
                    ry = x * sin_a + y * cos_a
                    arrow_poly.append((p1[0] + rx, p1[1] + ry))

                pygame.draw.polygon(temp, (255, 30, 30), arrow_poly)

        # -----------------------------
        # Draw robot marker at center
        # -----------------------------
        pygame.draw.circle(temp, (255, 255, 255), (self.cx, self.cy), 15)

        # UI labels
        label = self.font.render("ROBOT PATH", True, (0, 200, 255))
        temp.blit(label, (self.cx - label.get_width() // 2, int(self.h * 0.88)))

        rot_text = f"Rotation: {self.rotation_angle}°"
        temp.blit(self.smallfont.render(rot_text, True, (255, 255, 0)), (20, 20))

        # -----------------------------
        # Apply calibration rotation
        # -----------------------------
        output = pygame.transform.rotate(temp, self.rotation_angle)

        if FLIP_HORIZONTAL:
            output = pygame.transform.flip(output, True, False)

        self.screen.blit(output, (0, 0))
        pygame.display.flip()
        self.clock.tick(30)


# -----------------------------
# Main
# -----------------------------
def main():
    proj = Projector()

    ros = roslibpy.Ros(host=ROBOT_IP, port=9090)
    ros.run()

    roslibpy.Topic(ros, ODOM_TOPIC, "nav_msgs/Odometry") \
        .subscribe(lambda msg: proj.update_odom(msg))

    roslibpy.Topic(ros, PLAN_TOPIC, "nav_msgs/Path") \
        .subscribe(lambda msg: proj.update_plan(msg))

    while True:
        proj.render()


if __name__ == "__main__":
    main()
