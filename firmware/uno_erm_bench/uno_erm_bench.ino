// UNVALIDATED BENCH TEMPLATE. Arduino UNO R3 (ATmega328P) only.
// ERM PWM DUTY ONLY: no commanded Newtons or independent mechanical frequency.
// External low-voltage rated driver, flyback diode, common ground and fuse required.
// D2 physical ARM switch to GND; open = disabled. No body attachment/human trial.
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <avr/wdt.h>

const uint8_t MOTOR_PIN = 9, ARM_PIN = 2;
const unsigned long STALE_MS = 150;
char line[48];
uint8_t used = 0, applied = 0;
bool dropping = false;
unsigned long lastCommand = 0;

void stopMotor() { applied = 0; analogWrite(MOTOR_PIN, 0); }

bool number(const char *s, unsigned long maximum, unsigned long &value) {
  if (!s || !*s) return false;
  value = 0;
  for (; *s; ++s) {
    if (*s < '0' || *s > '9') return false;
    unsigned long digit = *s - '0';
    if (value > (maximum - digit) / 10UL || digit > maximum) return false;
    value = value * 10UL + digit;
  }
  return value <= maximum;
}

void processLine() {
  unsigned long seq, pwm;
  char *a = strchr(line, ',');
  char *b = a ? strchr(a + 1, ',') : NULL;
  if (!a || !b || strchr(b + 1, ',')) { stopMotor(); return; }
  *a = 0; *b = 0;
  if (strcmp(line, "H1") || !number(a + 1, 2147483647UL, seq) || !number(b + 1, 64UL, pwm)) {
    stopMotor(); return;
  }
  lastCommand = millis();
  applied = digitalRead(ARM_PIN) == LOW ? (uint8_t)pwm : 0;
  analogWrite(MOTOR_PIN, applied);
  Serial.print("A1,"); Serial.print(seq); Serial.print(','); Serial.print(applied);
  Serial.print(','); Serial.print(analogRead(A0)); Serial.print(','); Serial.println(millis());
}

void setup() {
  MCUSR = 0; wdt_disable();
  pinMode(MOTOR_PIN, OUTPUT); pinMode(ARM_PIN, INPUT_PULLUP); stopMotor();
  Serial.begin(115200);
  // Stock UNO bootloader compatibility must be checked before arming hardware.
  wdt_enable(WDTO_250MS);
}

void loop() {
  wdt_reset();
  if (digitalRead(ARM_PIN) != LOW || (unsigned long)(millis() - lastCommand) >= STALE_MS) stopMotor();
  for (uint8_t budget = 0; budget < 48 && Serial.available(); ++budget) {
    char c = Serial.read();
    if (c == '\n') {
      if (!dropping) { line[used] = 0; processLine(); }
      used = 0; dropping = false;
    } else if (dropping) { /* discard remainder after overflow */ }
    else if (used >= sizeof(line) - 1 || c < 32 || c > 126) {
      stopMotor(); used = 0; dropping = true;
    } else line[used++] = c;
  }
}
