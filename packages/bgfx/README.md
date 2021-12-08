# Bgfx

Set `BGFX_BUILD_COMPILERS` in yacpm variables to true to build shaderc and
texturec. Recommended to set `CMAKE_BUILD_TYPE` to Release to reduce build size
(it's quite big). Also set `BGFX_OPENGL_VERSION` and `BGFX_OPENGLES_VERSION` to
get their respective minimum version.
