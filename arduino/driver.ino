
#include <Adafruit_NeoPixel.h>

#define DIN_PIN 6
#define NUM_LEDS 300
#define COMMAND_BUFFER_LENGTH 7
#define SET_LED_COMMMAND 0x1
#define RENDER_COMMAND 0x2
#define RESET_COMMAND 0x3
#define SET_BRIGHTNESS_COMMAND 0x4

Adafruit_NeoPixel leds(NUM_LEDS, DIN_PIN, NEO_GRB + NEO_KHZ800);
byte command_buffer[COMMAND_BUFFER_LENGTH];
byte buffer_position;

void setup()
{
    SerialUSB.begin(115200);
    leds.begin();
    clearBuffer();
    reset();
}

void loop()
{
    processSerial();
}

void clearBuffer()
{
    buffer_position = 0;
    for (int index = 0; index < COMMAND_BUFFER_LENGTH; index++)
    {
        command_buffer[index] = 0x0;
    }
}

void reset()
{
    leds.clear();
    leds.show();
}

void render()
{
    leds.show();
}

void setLed()
{
    leds.setPixelColor(
        command_buffer[1] << 8 | command_buffer[2],
        command_buffer[3] << 24 |
            command_buffer[4] << 16 |
            command_buffer[5] << 8 |
            command_buffer[6]);
}

void setBrightness() {
    leds.setBrightness(command_buffer[1]);
    reset();
}

void processCommand()
{
    switch (command_buffer[0])
    {
    case SET_LED_COMMMAND:
        setLed();
        break;
    case RENDER_COMMAND:
        render();
        break;
    case RESET_COMMAND:
        reset();
        break;
    case SET_BRIGHTNESS_COMMAND:
        setBrightness();
    default:
        break;
    }
    clearBuffer();
}

void processSerial()
{
    if (SerialUSB.available())
    {
        byte incoming_byte = Serial.read();

        command_buffer[buffer_position] = incoming_byte;
        buffer_position++;

        if (buffer_position == COMMAND_BUFFER_LENGTH)
        {
            processCommand();
        }
    }
}