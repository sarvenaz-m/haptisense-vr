// Host-side logic harness only. Does NOT compile for AVR or validate electronics.
#include <cassert>
#include <cstring>
#include "Arduino.h"
unsigned char MCUSR = 0;
int mockArm = HIGH, mockPwm = 0;
unsigned long mockTime = 1000;
SerialMock Serial;
#include "../firmware/uno_erm_bench/uno_erm_bench.ino"
void send(const char *s) { strcpy(line, s); processLine(); }
int main() {
  setup(); assert(mockPwm == 0);
  send("H1,1,64"); assert(mockPwm == 0); // physical arm open
  mockArm = LOW; send("H1,2,64"); assert(mockPwm == 64);
  send("H1,3,65"); assert(mockPwm == 0);
  send("H1,3,-1"); assert(mockPwm == 0);
  send("H1,3,6,4"); assert(mockPwm == 0);
  send("H1,2147483648,64"); assert(mockPwm == 0);
  send("H1,2147483647,64"); assert(mockPwm == 64);
  mockTime += 150; loop(); assert(mockPwm == 0);
  send("H1,4,32"); mockArm = HIGH; loop(); assert(mockPwm == 0);
  unsigned long n;
  assert(!number("9999999999999999999999999", 64, n));
  assert(!number("", 64, n)); assert(!number("+1", 64, n));
  return 0;
}
