# -*- coding: utf-8 -*-    
from unittest import skip
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
configThreshold = 0.8
pause = 0.2

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

def clickBtn(img, timeout=3, threshold = configThreshold):
    """ Parameters:
        img: The image that will be used as an template to find where to click.
        timeout (int): Time in seconds that it will keep looking for the img before returning with fail
        threshold(float): How confident the bot needs to be to click the buttons (values from 0 to 1)
    """

    logger(None, progress_indicator=True)
    start = time.time()
    has_timed_out = False
    clicked = False

    while(not has_timed_out):
        matches = positions(img, threshold=threshold)
        count = 0
        
        for match in matches:
            if(len(matches)==0):
                has_timed_out = time.time()-start > timeout
                continue
            
            x = match[[0]] 
            y = match[[1]]
            w = match[[2]]
            h = match[[3]]
        
            pos_click_x = x+w/2
            pos_click_y = y+h/2
            moveToPosition(pos_click_x,pos_click_y)
            pyautogui.click()
            clicked = True
            count += 1
            if (count >= len(matches)):
                return clicked
            
    return clicked

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        # The screen part to capture
        # monitor = {"top": 160, "left": 160, "width": 1000, "height": 135}

        # Grab the data
        return sct_img[:,:,:3]

def positions(target, threshold = configThreshold, img = None):
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

def goToHeroes():
    if clickBtn(images['go-back-arrow']):
        global login_attempts
        login_attempts = 0

    # TODO: Verificar tempo para proxima ação
    time.sleep(0.5)
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
        login_attempts = login_attempts + 1
        if clickBtn(images['treasure-hunt-icon'], timeout = 15):
            login_attempts = 0
        return

    if clickBtn(images['select-wallet-2'], timeout = 20):
        login_attempts = login_attempts + 1
        if clickBtn(images['treasure-hunt-icon'], timeout=25):
            login_attempts = 0

    if clickBtn(images['ok'], timeout=5):
         if clickBtn(images['treasure-hunt-icon'], timeout=25):
            login_attempts = 0
            pass

def sendHeroesToWork():
    logger('Search for heroes to work')

    goToHeroes()

    logger('Sending all heroes to work', 'all')

    failed_send_to_work = 0
    # Tenta 3 vezes clicar no botão ALL
    while (failed_send_to_work < 2):
        if clickBtn(images['send-all-icon']):
            break
        else:
            failed_send_to_work += 1

    goToGame()

def forceRefresh():
    pyautogui.hotkey('ctrl','f5')
    return

def main(): 
    """Main execution setup and loop"""
    # Setup

    global login_attempts
    global last_log_is_progress
    login_attempts = 0
    last_log_is_progress = False

    # Limpa o console para mensagem de inicio
    clearConsole()

    # Carrega as imagens alvo
    global images
    images = load_images()

    # Carrega os intervalos de tempo do arquivo 
    # TODO: Verificar se mantem carregamento por arquivo ou definir diretamente no código
    time_interval = {
        'check_for_login': 3,
        'send_heroes_for_work': 10,
        'check_for_new_map_button': 5,
        'refresh_heroes_positions': 3,
        'force_update': 10,
    }
    
    #config['time_intervals']

    last = {
    "login" : 0,
    "heroes" : 0,
    "new_map" : 0,
    "refresh_heroes" : 0,
    "force_update": 0
    }

    # ============
    while True:
        # Fazer com que os click sejam simultaneos em várias contas
        # Após cada ação verificar se alguma conta foi desconectada afim de manter a sincronia entre as contas
        # A cada X tempo realizar o ctrl + F5 em todas as contas, evitando problemas nas contas
        # Melhorar processo de reconhecimento das imagens

        
        clearConsole()
        time.sleep(1)
        sendHeroesToWork()

        while True:
            #Verificador de tempo entre as ações do game
            now = time.time()

            if now - last["login"] > time_interval['check_for_login'] * 60:
                sys.stdout.flush()
                last["login"] = now
                login()

            if now - last["heroes"] > time_interval['send_heroes_for_work'] * 60:
                last["heroes"] = now
                sendHeroesToWork()

            if now - last["new_map"] > time_interval['check_for_new_map_button']:
                last["new_map"] = now

            if clickBtn(images['new-map']):
                loggerMapClicked()

            if now - last["refresh_heroes"] > time_interval['refresh_heroes_positions'] * 60:
                last["refresh_heroes"] = now
                refreshHeroesPositions()

            if now - last["force_update"] > time_interval['force_update'] * 60:
                last["force_update"] = now
                forceRefresh()

            logger(None, progress_indicator=True)

            sys.stdout.flush()
            time.sleep(1)
        
if __name__ == '__main__':
    main()
