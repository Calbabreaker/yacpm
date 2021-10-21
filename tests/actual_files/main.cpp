#include "stb_image.h"
#include <stdio.h>

int main()
{
#ifndef STBI_VERSION
    #error "stb_image was not built!"
#endif
    printf("Sucessful!\n");
}
