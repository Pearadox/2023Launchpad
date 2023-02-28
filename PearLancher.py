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
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]],
    [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[63,0,0]],
    [[63,25,25],[63,25,25],[63,25,25],[63,25,25],[63,25,25],[63,25,25],[63,25,25],[63,25,25],[63,25,25]],
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
lp = launchpad.LaunchpadMk2()

# initialize networktables
NetworkTables.initialize(server='roborio-'+teamNumber+'-frc.local')
nt = NetworkTables.getTable(tableName)
ntScored = NetworkTables.getTable("Scored")

# Rio connection monitor
lastPingValue = False
lastPingValueTime = 0
pingMaxTimeMillis = 500

def main():
    global btns
    # open the first Launchpad Mk2
    if lp.Open(0, "mk2"):
        print(" - Launchpad Mk2: OK")
    else:
        print(" - Launchpad Mk2: ERROR (most likely not connected)")
        return

    # Clear the buffer because the Launchpad remembers everything
    lp.ButtonFlush()
    lp.Reset()

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
        if(len(stateArray) == 0):
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


def looper():
    global isPattern, resetSenseTime, willReset, lastPingValue, nt, lastPingValueTime
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


    # send networktables buttons
    for r in range(9):
        for c in range(9):
            status = btns[r][c]
            nt.putBoolean(str(r)+':'+str(c), status)
            status = scored[r][c]
            ntScored.putBoolean(str(r)+":"+str(c), status)

    # reset checker
    # buttons are still held down, ready to reset
    if isPattern and (currentTimeMillis - resetSenseTime) > 1000:
        willReset = True
        for r in range(9):
            for c in range(9):
                scored[r][c] = False
        setAllColor(26)

    # buttons let go, reset it
    if willReset and not isPattern:
        isPattern = False
        willReset = False
        print("Resetting!")
        main()


main()