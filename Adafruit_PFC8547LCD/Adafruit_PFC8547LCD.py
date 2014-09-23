from time import sleep
from Adafruit_I2C import Adafruit_I2C

# Code based on https://gist.github.com/ufux/6094977
# Massaged to use Adafruit_I2C library and commands.
# Communication from expander to display: high nibble first, then low nibble
# Communication via i2c to the PCF 8547: bits are processed from highest to lowest (send P7 bit first)

class Adafruit_PCF8547LCD:
    #initializes objects and lcd

    # LCD Commands
    LCD_CLEARDISPLAY        = 0x01
    LCD_RETURNHOME          = 0x02
    LCD_ENTRYMODESET        = 0x04
    LCD_DISPLAYCONTROL      = 0x08
    LCD_CURSORSHIFT         = 0x10
    LCD_FUNCTIONSET         = 0x20
    LCD_SETCGRAMADDR        = 0x40
    LCD_SETDDRAMADDR        = 0x80

    # Flags for display on/off control
    LCD_DISPLAYON           = 0x04
    LCD_DISPLAYOFF          = 0x00
    LCD_CURSORON            = 0x02
    LCD_CURSOROFF           = 0x00
    LCD_BLINKON             = 0x01
    LCD_BLINKOFF            = 0x00

    # Flags for display entry mode
    LCD_ENTRYRIGHT          = 0x00
    LCD_ENTRYLEFT           = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00

    # Flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE  = 0x00
    LCD_MOVERIGHT   = 0x04
    LCD_MOVELEFT    = 0x00

    # flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    # flags for backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00

    EN = 0b00000100  # Enable bit
    RW = 0b00000010  # Read/Write bit
    RS = 0b00000001  # Register select bit

    '''
    new pinout:
    -----------    -----------
    0x80    P7 -  - D7
    0x40    P6 -  - D6
    0x20    P5 -  - D5
    0x10    P4 -  - D4
    -----------    -----------
    0x08    P3 -  - BL   Backlight ???
    0x04    P2 -  - EN   Starts Data read/write
    0x02    P1 -  - RW   low: write, high: read
    0x01    P0 -  - RS   Register Select: 0: Instruction Register (IR) (AC when read), 1: data register (DR)
    '''

    def __init__(self, addr=0x3f, busnum=-1, withBacklight=True, withOneTimeInit=False):
        '''
        device writes!
        crosscheck also http://www.monkeyboard.org/tutorials/81-display/70-usb-serial-to-hd44780-lcd
        here a sequence is listed
        '''
        self.addr = addr
        self.busnum = busnum

        self.bus = Adafruit_I2C(self.addr, self.busnum)

        self.displayshift   = (self.LCD_CURSORMOVE |
                               self.LCD_MOVERIGHT)
        self.displaymode    = (self.LCD_ENTRYLEFT |
                               self.LCD_ENTRYSHIFTDECREMENT)
        self.displaycontrol = (self.LCD_DISPLAYON |
                               self.LCD_CURSOROFF |
                               self.LCD_BLINKOFF)

        self.displayfunction = self.LCD_4BITMODE | self.LCD_1LINE | self.LCD_5x8DOTS
        self.displayfunction |= self.LCD_2LINE

        if withBacklight:
            self.blFlag=self.LCD_BACKLIGHT
        else:
            self.blFlag=self.LCD_NOBACKLIGHT

        # we can initialize the display only once after it had been powered on
        if(withOneTimeInit):
            self.bus.writeRaw8(0x3f)
            self.pulseEnable()
            sleep(0.0100) # TODO: Not clear if we have to wait that long
        self.write(self.displayfunction) # 0x28

        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)   # 0x08 + 0x4 = 0x0C
        self.write(self.LCD_ENTRYMODESET   | self.displaymode)      # 0x06
        self.clear()                           # 0x01
        self.home()

    def begin(self, cols, lines):
        if (lines > 1):
            self.numlines = lines
            self.displayfunction |= self.LCD_2LINE

    def home(self):
        self.write(self.LCD_RETURNHOME)  # set cursor position to zero
        self.delayMicroseconds(3000)  # this command takes a long time!

    def clear(self):
        self.write(self.LCD_CLEARDISPLAY)  # command to clear display
        self.delayMicroseconds(3000)  # 3000 microsecond sleep, clearing the display takes a long time

    def setCursor(self, col, row):
        self.row_offsets = [0x00, 0x40, 0x14, 0x54]
        if row > self.numlines:
            row = self.numlines
        row -= 1 # row_offsets is zero indexed
        self.write(self.LCD_SETDDRAMADDR | (col - 1 + self.row_offsets[row]))

    def noDisplay(self):
        """ Turn the display off (quickly) """
        self.displaycontrol &= ~self.LCD_DISPLAYON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def display(self):
        """ Turn the display on (quickly) """
        self.displaycontrol |= self.LCD_DISPLAYON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def noCursor(self):
        """ Turns the underline cursor off """
        self.displaycontrol &= ~self.LCD_CURSORON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def cursor(self):
        """ Turns the underline cursor on """
        self.displaycontrol |= self.LCD_CURSORON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def noBlink(self):
        """ Turn the blinking cursor off """
        self.displaycontrol &= ~self.LCD_BLINKON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def blink(self):
        """ Turn the blinking cursor on """
        self.displaycontrol |= self.LCD_BLINKON
        self.write(self.LCD_DISPLAYCONTROL | self.displaycontrol)

    def DisplayLeft(self):
        """ These commands scroll the display without changing the RAM """
        self.write(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT)

    def scrollDisplayRight(self):
        """ These commands scroll the display without changing the RAM """
        self.write(self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT)

    def leftToRight(self):
        """ This is for text that flows Left to Right """
        self.displaymode |= self.LCD_ENTRYLEFT
        self.write(self.LCD_ENTRYMODESET | self.displaymode)

    def rightToLeft(self):
        """ This is for text that flows Right to Left """
        self.displaymode &= ~self.LCD_ENTRYLEFT
        self.write(self.LCD_ENTRYMODESET | self.displaymode)

    def autoscroll(self):
        """ This will 'right justify' text from the cursor """
        self.displaymode |= self.LCD_ENTRYSHIFTINCREMENT
        self.write(self.LCD_ENTRYMODESET | self.displaymode)

    def noAutoscroll(self):
        """ This will 'left justify' text from the cursor """
        self.displaymode &= ~self.LCD_ENTRYSHIFTINCREMENT
        self.write(self.LCD_ENTRYMODESET | self.displaymode)

    def delayMicroseconds(self, microseconds):
        seconds = microseconds / float(1000000)  # divide microseconds by 1 million for seconds
        sleep(seconds)

    # clocks EN to latch command
    def pulseEnable(self):
        # uses underlying
        self.bus.writeRaw8((self.bus.bus.read_byte(self.addr) | self.EN | self.blFlag)) # | 0b0000 0100 # set "EN" high
        self.bus.writeRaw8(((self.bus.bus.read_byte(self.addr) | self.blFlag) & 0xFB)) # & 0b1111 1011 # set "EN" low

    # write data to lcd in 4 bit mode, 2 nibbles
    # high nibble is sent first
    def write(self, cmd):
        #write high nibble first
        self.bus.writeRaw8( (cmd & 0xF0) | self.blFlag )
        hi= self.bus.bus.read_byte(self.addr)
        self.pulseEnable()

        # write low nibble second ...
        self.bus.writeRaw8( (cmd << 4) | self.blFlag )
        lo= self.bus.bus.read_byte(self.addr)
        self.pulseEnable()
        self.bus.writeRaw8(self.blFlag)

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR
    def write_char(self, charvalue):
        controlFlag = self.blFlag | self.RS

        # write high nibble
        self.bus.writeRaw8((controlFlag | (charvalue & 0xF0)))
        self.pulseEnable()

        # write low nibble
        self.bus.writeRaw8((controlFlag | (charvalue << 4)))
        self.pulseEnable()
        self.bus.writeRaw8(self.blFlag)

    # put char function
    def putc(self, char):
        self.write_char(ord(char))

    def _setDDRAMAdress(self, line, col):
        # we write to the Data Display RAM (DDRAM)
        # TODO: Factor line offsets for other display organizations; this is for 20x4 only
        if line == 1:
            self.write(self.LCD_SETDDRAMADDR | (0x00 + col) )
        if line == 2:
            self.write(self.LCD_SETDDRAMADDR | (0x40 + col) )
        if line == 3:
            self.write(self.LCD_SETDDRAMADDR | (0x14 + col) )
        if line == 4:
            self.write(self.LCD_SETDDRAMADDR | (0x54 + col) )

    # put string function
    def message(self, string, line=1):
        """ Send string to LCD.  Newline wraps to next line.
            Starts at line 1 unless passed starting line """
        self._setDDRAMAdress(line, 0)
        for char in string:
            if char == '\n':
                line = 1 if line > 4 else line + 1
                self._setDDRAMAdress(line, 0)
            else:
                self.putc(char)

    def putString(self, string):
        """ Sends a string to LCD starting at current cursor position
            Doesn't handle newline character
        """
        for char in string:
            self.putc(char)

    # add custom characters (0 - 7)
    def lcd_load_custon_chars(self, fontdata):
        self.lcd_device.bus.write(0x40);
        for char in fontdata:
            for line in char:
                self.write_char(line)

if __name__ == '__main__':
    from time import localtime, strftime

    initFlag=False
    debug=False
    backlight=True

    lcd = Adafruit_PCF8547LCD(0x3f,1,backlight, initFlag)
    lcd.begin(20,4)
    msg = "+" + "=" * 18 + "+\n"
    msg += "|    20x4 LCD      |\n"
    msg += "|   w/ PCF8547     |\n"
    msg += "+" + "=" * 18 + "+"

    lcd.message(msg)
    sleep(3)

    lcd.clear()
    lcd.cursor()
    lcd.message("Cursor Positioning")
    lcd.setCursor(2,4)
    lcd.putString(". <- (2,4)")
    lcd.setCursor(6,2)
    lcd.putString(". <- (6,2)")
    lcd.setCursor(11,3)
    lcd.putString(".")
    lcd.setCursor(1,3)
    lcd.putString("(11,3) -> ")

    sleep(5)

    lcd.clear()
    lcd.noCursor()
    lcd.message("    Simple Clock    ",1)
    lcd.message("CTRL-C to quit",4)
    while True:
        lcd.message(strftime("%Y-%m-%d %H:%M:%S ", localtime()),3)
        sleep(1)
