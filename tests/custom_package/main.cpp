#define STB_IMAGE_IMPLEMENTATION
#include <glad/glad.h>
#include <stb_image.h>
#include <stdint.h>
#include <stdio.h>

int main()
{
#if GL_VERSION_4_1 == 1
    printf("Using version greater than 4.1 (specified in config as 4.0)!\n");
    exit(EXIT_FAILURE);
#endif

    int w, h, comp;
    uint8_t* data = stbi_load("test.png", &w, &h, &comp, 0);
    printf("First pixel: %i, %i, %i\n", data[0], data[1], data[2]);
    stbi_image_free(data);
}
