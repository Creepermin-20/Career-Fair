import pygame
import sys
import RPi.GPIO as GPIO # type: ignore

pygame.init()

screen = pygame.display.set_mode((800, 480), pygame.RESIZABLE)
screen_width, screen_height = pygame.display.get_surface().get_size()
pygame.display.set_caption("Conveyor Simulator")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (230, 230, 230)
BLUE = (0, 0, 255)
assigned_color = (0,0,0)
output_pin = 11
stepper_pin = 17

# ==============================================
#          Start of Button Functions
# ==============================================

on = False

def start():
    global on,assigned_color,output_pin
    if not on:
        GPIO.output(output_pin, GPIO.HIGH)
        assigned_color = (15, 180, 30)
        on = True

def stop():
    global on,assigned_color,output_pin
    if on:
        assigned_color = (255, 40, 50)
        GPIO.output(output_pin, GPIO.LOW)
        on = False

def rst_count():
    global red_blocks, blue_blocks, green_blocks, yellow_blocks
    red_blocks = 0
    blue_blocks = 0
    green_blocks = 0
    yellow_blocks = 0

def jog_conveyor():
    if on:
        print("PROGRAM IS STARTED. STOP THE PROGRAM TO JOG CONVEYOR.")
    GPIO.output(stepper_pin, GPIO.HIGH)

def stop_program():
    global running
    GPIO.cleanup()
    pygame.quit()
    sys.exit()

# ==============================================
#               START OF CONSOLE
# ==============================================

# Console class
class Console:
    def __init__(self, rect, text_size, text_font="monospace", max_lines=10):
        self.rect = pygame.Rect(rect)
        self.font = pygame.font.SysFont(text_font, text_size, True)
        self.max_lines = max_lines
        self.lines = []

        # For scheduled logging
        self.log_schedule = []
        self.start_time = pygame.time.get_ticks()
        self.next_log_index = 0

    def log(self, message, color=BLACK):
        self.lines.append((str(message), color))
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)

    def draw(self, surface):
        border_radius = 0
        pygame.draw.rect(surface, GRAY, self.rect,0,border_radius)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius)
        y = self.rect.top + 5
        for message, color in self.lines:
            # message_wrapped = textwrap.fill(message,((screen_width - (screen_width/5))))
            rendered = self.font.render(message, True, color)
            surface.blit(rendered, (self.rect.left + 5, y))
            y += self.font.get_height()

    def schedule_logs(self, log_entries):
        """
        log_entries: list of tuples (delay_ms_from_start, message)
        """
        self.log_schedule = sorted(log_entries)
        self.start_time = pygame.time.get_ticks()
        self.next_log_index = 0

    def update(self):
        """
        Should be called every frame inside the game loop to update log messages based on time.
        """
        now = pygame.time.get_ticks() - self.start_time
        while self.next_log_index < len(self.log_schedule) and now >= self.log_schedule[self.next_log_index][0]:
            _, message = self.log_schedule[self.next_log_index]
            self.log(message)
            self.next_log_index += 1

def update_color_blocks(colored_block_list):
    global color_blocks
    red_blocks = colored_block_list[0]
    blue_blocks = colored_block_list[1]
    green_blocks = colored_block_list[2]
    yellow_blocks = colored_block_list[3]
    color_blocks.log("Red Blocks: " + str(red_blocks))
    color_blocks.log("")
    color_blocks.log("Blue Blocks: " + str(blue_blocks))
    color_blocks.log("")
    color_blocks.log("Green Blocks: " + str(green_blocks))
    color_blocks.log("")
    color_blocks.log("Yellow Blocks: " + str(yellow_blocks))

def update_stats(block_list):
    global count, block_stats
    for num in block_list:
        count += num
    block_stats.log("Total Run Time: ")
    block_stats.log("")
    block_stats.log("Total Part Count: " + str(count))

# ==============================================
#              START OF BUTTON SYS
# ==============================================

class Button:
    def __init__(self, rect, text, on_click, text_font="Arial", radius=0, text_size=13, text_color=(25, 25, 25), bg_color=(200, 200, 200), click_color=(150, 150, 150)):
        
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.font = pygame.font.SysFont(text_font, text_size, True)

        self.text_color = text_color
        self.bg_color = bg_color
        self.click_color = click_color
        self.radius = radius

        self.clicked = False
        self.mouse_over = False
        self.argument = None

    def draw(self, surface):
        color = self.click_color if self.clicked else self.bg_color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 2, self.radius)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_over = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.mouse_over and event.button == 1:
                self.clicked = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked and self.mouse_over and event.button == 1 and self.on_click is not None:
                self.on_click()
            self.clicked = False

class CircleButton:
    def __init__(self, x, y, radius, color, hover_color, outline_color, text='', text_color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.outline_color = outline_color
        self.hover_color = hover_color or color
        self.bright_color = (self.color[0] + 55 if self.color[0] < 200 else self.color[0], self.color[1] + 55 if self.color[1] < 200 else self.color[1], self.color[2] + 55 if self.color[2] < 200 else self.color[2])
        self.text = text
        self.font = pygame.font.SysFont("roboto mono", 30, bold=True)
        self.text_color = text_color

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.is_hovered(mouse_pos)
        pygame.draw.circle(screen, self.hover_color if is_hovered else self.color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, self.outline_color if not is_hovered else self.bright_color, (self.x, self.y), self.radius, 4)

        if self.text and self.font:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=(self.x, self.y))
            screen.blit(text_surf, text_rect)

    def is_hovered(self, pos):
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx**2 + dy**2 <= self.radius**2

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered(event.pos)

# ============================================== 
#                START OF MISC
# ==============================================

# Nothing but us Chickens

# ============================================== 
#                START OF MAIN 
# ==============================================

# Name of Circular Button = CircularButtonClass(positional argument x, positional argument y, size argument x, size argument y, color, dark color, darker color, text="TEXT")
# Name of Rectangle Button = ButtonClass(rect=(positional argument x, positional argument y, size argument x, size argument y), text="TEXT", on_click=CLICKED_FUNCTION)
# Name of TextBox = Console(rect=(positional argument x, positional argument y, size argument x, size argument y), text_font="monospace", text_size=TEXT_SIZE, max_lines=10 or MAX_LINES)

start_button = CircleButton(552, 102, 47, (15, 180, 30), (15, 160, 30), (15, 140, 30), text="START")

stop_button = CircleButton(726, 102, 47, (180, 15, 30), (160, 15, 30), (140, 15, 30), text="STOP")

jog_button = CircleButton(275, 425, 47, (200, 210, 255), (180, 190, 235), (160, 170, 215), text="JOG")

exit_button = Button(rect=(10, 10, 30, 30), text="X", on_click=stop_program)

color_blocks = Console(rect=(552, 196, 219, 143), text_font="Corbel", text_size=19, max_lines=7)

reset_count = Button(rect=(color_blocks.rect.x + 54, color_blocks.rect.y + color_blocks.rect.height + 3, 110, 29), radius=4, text_font="Corbel", text_size=18, text="Reset Count", on_click=rst_count)

block_stats = Console(rect=(552, 373, 219, 67), text_font="Corbel", text_size=19, max_lines=3)

reset_time = Button(rect=(block_stats.rect.x, block_stats.rect.y + block_stats.rect.height + 6, 105, 29), radius=4, text_font="Corbel", text_size=18, text="Reset Time", on_click=rst_count)
reset_total = Button(rect=(color_blocks.rect.x + color_blocks.rect.width - 110, block_stats.rect.y + block_stats.rect.height + 6, 110, 29), radius=4, text_font="Corbel", text_size=18, text="Reset Count", on_click=None)

def draw_assets():
    global start_button, stop_button, jog_button, exit_button, color_blocks, reset_count, block_stats, reset_time, reset_total, blocks_list
    start_button.draw(screen)
    stop_button.draw(screen)
    exit_button.draw(screen)
    reset_count.draw(screen)
    reset_time.draw(screen)
    reset_total.draw(screen)
    jog_button.draw(screen)
    blocks_list = [red_blocks, blue_blocks, green_blocks, yellow_blocks]
    update_color_blocks(blocks_list)
    update_stats(blocks_list)
    color_blocks.update()
    block_stats.update()
    color_blocks.draw(screen)
    block_stats.draw(screen)

# ============================================== 
#                 START OF LOOP
# ==============================================

message_logged = False
running = True
image = pygame.image.load("background.png")
image_rect = image.get_rect()
image_rect.topleft = (0, 0)
blocks_list = []
red_blocks = 0
blue_blocks = 0
green_blocks = 0
yellow_blocks = 0
count = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                print("Escape Pressed\nStopping program...\nProgram Stopped.")
                running = False

        if event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        if start_button.is_clicked(event):
            start()
        
        if stop_button.is_clicked(event):
            stop()
        
        if jog_button.is_clicked(event):
            jog_conveyor()

        exit_button.handle_event(event)
        reset_count.handle_event(event)
        reset_time.handle_event(event)
        reset_total.handle_event(event)

    screen.blit(image, image_rect)
    draw_assets()
    pygame.display.flip()

GPIO.cleanup()
pygame.quit()
sys.exit()
