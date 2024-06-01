# graphic interface for F3S
import subprocess

import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.textbox import TextBox

pygame.init()

# general setup
screen = pygame.display.set_mode((300, 360))
bg_color = (255,255,255)
screen.fill(color=bg_color)
pygame.display.set_caption('Flying 3D Scanner')
pygame.display.flip()

#elements setup
# light shade of the button
color_light = (170, 170, 170)

# dark shade of the button
color_dark = (100, 100, 100)

session_name_textbox = TextBox(screen, 50, 50, 200, 50, fontSize=30,
                  borderColour=(170, 170, 170), textColour=(0, 0, 0),
                  onSubmit=None, radius=10, borderThickness=5)

def run_pilot():
    if session_name_textbox.text != "":
        subprocess.Popen(["python", "pilot.py", session_name_textbox.text])

pilot_button = Button(
    # Mandatory Parameters
    screen,  # Surface to place button on
    50,  # X-coordinate of top left corner
    120,  # Y-coordinate of top left corner
    200,  # Width
    50,  # Height

    # Optional Parameters
    text='pilot',  # Text to display
    fontSize=35,  # Size of font
    margin=20,  # Minimum distance between text/image and edge of button
    inactiveColour=color_light,  # Colour of button when not being interacted with
    hoverColour=(100, 100, 100),  # Colour of button when being hovered over
    pressedColour=(0, 200, 20),  # Colour of button when being clicked
    radius=20,  # Radius of border corners (leave empty for not curved)
    onClick=lambda: run_pilot() # Function to call when clicked on
)

def run_convert(type):
    if session_name_textbox.text != "":
        if type == "CM":
            subprocess.Popen(["python", "convert.py", "COLMAP", session_name_textbox.text])
        else:
            subprocess.Popen(["python", "convert.py", "MVG", session_name_textbox.text])

colmap_button = Button(
    # Mandatory Parameters
    screen,  # Surface to place button on
    50,  # X-coordinate of top left corner
    190,  # Y-coordinate of top left corner
    200,  # Width
    50,  # Height

    # Optional Parameters
    text='convert (colmap)',  # Text to display
    fontSize=20,  # Size of font
    margin=20,  # Minimum distance between text/image and edge of button
    inactiveColour=color_light,  # Colour of button when not being interacted with
    hoverColour=(100, 100, 100),  # Colour of button when being hovered over
    pressedColour=(0, 200, 20),  # Colour of button when being clicked
    radius=20,  # Radius of border corners (leave empty for not curved)
    onClick=lambda: run_convert("CM") # Function to call when clicked on
)

mvg_button = Button(
    # Mandatory Parameters
    screen,  # Surface to place button on
    50,  # X-coordinate of top left corner
    260,  # Y-coordinate of top left corner
    200,  # Width
    50,  # Height

    # Optional Parameters
    text='convert (openMVG)',  # Text to display
    fontSize=20,  # Size of font
    margin=20,  # Minimum distance between text/image and edge of button
    inactiveColour=color_light,  # Colour of button when not being interacted with
    hoverColour=(100, 100, 100),  # Colour of button when being hovered over
    pressedColour=(0, 200, 20),  # Colour of button when being clicked
    radius=20,  # Radius of border corners (leave empty for not curved)
    onClick=lambda: run_convert("MVG") # Function to call when clicked on
)

# run loop
running = True
while running:
    pygame.time.delay(100)
    events = pygame.event.get()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            print(pos)

    pygame_widgets.update(events)
    pygame.display.update()
