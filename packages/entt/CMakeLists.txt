add_library(entt INTERFACE)
target_include_directories(entt INTERFACE SYSTEM repository/src)
target_compile_features(entt INTERFACE cxx_std_17)
