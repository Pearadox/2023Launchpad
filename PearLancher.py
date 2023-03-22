import sys, time
import pygame
from networktables import NetworkTables
from Libraries import launchpad

# Network tables config:
teamNumber = "5414"
tableName = "Launchpad"

# LED Arrays:
leds = [
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
    [[30,30,63],[0,0,0],[0,0,0],[15,63,45],[0,0,0],[0,0,0],[63,20,0],[25,60,0],[0,0,0]],
    [[20,20,63],[0,63,63],[0,0,0],[0,63,30],[0,0,0],[0,0,0],[63,10,0],[12,40,0],[0,0,0]],
    [[10,10,63],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,30,0],[30,0,63]],
    [[0,0,63],[0,0,0],[63,0,30],[63,20,40],[0,0,0],[0,0,0],[63,30,0],[0,0,0],[0,0,0]],
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[63,0,0]],
    [[30,0,63],[30,0,63],[30,0,63],[30,0,63],[30,0,63],[30,0,63],[30,0,63],[30,0,63],[30,0,63]],
    [[256,256,0],[30,0,211],[256,256,0],[256,256,0],[30,0,211],[256,256,0],[256,256,0],[30,0,211],[256,256,0]],
    [[256,256,0],[30,0,63],[256,256,0],[256,256,0],[30,0,211],[256,256,0],[256,256,0],[30,0,211],[256,256,0]]
]

# Current button status:
btns = [[False for x in range(9)] for y in range(9)]
#Make buttons to determine if scored
scored = [[False for x in range(9)] for y in range(9)]
# reset pattern counter
resetSenseTime = 0
isPattern = False
willReset = False

# create a Launchpad instance
if launchpad.LaunchpadMk2().Check(0):
    lp = launchpad.LaunchpadMk2()
    mini = False
elif launchpad.LaunchpadMiniMk3().Check(1):
    lp = launchpad.LaunchpadMiniMk3()
    mini = True

# initialize networktables
NetworkTables.initialize(server='roborio-'+teamNumber+'-frc.local')
nt = NetworkTables.getTable(tableName)
ntScored = NetworkTables.getTable("Scored")

# Rio connection monitor
lastPingValue = False
lastPingValueTime = 0
pingMaxTimeMillis = 500
lastPressed = 0
lastGridButtPress = [-1,-1]
lastFlashed = 0

def main():
    global btns
    # open the first Launchpad
    if not mini:
        if lp.Open(0):
            print(" - Launchpad Mk2: OK")
    elif lp.Open(1):
        print(" - Launchpad MiniMK3: OK")
    else:
        print(" - Launchpad: ERROR (most likely not connected)")

    # Clear the buffer because the Launchpad remembers everything
    lp.ButtonFlush()
    lp.Reset()

    nt.putBoolean('ConeMode', False)
    nt.putBoolean('CubeMode', True)


    btns = [[False for x in range(9)] for y in range(9)]

    pygame.time.wait(100)

    # Set LED colors to default defined
    for r in range(9):
        for c in range(9):
            setColor(r, c, leds[r][c][0], leds[r][c][1], leds[r][c][2])
    setColor(0, 7, leds[0][7][0], leds[0][7][1], leds[0][7][2])

    while 1:
        # pygame.time.wait(10)

        # call looper
        looper()

        # update button events
        stateArray = lp.ButtonStateXY()
        if(stateArray==[]):
            continue

        # update buttons
        row = str(stateArray[1])
        column = str(stateArray[0])
        isPressed = stateArray[2] == 127
        print(row + " " + column + " " + str(isPressed))
        received(stateArray[1], stateArray[0], isPressed)


# sets color of an individual pad
def setColor(row, column, r, g, b, shifter=0) :
    lp.LedCtrlXY(column, row, min(63, r + shifter), min(63, g + shifter), min(63, b + shifter))

def setAllColor(code):
    lp.LedAllOn(code)

# called on every pad press
def received(r, c, isPressed):

    pygame.time.wait(40)

    # update btn array
    btns[r][c] = isPressed

            

    if isPressed and btns[5][8] and r >= 6:
        if scored[r][c]:
            scored[r][c] = False
        else:
            scored[r][c] = True

    # change shifter color of pad to indicate press/release
    if scored[r][c]:
        setColor(r,c, 63, 0, 0 ,0)
    else:
        if isPressed:
            setColor(r, c, leds[r][c][0], leds[r][c][1], leds[r][c][2], 20)
        else:
            setColor(r, c, leds[r][c][0], leds[r][c][1], leds[r][c][2], 0)

    # check for reset pattern
    if btns[0][0] and btns[0][1] and btns[0][2] and btns[0][3]:
        global isPattern
        global resetSenseTime
        currentTimeMillis = int(round(time.time() * 1000))
        if not isPattern:
            resetSenseTime = currentTimeMillis
            isPattern = True
    else:
        isPattern = False


# def ifLink():
#     currentTimeMillis = int(round(time.time()*1000));
#     lastFlashed = currentTimeMillis
#     if(currentTimeMillis-lastFlashed > 400)
#         setColor(r, c, leds[r][c][0], leds[r][c][1], leds[r][c][2], 20)
#     else
#         setColor(r, c, leds[r][c][0], leds[r][c][1], leds[r][c][2], 0)
#         lastFlashed = currentTimeMillis



def looper():
    global isPattern, resetSenseTime, willReset, lastPingValue, nt, lastPingValueTime, lastPressed, lastFlashed, lastGridButtPress
    currentTimeMillis = int(round(time.time() * 1000))

    # get ping from rio
    pingValue = nt.getBoolean('pingValueRio', False)
    if lastPingValue is not pingValue:
        lastPingValueTime = currentTimeMillis
    if(currentTimeMillis - lastPingValueTime < pingMaxTimeMillis):
        # is connected
        setColor(0, 7, 0, 63, 0)
    else:
        # is not connected
        setColor(0, 7, 63, 0, 0)
    lastPingValue = pingValue
    
    # send launchpad ping
    nt.putBoolean('pingValueLaunchpad', not nt.getBoolean('pingValueLaunchpad', False))


    #Detect ConeMode or CubeMode
    if btns[3][8] and leds[3][8][0] == 30 and currentTimeMillis-lastPressed > 400:
        nt.putBoolean('ConeMode', True)
        nt.putBoolean('CubeMode', False)
        leds[3][8] = [63, 63, 0]
        lastPressed = currentTimeMillis
        for c in range (9):
            if not scored[6][c]:
                leds[6][c] = [63, 63, 0]
                setColor(6, c, leds[6][c][0], leds[6][c][1], leds[6][c][2], 0)
    elif btns[3][8] and currentTimeMillis-lastPressed > 400:
        nt.putBoolean('ConeMode', False)
        nt.putBoolean('CubeMode', True)
        leds[3][8] = [30, 0, 63]
        lastPressed = currentTimeMillis
        for c in range (9):
            if not scored[6][c]:
                leds[6][c] = [30, 0, 63]
                setColor(6, c, leds[6][c][0], leds[6][c][1], leds[6][c][2], 0)
    changing = False
    # send networktables buttons
    for r in range(9):
        for c in range(9):
            status = scored[r][c]
            ntScored.putBoolean(str(r)+":"+str(c), status)
            if not scored[r][c] and not btns[5][8]:
                status = btns[r][c]
                nt.putBoolean(str(r)+':'+str(c), status)
            if not scored[r][c] and not btns[5][8]:
                if r>=6 and btns[r][c]:
                    setColor(lastGridButtPress[0], lastGridButtPress[1], leds[lastGridButtPress[0]][lastGridButtPress[1]][0],leds[lastGridButtPress[0]][lastGridButtPress[1]][1],leds[lastGridButtPress[0]][lastGridButtPress[1]][2], 0)
                    changing = True
                    lastGridButtPress[0] = r
                    lastGridButtPress[1] = c
            if scored[r][c]:
                setColor(r,c,63,0,0, 0)
    if scored[lastGridButtPress[0]][lastGridButtPress[1]]:
        setColor(lastGridButtPress[0], lastGridButtPress[1], 63, 0, 0, 0)
    else:
        if currentTimeMillis-lastFlashed > 600:
            lastFlashed = currentTimeMillis
        elif currentTimeMillis-lastFlashed > 300:
            if not changing:
                r = lastGridButtPress[0]
                c = lastGridButtPress[1]
                setColor(r,c,0,0,0,0)
            else:
                lastFlashed = currentTimeMillis-300
        else:
            r = lastGridButtPress[0]
            c = lastGridButtPress[1]
            setColor(r,c,leds[r][c][0],leds[r][c][1],leds[r][c][2],0)
    

    # reset checker
    # buttons are still held down, ready to reset
    if isPattern and (currentTimeMillis - resetSenseTime) > 1000:
        willReset = True
        for r in range(9):
            for c in range(9):
                scored[r][c] = False
        lastGridButtPress[0] = -1
        setAllColor(26)

    # buttons let go, reset it
    if willReset and not isPattern:
        isPattern = False
        willReset = False
        print("Resetting!")
        main()


main()