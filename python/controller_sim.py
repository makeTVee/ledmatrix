# Simulator for controller
# by M Oehler
# https://hackaday.io/project/11064-raspberry-pi-retro-gaming-led-display

import random, time, pygame, sys, socket
from pygame.locals import *

FPS = 25
WINDOWWIDTH = 640
WINDOWHEIGHT = 480

mask = bytearray([1,2,4,8,16,32,64,128])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
    pygame.display.set_caption('Tetromino')

    host = 'localhost'
    port = 4711

    # connection to hostname on the port.
    s.connect((host, port))

    while True: # game loop
        runGame()
        pygame.mixer.music.stop()
        showTextScreen('Game Over')


def runGame():
    # setup variables for the start of the game

    data = 0;
    while True: # game loop

        checkForQuit()

        for event in pygame.event.get(): # event handling loop
            if event.type == KEYDOWN:
                # moving the piece sideways
                if (event.key == K_LEFT):
                   data+=mask[0]
                elif (event.key == K_RIGHT):
                    data+=mask[1]
                # rotating the piece (if there is room to rotate)
                elif (event.key == K_UP):
                    data+=mask[2]
                # making the piece fall faster with the down key
                elif (event.key == K_DOWN):
                    data+=mask[3]
                # move the current piece all the way down
                elif event.key == K_1:
                    data+=mask[4]
                elif event.key == K_2:
                    data+=mask[5]
                elif event.key == K_3:
                    data+=mask[6]
                elif event.key == K_4:
                    data+=mask[7]
            elif event.type == KEYUP:
                if (event.key == K_LEFT):
                   data-=mask[0]
                elif (event.key == K_RIGHT):
                    data-=mask[1]
                # rotating the piece (if there is room to rotate)
                elif (event.key == K_UP):
                    data-=mask[2]
                # making the piece fall faster with the down key
                elif (event.key == K_DOWN):
                    data-=mask[3]
                # move the current piece all the way down
                elif event.key == K_1:
                    data-=mask[4]
                elif event.key == K_2:
                    data-=mask[5]
                elif event.key == K_3:
                    data-=mask[6]
                elif event.key == K_4:
                    data-=mask[7]

        s.send(bytearray([data]))
        pygame.display.update()
        time.sleep(.025)


def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()


def terminate():
    pygame.quit()
    sys.exit()


# KRT 17/06/2012 rewrite event detection to deal with mouse use
def checkForKeyPress():
    for event in pygame.event.get():
        if event.type == QUIT:      #event is quit
            terminate()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:   #event is escape key
                terminate()
            else:
                return event.key   #key found return with it
    # no quit or key events in queue so return None
    return None



##def checkForKeyPress():
##    # Go through event queue looking for a KEYUP event.
##    # Grab KEYDOWN events to remove them from the event queue.
##    checkForQuit()
##
##    for event in pygame.event.get([KEYDOWN, KEYUP]):
##        if event.type == KEYDOWN:
##            continue
##        return event.key
##    return None


def showTextScreen(text):
    # This function displays large text in the
    # center of the screen until a key is pressed.
    # Draw the text drop shadow
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTSHADOWCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = makeTextObjs('Press a key to play.', BASICFONT, TEXTCOLOR)
    pressKeyRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while checkForKeyPress() == None:
        pygame.display.update()
        FPSCLOCK.tick()


def checkForQuit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back


if __name__ == '__main__':
    main()
