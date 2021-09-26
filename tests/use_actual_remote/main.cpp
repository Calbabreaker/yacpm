#include "spdlog/spdlog.h"

int main()
{
    spdlog::info("Hello spdlog!");
    spdlog::error("Error message with arg: {}", "asdfasd");
    spdlog::warn("Warn message with arg: {} {}", "asdfasdf", 23489);
}
