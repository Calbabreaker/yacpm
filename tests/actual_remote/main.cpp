#include <stb_image.h>
#include <stdio.h>

#ifndef STBI_VERSION
    #error "stb_image was not built!"
#endif

int main()
{
    printf("STBI version: %i. Sucessful!\n", STBI_VERSION);
}
