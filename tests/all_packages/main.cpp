#include "bgfx/bgfx.h"
#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>
#include <SDL.h>
#include <SFML/Graphics.hpp>
#include <Thor/Random.hpp>
#include <bgfx/bgfx.h>
#include <entt/entt.hpp>
#include <glad/glad.h>
#include <glm/glm.hpp>
#include <imgui.h>
#include <rttr/registration.h>
#include <spdlog/spdlog.h>
#include <stb_image.h>
#include <yaml-cpp/yaml.h>
#include <zlib.h>

int main()
{
    //
    // Runs a function from a library to see if yacpm works.
    // Put functions in order of usage in yacpm (package name alphabetical order).
    //

    bgfx::Init{};
    printf("entt version: %i.%i.%i\n", ENTT_VERSION_MAJOR, ENTT_VERSION_MINOR, ENTT_VERSION_PATCH);
    gladLoadGL();
    glfwGetCurrentContext();
    glm::vec2(1.0f, 2.0f) * 2.0f;
    ImGui::GetCurrentContext();
    rttr::variant(1.0f).clear();
    SDL_Init(SDL_INIT_EVENTS);
    sf::CircleShape(100.0f).setRadius(10.0f);
    spdlog::info("Test");
    printf("stbi version: %i\n", STBI_VERSION);
    printf("random number: %i", thor::random(0, 1));
    YAML::Node node = YAML::Load("[1, 2, 3]");
    printf("zlib version: %s", zlibVersion());

    printf("Yay! Sucessfully built every package in yacpm!\n");
}
