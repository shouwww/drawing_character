import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import binascii
import base64
import copy
import cv2
import numpy as np
import time

fileName = "data/KST32Bv3/KST32B.TXT"

class StrokeFonts():

    font_data_dict = dict()

    def __init__(self):
        font_file = open(fileName, 'r', encoding='shift_jis')
        for line in font_file:
            if line.startswith('*'):
                continue
            # End if
            data = line.split(' ')
            if len(data) < 2:
                continue
            # End if
            font_datas = ''
            for c in data[1]:
                font_datas = font_datas + hex(int.from_bytes(c.encode("shift_jis"),'little'))
            # End for
            self.font_data_dict[data[0]] = font_datas
        # End for
    # End def

    def get_font_data(self, charactor: str):
        '''
        文字からストロークフォントの座標データを取得する。
    
        Parameters
        ----------
        charactor : str
            ストロークフォントの座標を取得したい文字

        Returns
        -------
        font_data : str
        ストロークフォントのママのデータ
        '''
        if charactor.isascii():
            hex_char = format(ord(charactor), '04x')
            serch_char_code = hex_char
        else:
            hex_char = charactor.encode('iso-2022-jp').hex()
            serch_char_code = hex_char[6:-6]
        serch_char_code = serch_char_code.upper()
        ret_data = self.font_data_dict[serch_char_code]
        return ret_data
    # End def

    def change_point_data(self, point_datas: str):
        '''
        ストロークフォントの座標データをリストに変換する。
    
        Parameters
        ----------
        point_datas : str
            ストロークフォントのママのデータ

        Returns
        -------
        line_datas : list
        フォントの座標データを描画する直線の座標のリスト
        [[[l1x1,l1y1],[l1x2,l1y2],[l1x3,l1y3],[l1x4,l1y4]],
         [[l2x1,l2y1],[l2x2,l2y2],[l2x3,l2y3]]
        ]
        '''
        lines_data = []
        line_data = []
        set_point = [0,0]
        state = ''
        point = 0
        hex_datas = point_datas.split('0x')
        for data in hex_datas[1:]:
            state, point = self._get_point(data)
            if state == 'Move_x':
                if len(line_data) != 0:
                    lines_data.append(copy.deepcopy(line_data))
                    line_data = []
                set_point[0] = point
            elif state == 'Move_y':
                if len(line_data) != 0:
                    lines_data.append(copy.deepcopy(line_data))
                    line_data = []
                set_point[1] = point
            elif state == 'Next_x':
                if len(line_data) == 0:
                    line_data.append(copy.deepcopy(set_point))
                set_point[0] = point
            elif state == 'Draw_x':
                if len(line_data) == 0:
                    line_data.append(copy.deepcopy(set_point))
                set_point[0] = point
                line_data.append(copy.deepcopy(set_point))
            elif state == 'Draw_y':
                if len(line_data) == 0:
                    line_data.append(copy.deepcopy(set_point))
                set_point[1] = point
                line_data.append(copy.deepcopy(set_point))
        # End for
        lines_data.append(copy.deepcopy(line_data))
        return lines_data
    # End def

    def get_lines_data(self, charactor: str):
        '''
        文字からストロークフォントの直線データを取得する。
    
        Parameters
        ----------
        charactor : str
            ストロークフォントの座標を取得したい文字

        Returns
        -------
        line_datas : list
        フォントの座標データを描画する直線の座標のリスト
        [[[l1x1,l1y1],[l1x2,l1y2],[l1x3,l1y3],[l1x4,l1y4]],
         [[l2x1,l2y1],[l2x2,l2y2],[l2x3,l2y3]]
        ]
        '''
        row_data = self.get_font_data(charactor)
        lines_datas = self.change_point_data(row_data)
        return lines_datas

    def _get_point(self, data):
        state = ''
        point = 0
        dec_data = int(data, 16)
        if (int('0X21', 16) <= dec_data) and (dec_data <= int('0x26', 16)):
            state = 'Move_x'
            point = dec_data - int('0x21', 16)
        elif (int('0X28', 16) <= dec_data) and (dec_data <= int('0x3f', 16)):
            state = 'Move_x'
            point = dec_data - int('0x22', 16)
        elif (int('0X40', 16) <= dec_data) and (dec_data <= int('0x5B', 16)):
            state = 'Draw_x'
            point = dec_data - int('0x40', 16)
        elif (int('0X5E', 16) <= dec_data) and (dec_data <= int('0x5F', 16)):
            state = 'Draw_x'
            point = dec_data - int('0x42', 16)
        elif (int('0X60', 16) <= dec_data) and (dec_data <= int('0x7D', 16)):
            state = 'Next_x'
            point = dec_data - int('0x60', 16)
        elif int('0X7E', 16) == dec_data:
            state = 'Move_y'
            point = 0
        elif (int('0XA1', 16) <= dec_data) and (dec_data <= int('0xBF', 16)):
            state = 'Move_y'
            point = dec_data - int('0xA0', 16)
        elif (int('0XC0', 16) <= dec_data) and (dec_data <= int('0xDF', 16)):
            state = 'Draw_y'
            point = dec_data - int('0xC0', 16)
        # End if
        return state, point
    # End def

    def preview_font_line(self, charactor: str, interval: int = 1):
        '''
        文字からストロークフォントの直線データをウィンドウに描画する。
    
        Parameters
        ----------
        charactor : str
            ストロークフォントの座標を取得したい文字
        interval : int
            一画ごとに描画する間隔の設定[sec]

        Returns
        -------
        None
        '''
        rate = 10
        lines_data = self.get_lines_data(charactor)
        img = np.ones((32 * rate, 32 * rate), np.uint8) * 255
        for line_data in lines_data:
            for i, point in enumerate(line_data):
                if i == 0:
                    start_point = point
                else:
                    # 32 - y : reverse 
                    cv2.line(img,(start_point[0] * rate, (32 - start_point[1]) * rate),(point[0] * rate, (32 - point[1]) * rate),(125,125,125),1)
                    cv2.imshow('draw_line',img)
                    cv2.waitKey(1)
                    time.sleep(interval)
                    start_point = point
                # End if
            # End for
        # End for
        time.sleep(5)
        cv2.destroyAllWindows()
    # End def

    def all_font_save_img(self):
        '''
        フォントデータすべてを画像として保存する
        '''
        file_path = '../data/img/'
        serch_codes = []
        rate = 10
        for code in range(int('00',16),int('FF',16)):
            # ascii
            hex_code = format(code, '04x')
            serch_code = hex_code.upper()
            serch_codes.append(serch_code)
        for code in range(int('1A20',16),int('1A7F',16)):
            hex_code = format(code, '04x')
            serch_code = hex_code.upper()
            serch_codes.append(serch_code)
        for code in range(int('2120',16),int('2FFF',16)):
            hex_code = format(code, '04x')
            serch_code = hex_code.upper()
            serch_codes.append(serch_code)
        for j,serch_code in enumerate(serch_codes):
            row_data = self.font_data_dict.get(serch_code, 'NO KEY')
            if row_data == 'NO KEY':
                continue
            # End if
            lines_data = self.change_point_data(row_data)
            img = np.ones((32 * rate, 32 * rate), np.uint8) * 255
            for line_data in lines_data:
                for i, point in enumerate(line_data):
                    if i == 0:
                        start_point = point
                    else:
                        # 32 - y : reverse 
                        cv2.line(img,(start_point[0] * rate, (32 - start_point[1]) * rate),(point[0] * rate, (32 - point[1]) * rate),(125,125,125),1)
                        cv2.imshow('draw_line',img)
                        cv2.waitKey(1)
                        time.sleep(0.2)
                        start_point = point
                    # End if
                # End for
            # End for
            cv2.imwrite(file_path + serch_code + '.png',img)
            cv2.destroyAllWindows()
        # End for
    # End def
# End class