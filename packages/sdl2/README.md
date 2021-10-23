# SDL2

Remove SDL2/ in #include. So do `#include <SDL.h>` not `#include <SDL2/SDL.h>`..

Disable these sdl modules:
`SDL_AUDIO, SDL_HAPTIC, SDL_JOYSTICK, SDL_LOCALE, SDL_POWER, SDL_SENSOR, SDL_TIMERS, SDL_VIDEO`
from being built by setting the cmake variable to false in yacpm.json.
