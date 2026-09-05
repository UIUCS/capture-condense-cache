cmake_minimum_required(VERSION 3.13)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Pull in Pico and FreeRTOS
include(pico_sdk_import.cmake)
#include(pico_extras_import_optional.cmake)
#include($ENV{FREERTOS_KERNEL_PATH}/portable/ThirdParty/GCC/RP2040/FreeRTOS_Kernel_import.cmake)


if(PICO_SDK_VERSION_STRING VERSION_LESS "1.3.0")
    message(FATAL_ERROR "Raspberry Pi Pico SDK version 1.3.0 (or later) required. Your version is ${PICO_SDK_VERSION_STRING}")
endif()

project(wolf_pico_examples C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

### Global Include Path
include_directories(config)
include_directories(include)
include_directories(${PICO_SDK_PATH}/src/rp2_common/pico_lwip/include)
include_directories(${PICO_SDK_PATH}/lib/lwip/contrib/ports/freertos/include)
include_directories(${PICO_SDK_PATH}/lib/lwip/src/include)
include_directories(${PICO_SDK_PATH}/src/rp2_common/pico_async_context/include)
### End of Global Include Path


add_executable(capture
    src/main.c
)

target_link_libraries(capture
    pico_stdlib
    pico_rand
    pico_cyw43_arch_none
)

pico_enable_stdio_usb(capture 1)
pico_enable_stdio_uart(capture 0)


# if (${PICO_PLATFORM} STREQUAL "rp2350")
#     add_compile_definitions(wolfssl WOLFSSL_SP_ARM_CORTEX_M_ASM)
# elseif (${PICO_PLATFORM} STREQUAL "rp2350-riscv")
#     add_compile_definitions(wolfSSL WOLFSSL_SP_RISCV32)
# else()
#     add_compile_definitions(wolfssl WOLFSSL_SP_ARM_THUMB_ASM)
# endif()

pico_add_extra_outputs(capture)
### End of Benchmark wolfCrypt algorithms