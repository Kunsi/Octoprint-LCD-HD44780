# coding=utf-8

import future
from builtins import chr

import octoprint.plugin

class LCD_HD44780_PrinterCallback(octoprint.printer.PrinterCallback):
    def on_printer_add_log(data):
        pass

    def on_printer_add_message(data):
        pass

    def on_printer_add_temperature(data):
        LCD_HD44780._lcd.cursor_pos = (3,0)
        LCD_HD44780._lcd.write_string(chr(1) + '{:5.1f}/{:3f}'.format(data['tool0']['actual'], data['tool0']['target']) + '  ' + chr(0) + '{:5.1f}/{:3f}'.format(data['tool0']['actual'], data['tool0']['target']))

    def on_printer_received_registered_message(name, output):
        pass

    def on_printer_send_current_data(data):
        self._lcd.cursor_pos = (0,0)
        self._lcd.write_string(data['state']['text'].center(20))

    def on_printer_send_initial_data(data):
        self._lcd.clear()
