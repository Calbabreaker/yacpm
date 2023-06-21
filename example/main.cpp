#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>
#include <glad/glad.h>
#include <imgui.h>
#include <stdio.h>
#include <stdlib.h>

#define IMGUI_IMPL_OPENGL_LOADER_CUSTOM
#include <backends/imgui_impl_glfw.cpp>
#include <backends/imgui_impl_glfw.h>
#include <backends/imgui_impl_opengl3.cpp>
#include <backends/imgui_impl_opengl3.h>

struct WindowData
{
    int width;
    int height;
    WindowData(int p_width, int p_height) : width(p_width), height(p_height) {}
};

int main()
{
    GLFWwindow* window;

    if (!glfwInit())
    {
        fprintf(stderr, "Failed to init GLFW!\n");
        return EXIT_FAILURE;
    }

    WindowData window_data(640, 480);

    window = glfwCreateWindow(window_data.width, window_data.height, "Hello World", NULL, NULL);
    if (!window)
    {
        fprintf(stderr, "Failed to create window!\n");
        glfwTerminate();
        return EXIT_FAILURE;
    }

    glfwMakeContextCurrent(window);

    int status = gladLoadGLLoader(reinterpret_cast<GLADloadproc>(glfwGetProcAddress));
    if (!status)
    {
        fprintf(stderr, "Failed to load glad!\n");
        return EXIT_FAILURE;
    }

    glfwSetWindowUserPointer(window, &window_data);

    glfwSetWindowSizeCallback(window, [](GLFWwindow* win, int width, int height) {
        WindowData& data = *static_cast<WindowData*>(glfwGetWindowUserPointer(win));
        data.width = width;
        data.height = height;
    });

    // setup imgui
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard; // Enable Keyboard Controls
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;     // Enable Docking
    io.ConfigFlags |= ImGuiConfigFlags_ViewportsEnable;   // Enable Multi-Viewport

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 300 es");

    ImVec4 color = {0.4f, 0.8f, 1.0f, 1.0f};
    bool checked = false;

    while (!glfwWindowShouldClose(window))
    {
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glClearColor(0.2f, 0.2f, 0.2f, 1.0f);

        // begin imgui new frame
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        // render stuff
        ImGui::Begin("Yacpm");
        ImGui::TextColored(color, "Yacpm is very nice!");
        ImGui::ColorEdit3("Text Colour", reinterpret_cast<float*>(&color));

        ImGui::Checkbox("Nice", &checked);
        if (checked)
        {
            ImGui::Text("yes");
        }

        ImGui::End();

        // end imgui frame
        io.DisplaySize =
            ImVec2(static_cast<float>(window_data.width), static_cast<float>(window_data.height));
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        GLFWwindow* backup_current_context = glfwGetCurrentContext();
        ImGui::UpdatePlatformWindows();
        ImGui::RenderPlatformWindowsDefault();
        glfwMakeContextCurrent(backup_current_context);

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwTerminate();
}
