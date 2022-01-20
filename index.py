# -*- coding: utf-8 -*-    
from src.logger import logger, loggerMapClicked
from cv2 import cv2
from os import listdir
import subprocess as sp
import numpy as np
import mss
import pyautogui
import time
import sys
import yaml

# Load config file.
stream = open("config.yaml", 'r')
config = yaml.safe_load(stream)
configThreshold = config['threshold']
pause = config['time_intervals']['interval_between_moviments']
pyautogui.PAUSE = pause

import os
def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
        command = 'cls'
    os.system(command)

def moveToPosition(x,y):
    pyautogui.moveTo(x,y,0.3) 
    # 0.3 é o tempo em que o mouse irá levar para se movimentar até a posição
    # Deixar mais rápido aumenta a chance de problemas na navegação

def remove_suffix(input_string, suffix):
    """Returns the input_string without the suffix"""

    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def load_images(dir_path='./targets/'):
    """ Programatically loads all images of dir_path as a key:value where the
        key is the file name without the .png suffix

    Returns:
        dict: dictionary containing the loaded images as key:value pairs.
    """

    file_names = listdir(dir_path)
    targets = {}
    for file in file_names:
        path = 'targets/' + file
        targets[remove_suffix(file, '.png')] = cv2.imread(path)

    return targets

def clickBtn(img, timeout=3, threshold = configThreshold['default']):
    """Search for img in the screen, if found moves the cursor over it and clicks.
    Parameters:
        img: The image that will be used as an template to find where to click.
        timeout (int): Time in seconds that it will keep looking for the img before returning with fail
        threshold(float): How confident the bot needs to be to click the buttons (values from 0 to 1)
    """

    logger(None, progress_indicator=True)
    start = time.time()
    has_timed_out = False
    while(not has_timed_out):
        matches = positions(img, threshold=threshold)

        if(len(matches)==0):
            has_timed_out = time.time()-start > timeout
            continue

        x,y,w,h = matches[0]
        pos_click_x = x+w/2
        pos_click_y = y+h/2
        moveToPosition(pos_click_x,pos_click_y)
        pyautogui.click()
        return True

    return False

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        # The screen part to capture
        # monitor = {"top": 160, "left": 160, "width": 1000, "height": 135}

        # Grab the data
        return sct_img[:,:,:3]

def positions(target, threshold=configThreshold['default'],img = None):
    if img is None:
        img = printSreen()
    result = cv2.matchTemplate(img,target,cv2.TM_CCOEFF_NORMED)
    w = target.shape[1]
    h = target.shape[0]

    yloc, xloc = np.where(result >= threshold)


    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def scroll():
    commoms = positions(images['commom-text'], threshold = configThreshold['commom'])
    if (len(commoms) == 0):
        return
    x,y,w,h = commoms[len(commoms)-1]
#
    moveToPosition(x,y)

    if not config['use_click_and_drag_instead_of_scroll']:
        pyautogui.scroll(-config['scroll_size'])
    else:
        pyautogui.dragRel(0,-config['click_and_drag_amount'],duration=1, button='left')


def clickButtons():
    buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])
    # print('buttons: {}'.format(len(buttons)))
    for (x, y, w, h) in buttons:
        moveToPosition(x+(w/2),y+(h/2))
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        #cv2.rectangle(sct_img, (x, y) , (x + w, y + h), (0,255,255),2)
        if hero_clicks > 20:
            logger('too many hero clicks, try to increase the go_to_work_btn threshold')
            return
    return len(buttons)

def isWorking(bar, buttons):
    y = bar[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def clickGreenBarButtons():
    # ele clicka nos q tao trabaiano mas axo q n importa
    offset = 140

    green_bars = positions(images['green-bar'], threshold=configThreshold['green_bar'])
    logger('%d green bars detected' % len(green_bars))
    buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])
    logger('%d buttons detected' % len(buttons))


    not_working_green_bars = []
    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
    if len(not_working_green_bars) > 0:
        logger('%d buttons with green bar detected' % len(not_working_green_bars))
        logger('Clicking in %d heroes' % len(not_working_green_bars))

    # se tiver botao com y maior que bar y-10 e menor que y+10
    hero_clicks_cnt = 0
    for (x, y, w, h) in not_working_green_bars:
        # isWorking(y, buttons)
        moveToPosition(x+offset+(w/2),y+(h/2))
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        hero_clicks_cnt = hero_clicks_cnt + 1
        if hero_clicks_cnt > 20:
            logger('Too many hero clicks, try to increase the go_to_work_btn threshold')
            return
        #cv2.rectangle(sct_img, (x, y) , (x + w, y + h), (0,255,255),2)
    return len(not_working_green_bars)

def clickFullBarButtons():
    offset = 100
    full_bars = positions(images['full-stamina'], threshold=configThreshold['default'])
    buttons = positions(images['go-work'], threshold=configThreshold['go_to_work_btn'])

    not_working_full_bars = []
    for bar in full_bars:
        if not isWorking(bar, buttons):
            not_working_full_bars.append(bar)

    if len(not_working_full_bars) > 0:
        logger('Clicking in %d heroes' % len(not_working_full_bars))

    for (x, y, w, h) in not_working_full_bars:
        moveToPosition(x+offset+(w/2),y+(h/2))
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1

    return len(not_working_full_bars)

def goToHeroes():
    if clickBtn(images['go-back-arrow']):
        global login_attempts
        login_attempts = 0

    time.sleep(1)
    clickBtn(images['hero-icon'])

def goToGame():
    # in case of server overload popup
    clickBtn(images['x'])
    # time.sleep(3)
    clickBtn(images['x'])

    clickBtn(images['treasure-hunt-icon'])

def refreshHeroesPositions():

    logger('Refreshing Heroes Positions')
    clickBtn(images['go-back-arrow'])
    clickBtn(images['treasure-hunt-icon'])

    time.sleep(3)
    clickBtn(images['treasure-hunt-icon'])

def login():
    global login_attempts
    logger('Checking if game has disconnected')

    # Auto ctrl F5
    if login_attempts > 3:
        logger('Too many login attempts, refreshing')
        login_attempts = 0
        pyautogui.hotkey('ctrl','f5')
        return

    if clickBtn(images['connect-wallet'], timeout = 10):
        logger('Connect wallet button detected, logging in!')
        login_attempts = login_attempts + 1
        time.sleep(5)

    if clickBtn(images['select-wallet-2'], timeout=8):
        # sometimes the sign popup appears imediately
        login_attempts = login_attempts + 1
        # print('sign button clicked')
        # print('{} login attempt'.format(login_attempts))
        if clickBtn(images['treasure-hunt-icon'], timeout = 15):
            # print('sucessfully login, treasure hunt btn clicked')
            login_attempts = 0
        return
        # click ok button

    if clickBtn(images['select-wallet-2'], timeout = 20):
        login_attempts = login_attempts + 1
        # print('sign button clicked')
        # print('{} login attempt'.format(login_attempts))
        # time.sleep(25)
        if clickBtn(images['treasure-hunt-icon'], timeout=25):
            # print('sucessfully login, treasure hunt btn clicked')
            login_attempts = 0
        # time.sleep(15)

    if clickBtn(images['ok'], timeout=5):
        pass
        # time.sleep(15)
        # print('ok button clicked')

def refreshHeroes():
    logger('Search for heroes to work')

    goToHeroes() 

    if config['select_heroes_mode'] == "full":
        logger('Sending heroes with full stamina bar to work', 'green')
    elif config['select_heroes_mode'] == "green":
        logger('Sending heroes with green stamina bar to work', 'green')
    else:
        logger('Sending all heroes to work', 'green')

    buttonsClicked = 1
    empty_scrolls_attempts = config['scroll_attemps']

    while(empty_scrolls_attempts > 0 ):
        if config['select_heroes_mode'] == 'full':
            buttonsClicked = clickFullBarButtons()
        elif config['select_heroes_mode'] == 'green':
            buttonsClicked = clickGreenBarButtons()
        else:
            buttonsClicked = clickButtons()

        if buttonsClicked == 0:
            empty_scrolls_attempts = empty_scrolls_attempts - 1
        scroll()
        time.sleep(2)
    logger('{} heroes sent to work'.format(hero_clicks))
    goToGame()

def main():
    """Main execution setup and loop"""
    # ==Setup==
    global hero_clicks
    global login_attempts
    global last_log_is_progress
    hero_clicks = 0
    login_attempts = 0
    last_log_is_progress = False

    # Limpa o console para mensagem de inicio
    clearConsole()

    global images
    images = load_images()

    t = config['time_intervals']
    last = {
    "login" : 0,
    "heroes" : 0,
    "new_map" : 0,
    "refresh_heroes" : 0
    }

    # ============
    while True:
        clearConsole()
        time.sleep(1)

        while True:
            now = time.time()

            if now - last["login"] > t['check_for_login'] * 60:
                sys.stdout.flush()
                last["login"] = now
                login()

            if now - last["heroes"] > t['send_heroes_for_work'] * 60:
                last["heroes"] = now
                refreshHeroes()

            if now - last["new_map"] > t['check_for_new_map_button']:
                last["new_map"] = now

            if clickBtn(images['new-map']):
                loggerMapClicked()

            if now - last["refresh_heroes"] > t['refresh_heroes_positions'] * 60:
                last["refresh_heroes"] = now
                refreshHeroesPositions()

            logger(None, progress_indicator=True)

            sys.stdout.flush()
            time.sleep(1)
        
if __name__ == '__main__':
    main()
