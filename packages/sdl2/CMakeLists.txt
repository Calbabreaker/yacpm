# set these variables in yacpm.json to false to disable the modules from being built
option(SDL_AUDIO "Set to off to disable audio module" ON)
option(SDL_HAPTIC "Set to off to disable haptic module" ON)
option(SDL_JOYSTICK "Set to off to disable joystick module" ON)
option(SDL_LOCALE "Set to off to disable locale module" ON)
option(SDL_POWER "Set to off to disable power module" ON)
option(SDL_SENSOR "Set to off to disable sensor module" ON)
option(SDL_TIMERS "Set to off to disable timers module" ON)
option(SDL_VIDEO "Set to off to disable video module" ON)

add_subdirectory(repository)

if(TARGET SDL2)
    set(SDL2_TARGET_USED SDL2)
elseif(TARGET SDL2-static)
    set(SDL2_TARGET_USED SDL2-static)
endif()

add_library(sdl2 ALIAS ${SDL2_TARGET_USED})
