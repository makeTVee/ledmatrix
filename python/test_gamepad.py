import  os,time

os.environ["SDL_VIDEODRIVER"] = "dummy" #dummy display for pygame audio
import pygame
from pygame.locals import *
pygame.init()
pygame.display.set_mode((1,1))
pygame.joystick.init()
while True:   
   pygame.joystick.quit()
   pygame.joystick.init()
   time.sleep(1)
   try:
      joystick = pygame.joystick.Joystick(0) # create a joystick instance
      joystick.init() # init instance
      print("Initialized joystick: {}".format(joystick.get_name()))
      print("Buttons joystick: {}".format(joystick.get_numbuttons()))
   except pygame.error:
      print("no joystick found.")


#pygame.init()

# Initialize the joysticks.
#pygame.joystick.init()

while True:
   pygame.event.pump()
   for event in pygame.event.get(): # User did something.
      if event.type == pygame.QUIT: # If user clicked close.
          done = True # Flag that we are done so we exit this loop.
      elif event.type == pygame.JOYBUTTONDOWN:
          print(event.button)
          print("Joystick button pressed.")
      elif event.type == pygame.JOYBUTTONUP:
          print("Joystick button released.")
      elif event.type == pygame.JOYAXISMOTION:
          print(event.axis)
          print(event.value)
