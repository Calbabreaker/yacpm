#include "spdlog/spdlog.h"

int main()
{
    spdlog::info("Hello spdlog!");
    spdlog::error("Using actual remote yes: {}", "asdfasd");
    spdlog::warn("Warn message with arg: {} {}", "asdfasdf", 23489);
}
