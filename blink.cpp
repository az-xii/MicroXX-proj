#include <pico/stdlib.h>

const int LED_PIN = 25;  // Onboard LED on Raspberry Pi Pico

int main() {
    // Initialize LED pin
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    // Main loop
    while (true) {
        gpio_put(LED_PIN, 1);  // LED on
        sleep_ms(500);         // Wait 500ms
        gpio_put(LED_PIN, 0);  // LED off
        sleep_ms(500);         // Wait 500ms
    }

    return 0;
}