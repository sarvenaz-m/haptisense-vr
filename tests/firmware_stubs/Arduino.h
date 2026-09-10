#pragma once
#include <stdint.h>
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define INPUT_PULLUP 2
#define A0 14
extern unsigned char MCUSR;
extern int mockArm, mockPwm;
extern unsigned long mockTime;
inline void pinMode(int, int) {}
inline void analogWrite(int, int v) { mockPwm = v; }
inline int digitalRead(int) { return mockArm; }
inline int analogRead(int) { return 512; }
inline unsigned long millis() { return mockTime; }
struct SerialMock {
  void begin(int) {} int available() { return 0; } char read() { return 0; }
  template<class T> void print(T) {} template<class T> void println(T) {}
};
extern SerialMock Serial;
