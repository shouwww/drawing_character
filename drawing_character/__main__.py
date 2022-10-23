import cv2
import numpy as np
import PySimpleGUI as sg
import time
from screeninfo import get_monitors
from . import strokefonts


def main():
    layout = [
        [sg.Text('Stroke Fonts', key='-Title-')],
        [sg.Text('入力欄'), sg.InputText(key='-IN-'), sg.Button('Start', size=(10, 1), font='Helvetica 14', key='-Start-')],
        [sg.Output(size=(50,10), key='-debug-'), sg.Image(filename='', key='-Image-')],
        [sg.Button('Clear',key='-Clear-'), sg.Button('Exit',key='-Exit-')]
    ]
    stroke = strokefonts.StrokeFonts()
    window = sg.Window('テキスト表示アプリ', layout, finalize=True)

    img_update = False

    while True:
        #　ユーザからの入力を待ちます。入力があると、次の処理に進みます。
        event, values = window.read(timeout=200)
        #　ウィンドウの右上の×を押したときの処理、「Exit」ボタンを押したときの処理
        if event in (sg.WIN_CLOSED, '-Exit-'):
            break
        #　「Clear」ボタンを押したときの処理
        elif event == '-Clear-':
            #　「-debug-」領域を、空白で更新します。
            window['-debug-'].update('')
        elif event == '-Start-':
            print(values['-IN-'])
        if img_update:
            pass
        
    # ウィンドウ終了処理
    window.close()
# End def

if __name__ == '__main__':
    main()
