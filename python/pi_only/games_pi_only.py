# WS2812 LED Matrix Gamecontrol (Tetris, Snake, Pong)
# by M Oehler
# https://hackaday.io/project/11064-raspberry-pi-retro-gaming-led-display
# ported from
# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, time, sys, os, pickle
from PIL import Image


# If Pi = False the script runs in simulation mode using pygame lib
PI = True
import pygame
from pygame.locals import *
if PI:
    os.environ["SDL_VIDEODRIVER"] = "dummy" #dummy display for pygame joystick usage
    import board
    import neopixel
    import subprocess
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi, noop
    from luma.core.render import canvas
    from luma.core.virtual import viewport
    from luma.core.legacy import text, show_message
    from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

# only modify this two values for size adaption!
PIXEL_X=10
PIXEL_Y=20

SIZE= 20
FPS = 15
BOXSIZE = 20
WINDOWWIDTH = BOXSIZE * PIXEL_X
WINDOWHEIGHT = BOXSIZE * PIXEL_Y
BOARDWIDTH = PIXEL_X
BOARDHEIGHT = PIXEL_Y
BLANK = '.'
MOVESIDEWAYSFREQ = 0.15
MOVEDOWNFREQ = 0.15
FALLING_SPEED = 0.8
LED_BRIGHTNESS = 0.6

#               R    G    B
WHITE       = (255, 255, 255)
GRAY        = (185, 185, 185)
BLACK       = (  0,   0,   0)
RED         = (255,   0,   0)
LIGHTRED    = (175,  20,  20)
GREEN       = (  0, 255,   0)
LIGHTGREEN  = ( 20, 175,  20)
BLUE        = (  0,   0, 255)
LIGHTBLUE   = ( 20,  20, 175)
YELLOW      = (255, 255,   0)
LIGHTYELLOW = (175, 175,  20)
CYAN        = (  0, 255, 255)
MAGENTA     = (255,   0, 255)
ORANGE      = (255, 100,   0)

SCORES =(0,40,100,300,1200)

BORDERCOLOR = BLUE
BGCOLOR = BLACK
TEXTCOLOR = WHITE
TEXTSHADOWCOLOR = GRAY
COLORS      = (BLUE,GREEN,RED,YELLOW,CYAN,MAGENTA,ORANGE)
LIGHTCOLORS = (LIGHTBLUE, LIGHTGREEN, LIGHTRED, LIGHTYELLOW)
#assert len(COLORS) == len(LIGHTCOLORS) # each color must have light color


TEMPLATEWIDTH = 5
TEMPLATEHEIGHT = 5


S_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '..OO.',
                     '.OO..',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..OO.',
                     '...O.',
                     '.....']]

Z_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '.OO..',
                     '..OO.',
                     '.....'],
                    ['.....',
                     '..O..',
                     '.OO..',
                     '.O...',
                     '.....']]

I_SHAPE_TEMPLATE = [['..O..',
                     '..O..',
                     '..O..',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     'OOOO.',
                     '.....',
                     '.....']]

O_SHAPE_TEMPLATE = [['.....',
                     '.....',
                     '.OO..',
                     '.OO..',
                     '.....']]

J_SHAPE_TEMPLATE = [['.....',
                     '.O...',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..OO.',
                     '..O..',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '...O.',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..O..',
                     '.OO..',
                     '.....']]

L_SHAPE_TEMPLATE = [['.....',
                     '...O.',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..O..',
                     '..OO.',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '.O...',
                     '.....'],
                    ['.....',
                     '.OO..',
                     '..O..',
                     '..O..',
                     '.....']]

T_SHAPE_TEMPLATE = [['.....',
                     '..O..',
                     '.OOO.',
                     '.....',
                     '.....'],
                    ['.....',
                     '..O..',
                     '..OO.',
                     '..O..',
                     '.....'],
                    ['.....',
                     '.....',
                     '.OOO.',
                     '..O..',
                     '.....'],
                    ['.....',
                     '..O..',
                     '.OO..',
                     '..O..',
                     '.....']]

PIECES = {'S': S_SHAPE_TEMPLATE,
          'Z': Z_SHAPE_TEMPLATE,
          'I': I_SHAPE_TEMPLATE,
          'J': J_SHAPE_TEMPLATE,
          'L': L_SHAPE_TEMPLATE,
          'O': O_SHAPE_TEMPLATE,
          'T': T_SHAPE_TEMPLATE}

PIECES_ORDER = {'S': 0,'Z': 1,'I': 2,'J': 3,'L': 4,'O': 5,'T': 6}

# snake constants #
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0 # syntactic sugar: index of the worm's head

# font clock #

clock_font = [
  0x1F, 0x11, 0x1F,
  0x00, 0x00, 0x1F,
  0x1D, 0x15, 0x17,
  0x15, 0x15, 0x1F,
  0x07, 0x04, 0x1F,
  0x17, 0x15, 0x1D,
  0x1F, 0x15, 0x1D,
  0x01, 0x01, 0x1F,
  0x1F, 0x15, 0x1F,
  0x17, 0x15, 0x1F]

theTetrisFont = [
    0x78,0x78,0x1E,0x1E, #S
    0x1E,0x1E,0x78,0x78, #Z
    0x00,0xFF,0xFF,0x00, #I
    0x06,0x06,0x7E,0x7E, #J
    0x7E,0x7E,0x06,0x06, #L
    0x3C,0x3C,0x3C,0x3C, #O
    0x7E,0x7E,0x18,0x18, #T
]

if PI:
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=4, blocks_arranged_in_reverse_order=True)
    pixel_pin = board.D18
    # The number of NeoPixels
    num_pixels = PIXEL_X*PIXEL_Y
    ORDER = neopixel.GRB
    pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=LED_BRIGHTNESS, auto_write=False,pixel_order=ORDER)

# key server for controller #

QKEYDOWN=0
QKEYUP=1

JKEY_X=3
JKEY_Y=4
JKEY_A=0
JKEY_B=1
JKEY_R=7
JKEY_L=6
JKEY_SEL=10
JKEY_START=11

mykeys =	{
  K_1: JKEY_A,
  K_2: JKEY_B,
  K_3: JKEY_Y,
  K_4: JKEY_X,
  K_x: JKEY_SEL,
  K_s: JKEY_START
}

mask = bytearray([1,2,4,8,16,32,64,128])

# main #

def main():

    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT
    global a1_counter ,RUNNING
    a1_counter=0
    RUNNING=True
    joystick_detected=False
    joystick_cnt=0

    if not PI:
        pygame.init()
        FPSCLOCK = pygame.time.Clock()
        DISPLAYSURF = pygame.display.set_mode((PIXEL_X*SIZE, PIXEL_Y*SIZE))
        BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
        BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
        pygame.display.set_caption('Pi Games')
        DISPLAYSURF.fill(BGCOLOR)
        pygame.display.update()
        drawImage('pi.bmp')
        time.sleep(2)
    else:
        device.contrast(200)
        pygame.init()
        drawImage('/home/pi/pi.bmp')
        pygame.joystick.init()
        while joystick_detected==False:
            show_message(device,"Waiting for controller...",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
            pygame.joystick.quit()
            pygame.joystick.init()
            try:
                joystick = pygame.joystick.Joystick(0) # create a joystick instance
                joystick.init() # init instance
                # print("Initialized joystick: {}".format(joystick.get_name()))
                joystick_detected = True
            except pygame.error:
                print("no joystick found.")
                joystick_detected = False

    clearScreen() 

    drawClock(1)
    if PI:
        show_message(device,"Let's play",fill="white", font=proportional(CP437_FONT))


    while True:
        clearScreen()
        #drawSymbols()
        if PI:
            drawImage('/home/pi/select.bmp')
        else: 
            drawImage('select.bmp')
        updateScreen()
        
        if not PI:
            checkForQuit()

        #check if joystick is still connected
        if PI:    
            if joystick_cnt==50:
                joystick_cnt=0
                pygame.joystick.quit()
                pygame.joystick.init()
                try:
                    joystick = pygame.joystick.Joystick(0) # create a joystick instance
                    joystick.init() # init instance
                    # print("Initialized joystick: {}".format(joystick.get_name()))
                    joystick_detected = True
                except pygame.error:
                    print("no joystick found.")
                    joystick_detected = False
            else:
                joystick_cnt+=1

        pygame.event.pump()
        for event in pygame.event.get():
            # print("event detected {}".format(event))
            if event.type == pygame.JOYBUTTONDOWN or event.type == KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                if (myevent == JKEY_B):
                  drawClock(1)
                if (myevent == JKEY_A):
                  runPongGame()
                if (myevent == JKEY_X):
                   runTetrisGame()
                if (myevent == JKEY_Y):
                  runSnakeGame() 
                if (myevent == JKEY_START):
                  shutdownScreen()
                  
            if event.type == pygame.QUIT: # get all the QUIT events
                terminate() # terminate if any QUIT events are present

        time.sleep(.1)
        

    terminate()

# gaming main routines #

def runPongGame():
    down = 0
    up = 1
    left = 0
    right = 1
    lowerbarx = PIXEL_X//2
    upperbarx = PIXEL_X//2
    score1 = 0
    score2 = 0
    ballx = PIXEL_X//2
    bally = PIXEL_Y//2
    directiony = down
    directionx = left
    movingRightUpper = False
    movingLeftUpper = False
    movingRightLower = False
    movingLeftLower = False
    restart=False
    lastLowerMoveSidewaysTime = time.time()
    lastUpperMoveSidewaysTime = time.time()

    while True: # main game loop
        
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                val = round(event.value)
                if (axis == 0 and val == -1):
                    movingLeftLower = True
                    movingRightLower = False
                if (axis == 0 and val == 1):
                    movingLeftLower = False
                    movingRightLower = True
                if (val == 0):
                    movingLeftLower = False
                    movingRightLower = False
        
            if event.type == pygame.JOYBUTTONDOWN:
                # print("Joystick button pressed: {}".format(event.button))
                if (event.button == JKEY_A):
                    movingLeftUpper = True
                    movingRightUpper = False
                if (event.button == JKEY_B):
                    movingLeftUpper = False
                    movingRightUpper = True
                if (event.button == JKEY_SEL):
                    # quit game
                    return

            if event.type == pygame.JOYBUTTONUP:
                    movingLeftUpper = False
                    movingRightUpper = False
            
            if event.type == pygame.KEYDOWN:
                if(event.key==K_LEFT):
                    movingLeftLower = True
                    movingRightLower = False
                if(event.key==K_RIGHT):
                    movingLeftLower = False
                    movingRightLower = True
                if(event.key==K_1):
                    movingLeftUpper = True
                    movingRightUpper = False
                if(event.key==K_2):
                    movingLeftUpper = False
                    movingRightUpper = True
                if(event.key==K_s):
                    return

            if event.type == pygame.KEYUP:
                movingLeftLower = False
                movingRightLower = False
                movingLeftUpper = False
                movingRightUpper = False

        if (movingLeftLower) and time.time() - lastLowerMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if lowerbarx >1:
                lowerbarx-=1;
            lastLowerMoveSidewaysTime = time.time()
        if (movingRightLower) and time.time() - lastLowerMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if lowerbarx <PIXEL_X-2:
                lowerbarx+=1;
            lastLowerMoveSidewaysTime = time.time()
        if (movingLeftUpper) and time.time() - lastUpperMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if upperbarx >1:
                upperbarx-=1;
            lastUpperMoveSidewaysTime = time.time()
        if (movingRightUpper) and time.time() - lastUpperMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if upperbarx <PIXEL_X-2:
                upperbarx+=1;
            lastUpperMoveSidewaysTime = time.time()

        if not PI:
                checkForQuit()

        if (directiony == up):
            if (bally>1):
                bally-=1
            else:
                if (abs(ballx-upperbarx)<2):
                    directiony = down
                    if (ballx==upperbarx+1):
                        if (directionx==left):
                            directionx=right
                    if (ballx==upperbarx-1):
                        if (directionx==right):
                            directionx=left
                elif ((ballx-upperbarx==2) and (directionx==left)):
                    directionx=right
                    directiony = down
                elif ((ballx-upperbarx==-2) and (directionx==right)):
                    directionx=left
                    directiony = down
                else:
                    bally-=1
                    score1+=1
                    restart = True
        else:
            if (bally<PIXEL_Y-2):
                bally+=1
            else:
                if (abs(ballx-lowerbarx)<2):
                    directiony = up
                    if (ballx==lowerbarx+1):
                        if (directionx==left):
                            directionx=right
                    if (ballx==lowerbarx-1):
                        if (directionx==right):
                            directionx=left
                elif ((ballx-lowerbarx==2) and (directionx==left)):
                    directionx=right
                    directiony = up
                elif ((ballx-lowerbarx==-2) and (directionx==right)):
                    directionx=left
                    directiony = up
                else:
                    bally+=1
                    score2+=1
                    restart = True

        if (directionx == left):
            if (ballx>0):
                if (ballx==1):
                   ballx-=1
                else:
                    ballx-=random.randint(1,2)
            else:
                directionx = right
                ballx+=1
                if(directiony == up):
                    if(bally>2):
                        bally-=1
                if(directiony == down):
                    if(bally<PIXEL_Y-2):
                        bally+=1
        else:
            if (ballx<PIXEL_X-1):
                if (ballx==8):
                   ballx+=1
                else:
                    ballx+=random.randint(1,2)
            else:
                directionx = left
                ballx-=random.randint(1,2)
                if(directiony == up):
                    if(bally>3):
                        bally-=random.randint(0,2)
                if(directiony == down):
                    if(bally<PIXEL_Y-3):
                        bally+=random.randint(0,2)
        clearScreen()
        drawBall(ballx,bally)
        drawBar(upperbarx,0)
        drawBar(lowerbarx,PIXEL_Y-1)
        twoscoreText(score1,score2)
        updateScreen()

        if (score1 == 9) or (score2 == 9):
            time.sleep(3)
            return

        if restart:
            time.sleep(1)
            ballx=PIXEL_X//2
            bally=PIXEL_Y//2
            if directiony==down:
                directiony = up
            else:
                directiony = down
            restart=False
        else:
            time.sleep(.1)

def runSnakeGame():
    
    # Set a random start point.
    startx = random.randint(2, BOARDWIDTH-2 )
    starty = random.randint(2, BOARDHEIGHT -2 )
    wormCoords = [{'x': startx,     'y': starty},
                  {'x': startx - 1, 'y': starty},
                  {'x': startx - 2, 'y': starty}]
    direction = RIGHT
    score = 0
    
    if os.path.isfile('/home/pi/hs_snake.p')==True:  
        try:
           highscore = pickle.load(open("/home/pi/hs_snake.p","rb"))
        except EOFError:
           highscore = 0
    else:
        highscore=0
    if PI:
        show_message(device,"Snake Highscore: " + str(highscore),fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)

    # Start the apple in a random place.
    apple = getRandomLocation(wormCoords)

    while True: # main game loop
        olddirection = direction
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                if (olddirection== direction):   #only one direction change per step
                    axis = event.axis
                    val = round(event.value)
                    if (axis == 0 and val == -1):
                        if direction != RIGHT:
                            direction = LEFT
                    if (axis == 0 and val == 1):
                        if direction != LEFT:
                            direction = RIGHT
                    if (axis == 1 and val == 1):
                        if direction != UP:
                            direction = DOWN
                    if (axis == 1 and val == -1):
                        if direction != DOWN:
                            direction = UP

            if event.type == pygame.KEYDOWN:
                if (event.key==K_LEFT):
                    if direction != RIGHT:
                        direction = LEFT
                if (event.key==K_RIGHT):
                    if direction != LEFT:
                        direction = RIGHT
                if (event.key==K_DOWN):
                    if direction != UP:
                        direction = DOWN
                if (event.key==K_UP):
                    if direction != DOWN:
                        direction = UP
                if (event.key == JKEY_SEL):
                    #quit game
                    return
            
            if event.type == pygame.JOYBUTTONDOWN:
                if (event.button==JKEY_SEL):
                    # quit game
                    return

        # check if the worm has hit itself or the edge
        if wormCoords[HEAD]['x'] == -1 or wormCoords[HEAD]['x'] == BOARDWIDTH or wormCoords[HEAD]['y'] == -1 or wormCoords[HEAD]['y'] == BOARDHEIGHT:
            time.sleep(1.5)
            if score > highscore:
                highscore = score
                if PI:
                    pickle.dump(highscore, open("/home/pi/hs_snake.p", "wb"))
                    show_message(device,"New Highscore !!!",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
            return # game over
        for wormBody in wormCoords[1:]:
            if wormBody['x'] == wormCoords[HEAD]['x'] and wormBody['y'] == wormCoords[HEAD]['y']:
                time.sleep(1.5)
                if score > highscore:
                    highscore = score
                    if PI:
                        pickle.dump(highscore, open("/home/pi/hs_snake.p", "wb"))
                        show_message(device,"New Highscore !!!",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
                return # game over

        # check if worm has eaten an apple
        if wormCoords[HEAD]['x'] == apple['x'] and wormCoords[HEAD]['y'] == apple['y']:
            # don't remove worm's tail segment
            score += 1
            apple = getRandomLocation(wormCoords) # set a new apple somewhere
        else:
            del wormCoords[-1] # remove worm's tail segment

        # move the worm by adding a segment in the direction it is moving
        if direction == UP:
            if wormCoords[HEAD]['y'] == 0 :
                newHead = {'x': wormCoords[HEAD]['x'], 'y': BOARDHEIGHT-1}
            else:
                newHead = {'x': wormCoords[HEAD]['x'], 'y': wormCoords[HEAD]['y'] - 1}
        elif direction == DOWN:
            if wormCoords[HEAD]['y'] == BOARDHEIGHT-1 :
                newHead = {'x': wormCoords[HEAD]['x'], 'y': 0}
            else:
                newHead = {'x': wormCoords[HEAD]['x'], 'y': wormCoords[HEAD]['y'] + 1}
        elif direction == LEFT:
            if wormCoords[HEAD]['x'] == 0 :
                newHead = {'x': BOARDWIDTH -1, 'y': wormCoords[HEAD]['y'] }
            else:
                newHead = {'x': wormCoords[HEAD]['x'] - 1, 'y': wormCoords[HEAD]['y']}
        elif direction == RIGHT:
            if wormCoords[HEAD]['x'] == BOARDWIDTH-1:
                newHead = {'x': 0, 'y': wormCoords[HEAD]['y']}
            else:
                newHead = {'x': wormCoords[HEAD]['x'] + 1, 'y': wormCoords[HEAD]['y']}
        if not PI:
            checkForQuit()
        wormCoords.insert(0, newHead)
        clearScreen()
        drawWorm(wormCoords)
        drawApple(apple)
        scoreText(score)
        updateScreen()
        time.sleep(.15)

def runTetrisGame():
    # setup varia
    # bles for the start of the game
    #if PI:
        #device.contrast(255)
        #device.show()
    board = getBlankBoard()
    lastMoveDownTime = time.time()
    lastMoveSidewaysTime = time.time()
    lastFallTime = time.time()
    movingDown = False # note: there is no movingUp variable
    movingLeft = False
    movingRight = False
    score = 0
    oldscore = -1
    oldpiece = 10
    lines = 0
    level, fallFreq = calculateLevelAndFallFreq(lines)
    if os.path.isfile('/home/pi/hs_tetris.p')==True:  
        try:
           highscore = pickle.load(open("/home/pi/hs_tetris.p","rb"))
        except EOFError:
           highscore = 0
    else:
        highscore=0
    if PI:
        show_message(device,"Tetris Highscore: " + str(highscore),fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
    

    fallingPiece = getNewPiece()
    nextPiece = getNewPiece()


    while True: # game loop


        if fallingPiece == None:
            # No falling piece in play, so start a new piece at the top
            fallingPiece = nextPiece
            nextPiece = getNewPiece()
            lastFallTime = time.time() # reset lastFallTime

            if not isValidPosition(board, fallingPiece):
                time.sleep(2)
                if score > highscore:
                    highscore = score
                    if PI:
                        pickle.dump(highscore, open("/home/pi/hs_tetris.p", "wb"))
                        show_message(device,"New Highscore !!!",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
                
                return # can't fit a new piece on the board, so game over
        if not PI:
            checkForQuit()

        pygame.event.pump()
        for event in pygame.event.get():
            # print("event detected {}".format(event))
            if event.type == pygame.JOYAXISMOTION:
              axis = event.axis
              val = round(event.value)
              if (axis == 0 and val == 0):
                # no motion or down motion
                movingLeft = movingRight = False
              
              if (axis == 1 and val == 0) :
                movingDown = False

              if (axis==0 and val== -1) and isValidPosition(board, fallingPiece, adjX=-1):
                fallingPiece['x'] -= 1
                movingLeft = True
                movingRight = False
                lastMoveSidewaysTime = time.time()

              if (axis == 0 and val== 1) and isValidPosition(board, fallingPiece, adjX=1):
                fallingPiece['x'] += 1
                movingLeft = False
                movingRight = True
                lastMoveSidewaysTime = time.time()

              if (axis==1 and val == 1):
                movingDown = True
                if isValidPosition(board, fallingPiece, adjY=1):
                    fallingPiece['y'] += 1
                lastMoveDownTime = time.time()

              if (axis==1 and val == -1):
                 fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                 if not isValidPosition(board, fallingPiece):
                      fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])

            if event.type == pygame.KEYDOWN:   

              if (event.key==K_LEFT) and isValidPosition(board, fallingPiece, adjX=-1):
                fallingPiece['x'] -= 1
                movingLeft = True
                movingRight = False
                lastMoveSidewaysTime = time.time()

              if (event.key==K_RIGHT) and isValidPosition(board, fallingPiece, adjX=1):
                fallingPiece['x'] += 1
                movingLeft = False
                movingRight = True
                lastMoveSidewaysTime = time.time()

              if (event.key==K_DOWN):
                movingDown = True
                if isValidPosition(board, fallingPiece, adjY=1):
                    fallingPiece['y'] += 1
                lastMoveDownTime = time.time()

              if (event.key==K_UP):
                 fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                 if not isValidPosition(board, fallingPiece):
                      fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
              
              if (event.key == K_3):
                    fallingPiece['rotation'] = (fallingPiece['rotation'] -1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
              
              if (event.key == K_4):
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    score+=i #TODO: more digits on numbercounter, more scores
                    fallingPiece['y'] += i - 1

            if event.type == pygame.KEYUP:
                movingDown = False
                movingLeft = False
                movingRight = False

            

            if event.type == pygame.JOYBUTTONDOWN:
                # print("Joystick button pressed: {}".format(event.button))
                if (event.button == JKEY_A):
                    fallingPiece['rotation'] = (fallingPiece['rotation'] -1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                if (event.button == JKEY_Y):
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    score+=i #TODO: more digits on numbercounter, more scores
                    fallingPiece['y'] += i - 1

                #  return


        # handle moving the piece because of user input
        if (movingLeft or movingRight) and time.time() - lastMoveSidewaysTime > MOVESIDEWAYSFREQ:
            if movingLeft and isValidPosition(board, fallingPiece, adjX=-1):
                fallingPiece['x'] -= 1
            elif movingRight and isValidPosition(board, fallingPiece, adjX=1):
                fallingPiece['x'] += 1
            lastMoveSidewaysTime = time.time()

        if movingDown and time.time() - lastMoveDownTime > MOVEDOWNFREQ and isValidPosition(board, fallingPiece, adjY=1):
            fallingPiece['y'] += 1
            lastMoveDownTime = time.time()

        # let the piece fall if it is time to fall
        if time.time() - lastFallTime > fallFreq:
            # see if the piece has landed
            if not isValidPosition(board, fallingPiece, adjY=1):
                # falling piece has landed, set it on the board
                addToBoard(board, fallingPiece)
                remLine = removeCompleteLines(board)
                # count lines for level calculation
                lines += remLine
                # more lines, more points per line
                score += SCORES[remLine]*level
                level, fallFreq = calculateLevelAndFallFreq(lines)
                fallingPiece = None
            else:
                # piece did not land, just move the piece down
                fallingPiece['y'] += 1
                lastFallTime = time.time()

        # drawing everything on the screen
        clearScreen()
        drawBoard(board)
        #scoreText(score)
        if score>oldscore:
            scoreTetris(score,level,PIECES_ORDER.get(nextPiece['shape']))
            oldscore = score
        if oldpiece!=PIECES_ORDER.get(nextPiece['shape']):
            scoreTetris(score,level,PIECES_ORDER.get(nextPiece['shape']))
            oldpiece=PIECES_ORDER.get(nextPiece['shape'])
        #drawStatus(score, level)
        #drawNextPiece(nextPiece)
        if fallingPiece != None:
            drawPiece(fallingPiece)

        updateScreen()
        #FPSCLOCK.tick(FPS)
        time.sleep(.05)

def drawClock(color):
    joystick_cnt=0
    
    if PI:
        device.clear();
        device.show();

    hour =  time.localtime().tm_hour
    minute= time.localtime().tm_min
    second= time.localtime().tm_sec

    while True:

        pygame.event.pump()
        for event in pygame.event.get(): # User did something
            # print("event detected {}".format(event))
            # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            if event.type == pygame.JOYBUTTONDOWN or event.type == KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                # print("Joystick button pressed: {}".format(event.button))
                if (myevent==JKEY_X):
                  # print("exiting clock")
                  clearScreen()
                  updateScreen()
                  return
                if (myevent == JKEY_A):
                  color = color + 1
                  if (color > (len(COLORS) - 1)):
                    color = 0
 
            if event.type == pygame.QUIT: # get all the QUIT events
                terminate() # terminate if any QUIT events are present

        #check if joystick is still connected
        if PI:    
            if joystick_cnt==25:
                joystick_cnt=0
                pygame.joystick.quit()
                pygame.joystick.init()
                try:
                    joystick = pygame.joystick.Joystick(0) # create a joystick instance
                    joystick.init() # init instance
                    # print("Initialized joystick: {}".format(joystick.get_name()))
                    #joystick_detected = True
                except pygame.error:
                    print("no joystick found.")
                    #joystick_detected = False
            else:
                joystick_cnt+=1

        ltime =  time.localtime()
        hour = ltime.tm_hour
        minute= ltime.tm_min
        second= ltime.tm_sec
        clearScreen()

        drawnumber(int(hour/10),2,1,color)
        drawnumber(int(hour%10),6,1,color)
        drawnumber(int(minute/10),2,8,color)
        drawnumber(int(minute%10),6,8,color)
        drawnumber(int(second/10),2,15,color)
        drawnumber(int(second%10),6,15,color)

        updateScreen()
        time.sleep(.2)

def shutdownScreen():
        
    if PI:
        device.clear();
        device.show();
        drawImage('/home/pi/shutdown.bmp')
        show_message(device,"Press Select to shutdown!",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
    else:
        drawImage('shutdown.bmp')
       
    while True:

        pygame.event.pump()
        for event in pygame.event.get(): # User did something
            # print("event detected {}".format(event))
            # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
            if event.type == pygame.JOYBUTTONDOWN or event.type == KEYDOWN:
                if event.type == pygame.JOYBUTTONDOWN:
                    myevent = event.button
                else:
                    if event.key in mykeys:
                        myevent = mykeys[event.key]
                    else:
                        myevent = -1
                # print("Joystick button pressed: {}".format(event.button))
                if (myevent!=JKEY_SEL):
                    # print("exiting clock")
                    clearScreen()
                    updateScreen()
                    return
                else: 
                    if not PI:
                        terminate()
                    else:
                        clearScreen()
                        updateScreen()
                        show_message(device,"Shutdown...",fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
                        subprocess.Popen(['shutdown','-h','now'])
                        #call("sudo nohup shutdown -h now", shell=True)
                        terminate()
            if event.type == pygame.QUIT: # get all the QUIT events
                terminate() # terminate if any QUIT events are present

        updateScreen()
        time.sleep(.2)

def drawImage(filename):
    im = Image.open(filename)
    for row in range(0,BOARDHEIGHT):
        for col in range(0,BOARDWIDTH):
            r,g,b = im.getpixel((col,row))
            drawPixelRgb(col,row,r,g,b)
    updateScreen()

def drawHalfImage(filename,offset):
    im = Image.open(filename)
    if offset>10:
        offset = 10
    for row in range(0,10):
        for col in range(0,10):
            r,g,b = im.getpixel((col,row))
            drawPixelRgb(col,row+offset,r,g,b)

# drawing #

def clearScreen():
    if PI:
        pixels.fill((0,0,0))
    else:
        DISPLAYSURF.fill(BGCOLOR)

def updateScreen():
    if PI:
        pixels.show()
    else:
        pygame.display.update()

def drawPixel(x,y,color):
    if color == BLANK:
        return
    if PI:
        try:
            if (x>=0 and y>=0 and color >=0):
                if x%2==1:
                    pixels[x*PIXEL_Y+y] = COLORS[color]
                else:
                    pixels[x*PIXEL_Y+(PIXEL_Y-1-y)] = COLORS[color]
        except:
            print(str(x) + ' --- ' + str(y))    
    else:
        pygame.draw.rect(DISPLAYSURF, COLORS[color], (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))

def drawPixelRgb(x,y,r,g,b):
    if PI:
        if (x>=0 and y>=0):
            if x%2==1:
                pixels[x*PIXEL_Y+y] = (r,g,b)
            else:
                pixels[x*PIXEL_Y+(PIXEL_Y-1-y)] = (r,g,b)
    else:
        pygame.draw.rect(DISPLAYSURF, (r,g,b), (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))

def drawnumber(number,offsetx,offsety,color):
    for x in range(0,3):
        for y in range(0,5):
            if clock_font[3*number + x]&mask[y]:
                drawPixel(offsetx+x,offsety+y,color)

def drawnumberMAX7219(number,offsetx,offsety,draw1):
    for x in range(0,3):
        for y in range(0,5):
            if clock_font[3*number+2- x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,1,draw1)
            elif clock_font[3*number+2- x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,0,draw1)

def drawTetrisMAX7219(piece,offsetx,offsety,draw1):
        for x in range(0,4):
            for y in range(0,8):
                if theTetrisFont[4*piece + x]&mask[y]:
                    drawScorePixel(offsetx+x,offsety+y,1,draw1)
                elif theTetrisFont[4*piece + x]&mask[y]:
                    drawScorePixel(offsetx+x,offsety+y,0,draw1)

def drawScorePixel(x,y,on,draw):
    if PI:
        draw.point((31-x,y), fill= "white")
        #time.sleep(.01)
    else:
        pygame.draw.rect(DISPLAYSURF, COLORS[2], (64-2*x, 410+2*y,2,2))

def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def scrollText(text):
    if PI:
        show_message(device,text,fill="white", font=proportional(CP437_FONT))
    else:
        titleSurf, titleRect = makeTextObjs(str(text), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

def scoreText(score):
    _score=score
    if _score>999:
        _score = 999
    if PI:
        with canvas(device) as draw:
            for i in range(0,3):
                text(draw, ((3-i)*8, 0), str(_score%10), fill="white")
                _score //=10
    else:
        titleSurf, titleRect = makeTextObjs(str(_score), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

def scoreTetris(score,level,nextpiece):
    #if PI:
        #device.clear()
    _score=score
    if _score>999999:
        _score = 999999
   
    if PI:
      # one point per level
      with canvas(device) as draw1:
        for i in range(0,level):
            drawScorePixel(i*2,7,1,draw1)

        # score as 6 digit value
        for i in range(0,6):
            drawnumberMAX7219(_score%10,i*4,0,draw1)
            _score //=10

        # draw next piece
        drawTetrisMAX7219(nextpiece,27,0,draw1)

        if PI:
            device.show()

def twoscoreText(score1,score2):
    _score1=score1
    _score2=score2
    if _score1>9:
        _score1 = 9
    if _score2>9:
        _score2 = 9
    if PI:
        with canvas(device) as draw:
            text(draw, (0, 0), str(_score1), fill="white")
            text(draw, (8, 0), ":", fill="white")
            text(draw, (16, 0), str(_score2), fill="white")
            text(draw, (24, 0), " ", fill="white")
    else:
        titleSurf, titleRect = makeTextObjs(str(_score1)+':'+str(_score2), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

# program flow #

def terminate():
    RUNNING = False
    pygame.quit()
    exit()

def checkForQuit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back

# tetris subroutines #

def calculateLevelAndFallFreq(lines):
    # Based on the score, return the level the player is on and
    # how many seconds pass until a falling piece falls one space.
    level = int(lines / 10) + 1
    # limit level to 10
    if level >10:
        level = 10
    fallFreq = FALLING_SPEED - (level * 0.05)
    if fallFreq <= 0.05:
        fallFreq = 0.05
    return level, fallFreq

def getNewPiece():
    # return a random new piece in a random rotation and color
    shape = random.choice(list(PIECES.keys()))
    newPiece = {'shape': shape,
                'rotation': random.randint(0, len(PIECES[shape]) - 1),
                'x': int(BOARDWIDTH / 2) - int(TEMPLATEWIDTH / 2),
                'y': -2, # start it above the board (i.e. less than 0)
                'color': PIECES_ORDER.get(shape)}
    return newPiece

def addToBoard(board, piece):
    # fill in the board based on piece's location, shape, and rotation
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if PIECES[piece['shape']][piece['rotation']][y][x] != BLANK:
                board[x + piece['x']][y + piece['y']] = piece['color']

def isOnBoard(x, y):
    return x >= 0 and x < BOARDWIDTH and y < BOARDHEIGHT

def isValidPosition(board, piece, adjX=0, adjY=0):
    # Return True if the piece is within the board and not colliding
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            isAboveBoard = y + piece['y'] + adjY < 0
            if isAboveBoard or PIECES[piece['shape']][piece['rotation']][y][x] == BLANK:
                continue
            if not isOnBoard(x + piece['x'] + adjX, y + piece['y'] + adjY):
                return False
            if board[x + piece['x'] + adjX][y + piece['y'] + adjY] != BLANK:
                return False
    return True

def isCompleteLine(board, y):
    # Return True if the line filled with boxes with no gaps.
    for x in range(BOARDWIDTH):
        if board[x][y] == BLANK:
            return False
    return True

def removeCompleteLines(board):
    # Remove any completed lines on the board, move everything above them down, and return the number of complete lines.
    numLinesRemoved = 0
    y = BOARDHEIGHT - 1 # start y at the bottom of the board
    while y >= 0:
        if isCompleteLine(board, y):
            # Remove the line and pull boxes down by one line.
            for pullDownY in range(y, 0, -1):
                for x in range(BOARDWIDTH):
                    board[x][pullDownY] = board[x][pullDownY-1]
            # Set very top line to blank.
            for x in range(BOARDWIDTH):
                board[x][0] = BLANK
            numLinesRemoved += 1
            # Note on the next iteration of the loop, y is the same.
            # This is so that if the line that was pulled down is also
            # complete, it will be removed.
        else:
            y -= 1 # move on to check next row up
    return numLinesRemoved

def drawBoard(matrix):
    for i in range(0,BOARDWIDTH):
        for j in range(0,BOARDHEIGHT):
            drawPixel(i,j,matrix[i][j])

def getBlankBoard():
    # create and return a new blank board data structure
    board = []
    for i in range(BOARDWIDTH):
        board.append([BLANK] * BOARDHEIGHT)
    return board

def drawPiece(piece, pixelx=None, pixely=None):
    shapeToDraw = PIECES[piece['shape']][piece['rotation']]
    if pixelx == None and pixely == None:
        # if pixelx & pixely hasn't been specified, use the location stored in the piece data structure
        pixelx=piece['x']
        pixely=piece['y']

    # draw each of the boxes that make up the piece
    for x in range(TEMPLATEWIDTH):
        for y in range(TEMPLATEHEIGHT):
            if shapeToDraw[y][x] != BLANK:
                drawPixel( pixelx+ x , pixely+y,piece['color'])

# snake subroutines #

def getRandomLocation(wormCoords):
    while True:
        x = random.randint(0, BOARDWIDTH - 1)
        y = random.randint(0, BOARDHEIGHT - 1)
        if {'x': x, 'y': y} in wormCoords:
            print('no apples on worm')
        else:
            break
    return {'x': x, 'y': y}

def drawWorm(wormCoords):
    for coord in wormCoords:
        x = coord['x']
        y = coord['y']
        drawPixel(x,y,1)

def drawApple(coord):
    x = coord['x']
    y = coord['y']
    drawPixel(x,y,2)

# pong subroutines #

def drawBar(x,y):
    drawPixel(x-1,y,1)
    drawPixel(x,y,1)
    drawPixel(x+1,y,1)

def drawBall(x,y):
    drawPixel(x,y,0)

if __name__ == '__main__':
    main()
