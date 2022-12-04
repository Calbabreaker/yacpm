#include <stb_image.h>
#include <stdio.h>
#include <yacpm_library_test.h>

#ifndef STBI_VERSION
    #error "stb_image was not built!"
#endif

int main()
{
    do_math(glm::vec2(1.0f, 2.0f), glm::vec2(4.0f, 2.0f));
    printf("STBI version: %i. Sucessful!\n", STBI_VERSION);
}
