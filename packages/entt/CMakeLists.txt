add_library(entt INTERFACE)
target_include_directories(entt SYSTEM INTERFACE repository/src)
target_compile_features(entt INTERFACE cxx_std_17)
