# coding=utf-8

from __future__ import absolute_import

__author__ = "Franziska Kunsmann <hi@kunsmann.eu>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Felix Kunsmann - Released under terms of the AGPLv3 License"

import octoprint.plugin

import RPi.GPIO as GPIO
import time

class LCD_HD44780(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.SettingsPlugin,
                    octoprint.printer.PrinterCallback):
    def __init__(self):
        self._pin_to_gpio_rev1 = [-1, -1, -1, 0, -1, 1, -1, 4, 14, -1, 15, 17, 18, 21, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]
        self._pin_to_gpio_rev2 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1 ]
        self._pin_to_gpio_rev3 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10, -1, 9, 25, 11, 8, -1, 7, -1, -1, 5, -1, 6, 12, 13, -1, 19, 16, 26, 20, -1, 21 ]
        self._configuredGPIOPins = []

        self.pin_rs = 15
        self.pin_e  = 16
        self.pin_d4 = 21
        self.pin_d5 = 22
        self.pin_d6 = 23
        self.pin_d7 = 24

        self.cols = 20
        self.rows = 4

        self._ClosedOrError = False

        self._line1 = ''
        self._line2 = ''
        self._line3 = ''
        self._line4 = ''

        self._lcd_line1 = 0x80
        self._lcd_line2 = 0xC0
        self._lcd_chr   = GPIO.HIGH
        self._lcd_cmd   = GPIO.LOW
        self._lcd_pulse = 0.0005
        self._lcd_delay = 0.0005

        self._lcd_updating = False

        timer = RepeatedTimer(30, self._lcd_update())
        timer.start()

    def on_settings_initialized(self):
        self._initialize_lcd()
        self._printer.register_callback(self)

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

        GPIO.setup(self._gpio_get_pin(self.pin_rs), GPIO.OUT)
        GPIO.setup(self._gpio_get_pin(self.pin_e), GPIO.OUT)
        GPIO.setup(self._gpio_get_pin(self.pin_d4), GPIO.OUT)
        GPIO.setup(self._gpio_get_pin(self.pin_d5), GPIO.OUT)
        GPIO.setup(self._gpio_get_pin(self.pin_d6), GPIO.OUT)
        GPIO.setup(self._gpio_get_pin(self.pin_d7), GPIO.OUT)

        self._configuredGPIOPins = [self._gpio_get_pin(self.pin_rs), self._gpio_get_pin(self.pin_e), self._gpio_get_pin(self.pin_d4), self._gpio_get_pin(self.pin_d5), self._gpio_get_pin(self.pin_d6), self._gpio_get_pin(self.pin_d7)]

        self._lcd_send_byte(0x33, self._lcd_cmd)
        self._lcd_send_byte(0x32, self._lcd_cmd)
        self._lcd_send_byte(0x28, self._lcd_cmd)
        self._lcd_send_byte(0x0C, self._lcd_cmd)
        self._lcd_send_byte(0x06, self._lcd_cmd)
        self._lcd_send_byte(0x01, self._lcd_cmd)

        printerstate = self._printer.get_state_string()
        self._line1 = printerstate.center(20)
        self.clear_lower_half()

        self._lcd_update()

    def _lcd_update(self):
        if self._lcd_updating:
            return

        self._lcd_updating = True

        line1 = self._line1.ljust(self.cols, ' ')
        line2 = self._line2.ljust(self.cols, ' ')
        line3 = self._line3.ljust(self.cols, ' ')
        line4 = self._line4.ljust(self.cols, ' ')

        message = line1 + line3
        self._lcd_send_byte(self._lcd_line1, self._lcd_cmd)
        for i in range(self.cols*self.rows/2):
            self._lcd_send_byte(ord(message[i]), self._lcd_chr)

        message = line2 + line4
        self._lcd_send_byte(self._lcd_line2, self._lcd_cmd)
        for i in range(self.cols*self.rows/2):
            self._lcd_send_byte(ord(message[i]), self._lcd_chr)

        self._lcd_updating = False

    def _lcd_send_byte(self, bits, mode):
        GPIO.output(self.pin_rs, mode)
        GPIO.output(self.pin_d4, GPIO.LOW)
        GPIO.output(self.pin_d5, GPIO.LOW)
        GPIO.output(self.pin_d6, GPIO.LOW)
        GPIO.output(self.pin_d7, GPIO.LOW)
        if bits & 0x10 == 0x10:
            GPIO.output(self.pin_d4, GPIO.HIGH)
        if bits & 0x20 == 0x20:
            GPIO.output(self.pin_d5, GPIO.HIGH)
        if bits & 0x40 == 0x40:
            GPIO.output(self.pin_d6, GPIO.HIGH)
        if bits & 0x80 == 0x80:
            GPIO.output(self.pin_d7, GPIO.HIGH)
        time.sleep(self._lcd_delay)    
        GPIO.output(self.pin_e, GPIO.HIGH)  
        time.sleep(self._lcd_pulse)
        GPIO.output(self.pin_e, GPIO.LOW)  
        time.sleep(self._lcd_delay)      
        GPIO.output(self.pin_d4, GPIO.LOW)
        GPIO.output(self.pin_d5, GPIO.LOW)
        GPIO.output(self.pin_d6, GPIO.LOW)
        GPIO.output(self.pin_d7, GPIO.LOW)
        if bits&0x01==0x01:
            GPIO.output(self.pin_d4, GPIO.HIGH)
        if bits&0x02==0x02:
            GPIO.output(self.pin_d5, GPIO.HIGH)
        if bits&0x04==0x04:
            GPIO.output(self.pin_d6, GPIO.HIGH)
        if bits&0x08==0x08:
            GPIO.output(self.pin_d7, GPIO.HIGH)
        time.sleep(self._lcd_delay)    
        GPIO.output(self.pin_e, GPIO.HIGH)  
        time.sleep(self._lcd_pulse)
        GPIO.output(self.pin_e, GPIO.LOW)  
        time.sleep(self._lcd_delay) 

    def on_printer_add_temperature(self, data):
        if not self._ClosedOrError:
            self._line4 = 'E{:3.0f}/{:3.0f}  B{:3.0f}/{:3.0f}'.format(data['tool0']['actual'], data['tool0']['target'], data['bed']['actual'], data['bed']['target'])
            self._lcd_update()
        else:
            self.clear_lower_half()

    def on_printer_send_current_data(self, data):
        self._line1 = data['state']['text'][:20].center(20)

        self._ClosedOrError = data['state']['flags']['closedOrError']

        if not self._ClosedOrError:
            if data['job']['file']['name'] is not None:
                self._line2 = data['job']['file']['name'][:20]
            else:
                self._line2 = ''

            if data['progress']['completion'] is not None:
                self._line3 = '{:6.2f}'.format(data['progress']['completion']) + '%'

                if data['progress']['printTimeLeft'] is not None:
                    self._line3 += ' ~' + '{:1.0f}:{:02.0f}'.format(data['progress']['printTimeLeft']/60, data['progress']['printTimeLeft']%60) + 'min '
            else:
                self._line3 = ''
        else:
            self.clear_lower_half()

        self._lcd_update()

    def clear_lower_half(self):
        self._line2 = ''
        self._line3 = ''

        line4 = 'OctoPrint ' + octoprint.__version__

        self._line4 = line4.center(20)


__plugin_name__ = "LCD: HD44780-compatible"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = LCD_HD44780()

    global __plugin_hooks__
    __plugin_hooks__ = {
#        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
