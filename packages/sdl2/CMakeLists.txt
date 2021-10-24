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

if(TARGET SDL2)
    set(SDL2_TARGET_USED SDL2)
elseif(TARGET SDL2-static)
    set(SDL2_TARGET_USED SDL2-static)
endif()

add_library(sdl2 ALIAS ${SDL2_TARGET_USED})
