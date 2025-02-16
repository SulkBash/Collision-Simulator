import pygame
import math
import sys
import random

# Constants
WIDTH = 1000
HEIGHT = 750
BACKGROUND_COLOR = (0,0,0)
ELASTIC_COLOR = (0,255,0)
INELASTIC_COLOR = (255,0,0)
PANEL_WIDTH = 200
BUTTON_COLOR = (50,50,50)
HOVER_COLOR = (100,100,100)
substeps = 10

class Particle:
    def __init__(self, x, y, speed, direction, mass, radius, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.color = color
        angle = math.radians(direction)
        self.vx = speed * math.cos(angle)
        self.vy = -speed * math.sin(angle)
    
    def update_position(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val):
        self.rect = pygame.Rect(x,y,w,h)
        self.handle_rect = pygame.Rect(x,y-5,10,20)
        self.min = min_val
        self.max = max_val
        self.dragging = False
        self.value = 1.0
    def update(self, mouse_pos, mouse_down):
        if self.dragging:
            if mouse_down:
                self.handle_rect.centerx = max(self.rect.left, min(self.rect.right, mouse_pos[0]))
                self.value = (self.handle_rect.centerx - self.rect.left) / self.rect.width * (self.max - self.min) + self.min
                self.value = max(self.min, min(self.max, self.value))
            else:
                self.dragging = False
        elif mouse_down and self.handle_rect.collidepoint(mouse_pos):
            self.dragging = True
    
    def draw(self, screen):
        pygame.draw.rect(screen, (150,100,100), self.rect)
        pygame.draw.rect(screen, (200,200,200), self.handle_rect)

def wall_collision(particle, width, height, restitution):
    # Horizontal Walls
    if particle.x < particle.radius:
        particle.x = particle.radius
        particle.vx *= -restitution
        return True
    elif particle.x > width - particle.radius:
        particle.x = width - particle.radius
        particle.vx *= -restitution
        return True
    # Vertical Walls
    if particle.y < particle.radius:
        particle.y = particle.radius
        particle.vy *= -restitution
        return True
    elif particle.y > height - particle.radius:
        particle.y = height - particle.radius
        particle.vy *= -restitution
        return True

def particle_collision(p1, p2, restitution):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    distance = math.hypot(dx, dy)

    if distance == 0:
        return
    
    col_distance = p1.radius + p2.radius
    if distance < col_distance:
        # Normalized Collision Vector
        nx = dx / distance
        ny = dy / distance
        tx = -ny
        ty = nx

        # Normal Velocity
        vn1 = p1.vx * nx + p1.vy * ny
        vn2 = p2.vx * nx + p2.vy * ny
        # Tangent Velocity
        vt1 = p1.vx * tx + p1.vy * ty
        vt2 = p2.vx * tx + p2.vy * ty

        # New Velocities
        m1, m2 = p1.mass, p2.mass
        new_vn1 = vn1 + (m2/(m1+m2)) * (restitution + 1) * (vn2 - vn1)
        new_vn2 = vn2 - (m1/(m1+m2)) * (restitution + 1) * (vn2 - vn1)

        # Update Velocities
        p1.vx = new_vn1 * nx + vt1 * tx
        p1.vy = new_vn1 * ny + vt1 * ty
        p2.vx = new_vn2 * nx + vt2 * tx
        p2.vy = new_vn2 * ny + vt2 * ty

        # Overlap Correction
        overlap = (col_distance - distance)/2
        p1.x -= overlap * nx
        p1.y -= overlap * ny
        p2.x += overlap * nx
        p2.y += overlap * ny
        return True
    return False

def initial_particles(restitution):
    color = (int(255*(1-restitution)), int(255*restitution), 0)
    return [
        Particle(300, 300, 100, 0, 10, 20, color),
        Particle(650, 300, 0, 180, 10, 20, color),
    ]

def main():
    pygame.init() 
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Collision Simulator")
    clock = pygame.time.Clock()
    my_font = pygame.font.SysFont('Arial', 18)
    header_font = pygame.font.SysFont('Arial', 24, bold=True)

    # UI Elements
    slider = Slider(WIDTH-PANEL_WIDTH+10, 300, PANEL_WIDTH-20, 20, 0.0, 1.0)

    buttons = [
        {'rect': pygame.Rect(WIDTH-PANEL_WIDTH+10, 70, PANEL_WIDTH-20, 40), 'text': 'Reset Particles (R)', 'color': BUTTON_COLOR, 'hover': HOVER_COLOR, 'action': 'reset'},
        {'rect': pygame.Rect(WIDTH-PANEL_WIDTH+10, 145, PANEL_WIDTH-20, 40), 'text': 'Clear All (C)', 'color': BUTTON_COLOR, 'hover': HOVER_COLOR, 'action': 'clear'},
        {'rect': pygame.Rect(WIDTH-PANEL_WIDTH+10, 220, PANEL_WIDTH-20, 40), 'text': 'Quit', 'color': BUTTON_COLOR, 'hover': HOVER_COLOR, 'action': 'quit'}
    ]

    # Particles
    particles = []
    selected_particle = None
    restitution = 1.0
    running = True
    paused = False
    number_collisions = 0
    particles = initial_particles(restitution)

    while running:
        for event in pygame.event.get():
            mouse_pos = pygame.mouse.get_pos()
            mouse_down = pygame.mouse.get_pressed()[0]
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    number_collisions = 0
                    particles = initial_particles(restitution)
                elif event.key == pygame.K_c:
                    number_collisions = 0
                    particles = []
                elif event.key == pygame.K_q:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for p in reversed(particles):
                        if math.hypot(p.x - mouse_pos[0], p.y - mouse_pos[1]) < p.radius:
                            selected_particle = p
                            break
                        elif mouse_pos[0] > WIDTH-PANEL_WIDTH:
                            pass
                        else:
                            selected_particle = None
                    else:
                        for btn in buttons:
                            if btn['rect'].collidepoint(mouse_pos):
                                if btn['action'] == 'reset':
                                    number_collisions = 0
                                    particles = initial_particles(restitution)
                                elif btn['action'] == 'clear':
                                    number_collisions = 0
                                    particles = []
                                elif btn['action'] == 'quit':
                                    running = False
                elif event.button == 3:
                    if selected_particle:
                        particles.remove(selected_particle)
                        selected_particle = None
                    elif mouse_pos[0] < WIDTH-PANEL_WIDTH:
                        particles.append(Particle(
                            mouse_pos[0], mouse_pos[1], 
                            speed=random.uniform(50,300), 
                            direction=random.uniform(0,360), 
                            mass=random.uniform(1,100), 
                            radius = random.randint(10,30),
                            color = (int(255*(1-restitution)), int(255*restitution), 0)
                            ))

        # Update slider
        slider.update(mouse_pos, mouse_down)
        restitution = slider.value
        color = (int(255*(1-restitution)), int(255*restitution), 0)
        for p in particles:
            p.color = color

        # Update physics
        if not paused:
            dt = 1/60
            for _ in range(substeps):
                for p in particles:
                    p.update_position(dt/substeps)
                    if wall_collision(p, WIDTH-PANEL_WIDTH, HEIGHT, restitution):
                        number_collisions += 1

                for i in range(len(particles)):
                    for j in range(i+1, len(particles)):
                        if particle_collision(particles[i], particles[j], restitution):
                            number_collisions += 1


        # Display Collision Count
        text = my_font.render(f"Collisions: {number_collisions}", False, (255,255,255))

        screen.fill(BACKGROUND_COLOR)

        # Draw particles
        for p in particles:
            p.draw(screen)
            if p == selected_particle:
                pygame.draw.circle(screen, (255,255,0), (int(p.x), int(p.y)), p.radius+2, 2)

        # Draw control panel
        pygame.draw.rect(screen, (30,30,30), (WIDTH-PANEL_WIDTH, 0, PANEL_WIDTH, HEIGHT))
        text = header_font.render("Controls", True, (255,255,255))
        screen.blit(text, (WIDTH-PANEL_WIDTH+10, 10))

        # Draw slider
        slider.draw(screen)
        slider_text = my_font.render(f"Restitution: {restitution:.2f}", True, (255,255,255))
        screen.blit(slider_text, (WIDTH-PANEL_WIDTH+20, 320))

        # Draw buttons
        for btn in buttons:
            color = btn['color']
            if btn['rect'].collidepoint(mouse_pos):
                color = btn['hover']
            pygame.draw.rect(screen, color, btn['rect'])

            text = my_font.render(btn['text'], True, (255,255,255))
            screen.blit(text, (btn['rect'].x + 10, btn['rect'].y - 10))

        if paused:
            pause_text = my_font.render("PAUSED", True, (255,255,255))
            screen.blit(pause_text, (WIDTH//2 - 60, HEIGHT//2 - 20))

        # Particle properties panel
        if selected_particle:
            prop_y = 400
            txt = header_font.render("Selected Particle", True, (255,255,255))
            screen.blit(txt, (WIDTH-PANEL_WIDTH+10, prop_y-40))
            props = [
                ("X Position", "x", selected_particle.x, 0, WIDTH-PANEL_WIDTH, 5),
                ("Y Position", "y", HEIGHT - selected_particle.y, 0, HEIGHT, 5),
                ("H. Velocity", "vx", selected_particle.vx, -10000, 10000, 5),
                ("V. Velocity", "vy", -selected_particle.vy, -1000, 1000, 5),
                ("Mass", "mass", selected_particle.mass, 1, 10000, 1),
                ("Radius", "radius", selected_particle.radius, 1, 100, 1),
            ]
            for i, (label, attr, value, min_val, max_val, step) in enumerate(props):
                display_value = value if attr !="vy" else -value
                text = my_font.render(f"{label}: {value:.1f}", True, (255,255,255))
                screen.blit(text, (WIDTH-PANEL_WIDTH+10, prop_y + i*30))

                # Buttons
                btn_plus = pygame.Rect(WIDTH-PANEL_WIDTH+160, prop_y + i*30, 20, 20)
                btn_minus = pygame.Rect(WIDTH-PANEL_WIDTH+140, prop_y + i*30, 20, 20)

                # Button click
                if mouse_down:
                    current_value = getattr(selected_particle, attr)
                    if attr == "y":
                        current_value = HEIGHT - current_value
                        if btn_plus.collidepoint(mouse_pos):
                            new_value = current_value + step
                            setattr(selected_particle, attr, HEIGHT - min(max_val, new_value))
                        elif btn_minus.collidepoint(mouse_pos):
                            new_value = current_value - step
                            setattr(selected_particle, attr, HEIGHT - max(min_val, new_value))

                    elif btn_plus.collidepoint(mouse_pos):
                        new_value = current_value + (step if attr != "vy" else -step)
                        setattr(selected_particle, attr, min(max_val, new_value))

                    elif btn_minus.collidepoint(mouse_pos):
                        new_value = current_value - (step if attr != "vy" else -step)
                        setattr(selected_particle, attr, max(min_val, new_value))

                # Draw buttons
                pygame.draw.rect(screen, HOVER_COLOR if btn_plus.collidepoint(mouse_pos) else BUTTON_COLOR, btn_plus)
                pygame.draw.rect(screen, HOVER_COLOR if btn_minus.collidepoint(mouse_pos) else BUTTON_COLOR, btn_minus)
                screen.blit(my_font.render("+", True, (255,255,255)), (btn_plus.x+6, btn_plus.y+2))
                screen.blit(my_font.render("-", True, (255,255,255)), (btn_minus.x+6, btn_minus.y+2))

        # Draw stats
        stats = [
            f"Particles: {len(particles)} ",
            f"Restitution: {restitution:.2f} ",
            f"Collisions: {number_collisions} ",
            f"Mode: {'Elastic ' if restitution == 1.0 else 'Totally Inelastic ' if restitution == 0.0 else 'Inelastic'}",
        ]
        for i, stat in enumerate(stats):
            text = my_font.render(stat, True, (255,255,255))
            screen.blit(text, (10, 10 + i*20))

        # Draw help
        help_text = [
            "Left-Click to select particle",
            "Right-Click to add particles (or remove selected)",
            "R - Reset Particles",
            "C - Clear All",
            "Space - Pause",
        ]
        for i, line in enumerate(help_text):
            text = my_font.render(line, True, (200,200,200))
            screen.blit(text, (10, HEIGHT - 105 + i*20))

        pygame.display.flip()
        clock.tick(60)   

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
        
