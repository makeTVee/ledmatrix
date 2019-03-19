# WS2812 LED Matrix Gamecontrol (Tetris, Snake, Pong)
# by M Oehler
# https://hackaday.io/project/11064-raspberry-pi-retro-gaming-led-display
# ported from
# Tetromino (a Tetris clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, time, sys, socket, threading, queue, socketserver, os
from PIL import Image

# If Pi = False the script runs in simulation mode using pygame lib
PI = False
import pygame
from pygame.locals import *
if PI:
    import serial
    import max7219.led as led
    from max7219.font import proportional, SINCLAIR_FONT, TINY_FONT, CP437_FONT

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

BUTTON_BLUE=4
BUTTON_GREEN=5
BUTTON_RED=6
BUTTON_YELLOW=7

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

# serial port pi #

if PI:
    serport=serial.Serial("/dev/ttyAMA0",baudrate= 500000,timeout=3.0)
    device = led.matrix(cascaded=4)

# key server for controller #

QKEYDOWN=0
QKEYUP=1
myQueue = queue.Queue()
mask = bytearray([1,2,4,8,16,32,64,128])

class qEvent:
   def __init__(self, key, type):
        self.key = key
        self.type = type

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        oldstr=b'\x80'  #create event on connection start (0x80 != 0x00)
        while RUNNING:
            data = self.request.recv(1)
            #cur_thread = threading.current_thread()
            #response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
            if data:
                if data!=oldstr:
                    #print(str(time.time()) + ' -- ' + str(oldstr))
                    for i in range (0,8):
                        if (bytes(data[0]&mask[i])!=bytes(oldstr[0]&mask[i])) :
                            if (bytes(data[0]&mask[i])):
                                myQueue.put(qEvent(i,QKEYDOWN))
                            else:
                                myQueue.put(qEvent(i,QKEYUP))
                oldstr = data
                #print(data)
            #self.request.sendall(response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))
    finally:
        sock.close()

# main #

def main():

    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT
    global a1_counter ,RUNNING
    a1_counter=0
    RUNNING=True

    if not PI:
        pygame.init()
        FPSCLOCK = pygame.time.Clock()
        DISPLAYSURF = pygame.display.set_mode((PIXEL_X*SIZE, PIXEL_Y*SIZE))
        BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
        BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
        pygame.display.set_caption('Pi Games')
    else:
        # audio disabled
#        os.environ["SDL_VIDEODRIVER"] = "dummy" #dummy display for pygame audio
#        pygame.init()
#        pygame.mixer.music.load('tetrisb.mid')
        device.brightness(1)
        device.show_message("Waiting for controller...", font=proportional(CP437_FONT),delay=0.015)

    # Port 0 means to select an arbitrary unused port

    HOST, PORT = '', 4711

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    clearScreen()

    drawClock(1)
    if PI:
        device.show_message("Let's play", font=proportional(CP437_FONT),delay=0.03)

    while True:

        clearScreen()
        drawSymbols()
        while myQueue.empty():
            time.sleep(.1)
            a1_counter+=1
            updateScreen()
            if not PI:
                checkForQuit()
            time.sleep(.1)

        event = myQueue.get()

        if event.type == QKEYDOWN:
            if (event.key == BUTTON_BLUE):
                runSnakeGame()
            elif (event.key == BUTTON_YELLOW):
#                if PI:
#                    pygame.mixer.music.play(-1,0.0)
                runTetrisGame()
#                if PI:
#                    pygame.mixer.music.stop()
            elif (event.key == BUTTON_RED):
                runPongGame()
            elif (event.key == BUTTON_GREEN):
                drawClock(1)

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
        while not myQueue.empty():
            event = myQueue.get()
            if event.type == QKEYDOWN:
                if (event.key == 0):
                    movingLeftLower = True
                    movingRightLower = False
                elif (event.key == 1):
                    movingLeftLower = False
                    movingRightLower = True
                elif (event.key == BUTTON_YELLOW):
                    movingLeftUpper = True
                    movingRightUpper = False
                elif (event.key == BUTTON_GREEN):
                    movingLeftUpper = False
                    movingRightUpper = True
                elif event.key == BUTTON_RED:
                     return
            if event.type == QKEYUP:
                if (event.key == 0):
                    movingLeftLower =False
                elif (event.key == 1):
                    movingRightLower = False
                elif (event.key == BUTTON_YELLOW):
                    movingLeftUpper = False
                elif (event.key == BUTTON_GREEN):
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
                ballx-=1
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

    # Start the apple in a random place.
    apple = getRandomLocation()

    while True: # main game loop
        if not myQueue.empty():
            event = myQueue.get()
            # take only one input per run
            while not myQueue.empty():
                myQueue.get()
            if event.type == QKEYDOWN:
                if (event.key == 0) and direction != RIGHT:
                    direction = LEFT
                elif (event.key == 1) and direction != LEFT:
                    direction = RIGHT
                elif (event.key == 2) and direction != DOWN:
                    direction = UP
                elif (event.key == 3) and direction != UP:
                    direction = DOWN
                elif (event.key == BUTTON_RED):
                     return

        # check if the worm has hit itself or the edge
        if wormCoords[HEAD]['x'] == -1 or wormCoords[HEAD]['x'] == BOARDWIDTH or wormCoords[HEAD]['y'] == -1 or wormCoords[HEAD]['y'] == BOARDHEIGHT:
            time.sleep(1.5)
            return # game over
        for wormBody in wormCoords[1:]:
            if wormBody['x'] == wormCoords[HEAD]['x'] and wormBody['y'] == wormCoords[HEAD]['y']:
                time.sleep(1.5)
                return # game over

        # check if worm has eaten an apple
        if wormCoords[HEAD]['x'] == apple['x'] and wormCoords[HEAD]['y'] == apple['y']:
            # don't remove worm's tail segment
            score += 1
            apple = getRandomLocation() # set a new apple somewhere
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
    if PI:
        device.brightness(1)
        device.flush()
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

    fallingPiece = getNewPiece()
    nextPiece = getNewPiece()


    while True: # game loop

        #if not myQueue.empty():
        #    print(myQueue.get().type)

        if fallingPiece == None:
            # No falling piece in play, so start a new piece at the top
            fallingPiece = nextPiece
            nextPiece = getNewPiece()
            lastFallTime = time.time() # reset lastFallTime

            if not isValidPosition(board, fallingPiece):
                time.sleep(2)
                return # can't fit a new piece on the board, so game over
        if not PI:
            checkForQuit()

        while not myQueue.empty():
            event = myQueue.get()
            if event.type == QKEYUP:
                if (event.key == 7):

                    lastFallTime = time.time()
                    lastMoveDownTime = time.time()
                    lastMoveSidewaysTime = time.time()
                elif (event.key == 0):
                    movingLeft = False
                elif (event.key == 1):
                    movingRight = False
                elif (event.key == 3):
                    movingDown = False

            elif event.type == QKEYDOWN:
                # moving the piece sideways
                if (event.key == 0) and isValidPosition(board, fallingPiece, adjX=-1):
                    fallingPiece['x'] -= 1
                    movingLeft = True
                    movingRight = False
                    lastMoveSidewaysTime = time.time()

                elif (event.key == 1) and isValidPosition(board, fallingPiece, adjX=1):
                    fallingPiece['x'] += 1
                    movingRight = True
                    movingLeft = False
                    lastMoveSidewaysTime = time.time()

                # rotating the piece (if there is room to rotate)
                elif (event.key == 2):
                    fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                elif (event.key == 5): # rotate the other direction
                    fallingPiece['rotation'] = (fallingPiece['rotation'] - 1) % len(PIECES[fallingPiece['shape']])
                    if not isValidPosition(board, fallingPiece):
                        fallingPiece['rotation'] = (fallingPiece['rotation'] + 1) % len(PIECES[fallingPiece['shape']])

                # making the piece fall faster with the down key
                elif (event.key == 3):
                    movingDown = True
                    if isValidPosition(board, fallingPiece, adjY=1):
                        fallingPiece['y'] += 1
                    lastMoveDownTime = time.time()

                # move the current piece all the way down
                elif event.key == 4:
                    movingDown = False
                    movingLeft = False
                    movingRight = False
                    for i in range(1, BOARDHEIGHT):
                        if not isValidPosition(board, fallingPiece, adjY=i):
                            break
                    score+=i #TODO: more digits on numbercounter, more scores
                    fallingPiece['y'] += i - 1

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

def drawSymbols():
     #snbake symbol
    drawPixel(1,2,0)
    drawPixel(2,2,0)
    drawPixel(1,3,0)
    drawPixel(1,4,0)
    drawPixel(2,3,0)
    drawPixel(2,4,0)
    drawPixel(5,3,2)
    drawPixel(6,3,1)
    drawPixel(7,3,1)
    drawPixel(8,3,1)
    drawPixel(8,2,1)
    drawPixel(8,1,1)

    #pong symbol
    drawPixel(1,9,2)
    drawPixel(2,9,2)
    drawPixel(1,10,2)
    drawPixel(2,10,2)
    drawPixel(1,11,2)
    drawPixel(2,11,2)
    drawPixel(5,9,1)
    drawPixel(6,9,1)
    drawPixel(7,9,1)
    drawPixel(6,11,0)


    #tetris symbol
    drawPixel(1,16,3)
    drawPixel(2,16,3)
    drawPixel(1,17,3)
    drawPixel(1,18,3)
    drawPixel(2,17,3)
    drawPixel(2,18,3)
    drawPixel(7,16,0)
    drawPixel(6,16,0)
    drawPixel(6,17,0)
    drawPixel(6,18,0)

def drawClock(color):

    if PI:
        device.clear();
        device.flush();

    hour =  time.localtime().tm_hour
    minute= time.localtime().tm_min
    second= time.localtime().tm_sec

    while True:
        while not myQueue.empty():
            event = myQueue.get()
            if event.type == QKEYDOWN:
                if (event.key == 5):
                    # Pausing the game
                    return;
            elif event.type == QKEYUP:
                if (event.key == 7):
                    # Pausing the game
                    return;
        if not PI:
                checkForQuit()

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
        serport.write(bytearray([32]))
    else:
        DISPLAYSURF.fill(BGCOLOR)

def updateScreen():
    if PI:
        serport.write(bytearray([30]))
    else:
        pygame.display.update()

def drawPixel(x,y,color):
    if color == BLANK:
        return
    if PI:
        if (x>=0 and y>=0 and color >=0):
            serport.write(bytearray([26,x,y,color]))
    else:
        pygame.draw.rect(DISPLAYSURF, COLORS[color], (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))

def drawPixelRgb(x,y,r,g,b):
    if PI:
        if (x>=0 and y>=0):
            serport.write(bytearray([24,x,y,r,g,b]))
    else:
        pygame.draw.rect(DISPLAYSURF, (r,g,b), (x*SIZE+1, y*SIZE+1, SIZE-2, SIZE-2))

def drawnumber(number,offsetx,offsety,color):
    for x in range(0,3):
        for y in range(0,5):
            if clock_font[3*number + x]&mask[y]:
                drawPixel(offsetx+x,offsety+y,color)

def drawnumberMAX7219(number,offsetx,offsety):
    for x in range(0,3):
        for y in range(0,5):
            if clock_font[3*number+2- x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,1)
            elif clock_font[3*number+2- x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,0)

def drawTetrisMAX7219(piece,offsetx,offsety):
    for x in range(0,4):
        for y in range(0,8):
            if theTetrisFont[4*piece + x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,1)
            elif theTetrisFont[4*piece + x]&mask[y]:
                drawScorePixel(offsetx+x,offsety+y,0)

def drawScorePixel(x,y,on):
    if PI:
        device.pixel(31-x,y,on,False)
    else:
        pygame.draw.rect(DISPLAYSURF, COLORS[2], (64-2*x, 410+2*y,2,2))

def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def scrollText(text):
    if PI:
        device.show_message(text, font=proportional(CP437_FONT))
    else:
        titleSurf, titleRect = makeTextObjs(str(text), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

def scoreText(score):
    _score=score
    if _score>9999:
        _score = 9999
    if PI:
        for i in range(0,4):
            device.letter(3-i, ord('0') + (_score%10))
            _score //=10
    else:
        titleSurf, titleRect = makeTextObjs(str(_score), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

def scoreTetris(score,level,nextpiece):
    if PI:
        device.clear()
    _score=score
    if _score>999999:
        _score = 999999

    # one point per level
    for i in range(0,level):
        drawScorePixel(i*2,7,1)

    # score as 6 digit value
    for i in range(0,6):
        drawnumberMAX7219(_score%10,i*4,0)
        _score //=10

    # draw next piece
    drawTetrisMAX7219(nextpiece,27,0)

    if PI:
        device.flush()

def twoscoreText(score1,score2):
    _score1=score1
    _score2=score2
    if _score1>9:
        _score1 = 9
    if _score2>9:
        _score2 = 9
    if PI:
        device.letter(0, ord('0') + (_score1))
        device.letter(1, ord(':'))
        device.letter(2, ord('0') + (_score2))
        device.letter(3, ord(' '))
    else:
        titleSurf, titleRect = makeTextObjs(str(_score1)+':'+str(_score2), BASICFONT, TEXTCOLOR)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

# program flow #

def terminate():
    RUNNING = False
    if not PI:
        pygame.quit()
    sys.exit()

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

def getRandomLocation():
    return {'x': random.randint(0, BOARDWIDTH - 1), 'y': random.randint(0, BOARDHEIGHT - 1)}

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
