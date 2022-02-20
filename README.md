# pico-alink

A Raspberry Pi Pico DCC command station implementation for testing.

Compatible with the [Waveshare RP2040-LCD-0.96](https://www.waveshare.com/wiki/RP2040-LCD-0.96), set `LCD_LOGER` to `lcd_rp2040lcd096` in `config.py` to enable.

Debug menu can be accessed by sending `~` to the device using [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).

## Debug Loco

It is possible to invoke debug functions by sending function requests to loco id `9999`. The supported functions are:

|Function|Action|
|---|---|
| F0 | Write current run time stats to log |
| F27 | Delete boot.py from Pico file system |
| F28 | Exit the Python script |