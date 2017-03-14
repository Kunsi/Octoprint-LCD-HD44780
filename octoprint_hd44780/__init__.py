# coding=utf-8

import future
from builtins import chr

__author__ = "Felix Kunsmann <felix@kunsmann.eu>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Felix Kunsmann - Released under terms of the AGPLv3 License"

import octoprint.plugin

from hd44780_callback import *

import RPi.GPIO as GPIO

from RPLCD import CharLCD
from RPLCD import CursorMode
from RPLCD import cursor

class LCD_HD44780(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.SettingsPlugin):
    def __init__(self):
        self._pin_to_gpio_rev1 = [-1, -1, -1, 0, -1, 1, -1, 4, 14, -1, 15, 17, 18, 21, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]
        self._pin_to_gpio_rev2 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]
        self._pin_to_gpio_rev3 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, 5, -1, 6, 12, 13, -1, 19, 16, 26, 20, -1, 21 ]
        self._configuredGPIOPins = []

        self.pin_rs = 15
        self.pin_rw = None
        self.pin_e  = 16
        self.pin_d4 = 21
        self.pin_d5 = 22
        self.pin_d6 = 23
        self.pin_d7 = 24

        self.cols = 20
        self.rows = 4

        self._lcd = None

        self._custom_heatbed = (
            0b00000,
            0b11111,
            0b10101,
            0b10101,
            0b10001,
            0b10101,
            0b10101,
            0b11111,
        )

        self._custom_tool0 = (
            0b00000,
            0b11111,
            0b10001,
            0b10111,
            0b10011,
            0b10111,
            0b10001,
            0b11111,
        )

    def on_settings_initialized(self):
        self._initialize_lcd()
        self._printer.register_callback(LCD_HD44780_PrinterCallback)

    def _gpio_board_to_bcm(self, pin):
        if GPIO.RPI_REVISION == 1:
            pin_to_gpio = self._pin_to_gpio_rev1
        elif GPIO.RPI_REVISION == 2:
            pin_to_gpio = self._pin_to_gpio_rev2
        else:
            pin_to_gpio = self._pin_to_gpio_rev3

        return pin_to_gpio[pin]

    def _gpio_get_pin(self, pin):
        if GPIO.getmode() == GPIO.BOARD:
            return pin
        elif GPIO.getmode() == GPIO.BCM:
            return self._gpio_board_to_bcm(pin)
        else:
            return 0

    def _initialize_lcd(self):
        self._logger.info("Running RPi.GPIO version %s" % GPIO.VERSION)
        if GPIO.VERSION < "0.6":
            self._logger.error("RPi.GPIO version 0.6.0 or greater required.")

        GPIO.setwarnings(False)

        for pin in self._configuredGPIOPins:
            self._logger.debug("Cleaning up pin %s" % pin)
            try:
                GPIO.cleanup(self._gpio_get_pin(pin))
            except (RuntimeError, ValueError) as e:
                self._logger.error(e)
        self._configuredGPIOPins = []

        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BOARD)

        pin_rs = self._gpio_get_pin(self.pin_rs)

        if self.pin_rw is not None:
            pin_rw = self._gpio_get_pin(self.pin_rw)
        else:
            pin_rw = None

        pin_e  = self._gpio_get_pin(self.pin_e)
        pin_d4 = self._gpio_get_pin(self.pin_d4)
        pin_d5 = self._gpio_get_pin(self.pin_d5)
        pin_d6 = self._gpio_get_pin(self.pin_d6)
        pin_d7 = self._gpio_get_pin(self.pin_d7)

        self._lcd = CharLCD(pin_rs=pin_rs, pin_rw=pin_rw, pin_e=pin_e, pins_data=[pin_d4, pin_d5, pin_d6, pin_d7],
                            numbering_mode=GPIO.getmode(), cols=self.cols, rows=self.rows)

        self._lcd.create_char(0, self._custom_heatbed)
        self._lcd.create_char(1, self._custom_tool0)

        self._lcd.cursor_mode = CursorMode.hide
        self._lcd.clear()
        self._lcd.write_string('Octoprint')

__plugin_name__ = "LCD: HD44780-compatible"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LCD_HD44780()

    global __plugin_hooks__
    __plugin_hooks__ = {
#        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
