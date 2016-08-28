// Setup Board: Sparkfun Pro-micro and Processor: ATmega32U4 (5V/16MHz) by setting File->Preferences with the Additional Boards Manager URLs: https://raw.githubusercontent.com/sparkfun/Arduino_Boards/master/IDE_Board_Manager/package_sparkfun_index.json
// Setup Light WS2812 in Sketch->Include Library->Add .ZIP Library...: https://github.com/cpldcpu/light_ws2812/raw/master/light_ws2812_Arduino/light_WS2812.zip

// FUTURE IMPROVEMENTS:
// - More test mode programs
// - Serial command to go into (specific) test mode program
// - !Serial check in loop / timeout on serial communication to go into test mode
// - Better way to consume junk bytes (look for next GO alignment)
// - Since we do not use the read pixel state of the WS2812 lib, we can reuse the RGB byte buffer to save significant buffer space, but since we now only control so little pixels this is a non-issue.
//    We now use about 189 + 12 * HEIGHT bytes in 'dynamic memory' and malloc HEIGHT * WIDTH * 3 bytes on the heap (of 2560 bytes maximum), but we need to keep some space for the stack.

// Using https://github.com/cpldcpu/light_ws2812/
// This library obviously has a memory leak (a malloc in constructor but no free in destructor) at the time of writing, but you don't want to free it anyway and then there is the AVR memory 'management' that will leave your memory fragmented...
#include <WS2812.h>

// Height = pins, Width = LEDs in a cascading row/line setup
#define HEIGHT 11
#define WIDTH  17

// See http://stackoverflow.com/a/809465 (used for HEIGHT = sizeof(pins))
#define COMPILER_ASSERT(predicate, file) _impl_CASSERT_LINE(predicate,__LINE__,file)
#define _impl_PASTE(a,b) a##b
#define _impl_CASSERT_LINE(predicate, line, file) \
    typedef char _impl_PASTE(assertion_failed_##file##_,line)[2*!!(predicate)-1];

// Trick to construct array of objects with parameter in constructor in pre-C11
class WS2812_strip : public WS2812 {
    public: 
        WS2812_strip() : WS2812(WIDTH) {
            this->setColorOrderRGB();
        }
};

WS2812_strip lines[HEIGHT];
cRGB pixel;

void setup() {
    // Pin out of Pro Micro:  https://learn.sparkfun.com/tutorials/pro-micro--fio-v3-hookup-guide#hardware-overview-pro-micro
    // 21 = A3, 20 = A2, 19 = A1, 18 = A0

    const byte pins[] = {21, 20, 19, 18, 6, 5, 4, 3, 9, 8, 7};
    // Don't bite ourselves twice, check the height = pins at compile time:
    COMPILER_ASSERT(sizeof(pins) == HEIGHT, height_equals_pins);

    for (int y = 0; y < HEIGHT; y++) {
        lines[y].setOutput(pins[y]);
    }

    Serial.begin(9600);

    // Test mode when we have no serial connection:
    // show diagonal (from top-left) fills of red, green and blue to test all RGB LEDs and connections
    cRGB red = { 255, 0, 0};
    cRGB green = { 0, 255, 0};
    cRGB blue = { 0, 0, 255};
    cRGB bottomRight = red;
    cRGB topLeft = green;

    int distance = 0;
    int color = 0;

    while (!Serial) {
        for (int y = 0; y < HEIGHT; y++) {
            for (int x = 0; x < WIDTH; x++) {
                lines[y].set_crgb_at(x, x + y < distance ? topLeft : bottomRight);
            }
        }
        for (int y = 0; y < HEIGHT; y++) {
            lines[y].sync();
        }
        
        distance = (distance + 1) % (WIDTH + HEIGHT);
        if (distance == 0) {
            color = (color + 1) % 3;
            if (color == 0) {
                bottomRight = red;
                topLeft = green;
            } else if (color == 1) {
                bottomRight = green;
                topLeft = blue;
            } else if (color == 2) {
                bottomRight = blue;
                topLeft = red;
            }
        }
        delay(100);
    }
}

void loop() {
    // When we have a full line in the buffer, process
    if (Serial.available() >= 3 + (WIDTH * 3)) {
        // Format = "GO" + 1 byte for the line (0-HEIGHT-1) followed by WIDTH × 3 bytes (RGB) per pixel (there is *no* newline)
        if (Serial.read() == 'G' && Serial.read() == 'O') {
            int y = Serial.read();
            // Print some feedback
            Serial.print("OK line ");
            Serial.println(y);
            if (y >= 0 && y < HEIGHT) {
                for (int x = 0; x < WIDTH; x++) {
                    pixel = { Serial.read(), Serial.read(), Serial.read()};
                    lines[y].set_crgb_at(x, pixel);
                }
                lines[y].sync();
                // Only delay after the last line's sync, so refresh rates can be > 100 Hz
                if (y == HEIGHT - 1) {
                    delay(10);
                }
            }
        } else {
            // If the line does not start with GO, consume all bytes in the buffer, it might be better to look for GO (if the buffer is still enough)
            Serial.println("Error");
            while(Serial.available() > 0) {
                Serial.read();
            }
        }
    }
}
