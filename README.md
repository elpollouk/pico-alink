# pico-alink

A [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/) DCC command station implementation for testing.

Compatible with the [Waveshare RP2040-LCD-0.96](https://www.waveshare.com/wiki/RP2040-LCD-0.96), set `LCD_LOGER` to `lcd_rp2040lcd096` in `config.py` to enable.

Debug menu can be accessed by sending `~` to the device using [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).

## Installation

1. Install [mpreamote](https://docs.micropython.org/en/latest/reference/mpremote.html).
2. Connect your [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/).
3. Run install.py.
4. Disconnect and reconnect your Pico.

## Debug Loco

It is possible to invoke debug functions by sending function requests to loco id `9999`. The supported functions are:

|Function|Action|
|---|---|
| F0 | Write current run time stats to log |
| F27 | Delete boot.py from Pico file system |
| F28 | Exit the Python script |