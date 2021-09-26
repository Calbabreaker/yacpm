#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>
#include <stdio.h>

int main()
{
    int w, h, comp;
    uint8_t* data = stbi_load("test.png", &w, &h, &comp, 0);
    printf("First pixel: %i, %i, %i\n", data[0], data[1], data[2]);
    stbi_image_free(data);
}
