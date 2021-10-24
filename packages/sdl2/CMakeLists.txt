# set these variables in yacpm.json to false to disable the modules from being built
set(SDL_AUDIO ON)
set(SDL_HAPTIC ON)
set(SDL_JOYSTICK ON)
set(SDL_LOCALE ON)
set(SDL_POWER ON)
set(SDL_SENSOR ON)
set(SDL_TIMERS ON)
set(SDL_VIDEO ON)

add_subdirectory(repository)

add_library(sdl2 ALIAS 
    $<TARGET_NAME_IF_EXISTS:SDL2>
    $<TARGET_NAME_IF_EXISTS:SDL2-static>)
