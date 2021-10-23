#include <glm/gtx/io.hpp>
#include <iostream>
#include <yacpm_library_test.h>

int main()
{
    glm::vec2 result = do_math(glm::vec2(1.0f, 2.0f), glm::vec2(4.0f, 2.0f));
    std::cout << result << std::endl;
}
