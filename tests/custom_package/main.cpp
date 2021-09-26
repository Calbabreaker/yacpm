#include <stdint.h>

#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>

int main()
{
    uint8_t* data = stbi_load("test.png", nullptr, nullptr, nullptr, 0);
    stbi_image_free(data);
}
