cmake_minimum_required(VERSION 3.24)
project(PtRenew VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.12 REQUIRED COMPONENTS Core Gui Widgets)
include(CTest)

add_library(pt_core STATIC
    src/application/CommandCatalog.cpp
    src/application/CommandCatalog.h
    src/domain/DocumentInfo.h
    src/io/LegacyPcbInspector.cpp
    src/io/LegacyPcbInspector.h
)
target_include_directories(pt_core PUBLIC src)
target_link_libraries(pt_core PUBLIC Qt6::Core)

add_library(pt_ui STATIC
    src/ui/BoardCanvas.cpp
    src/ui/BoardCanvas.h
    src/ui/MainWindow.cpp
    src/ui/MainWindow.h
)
target_link_libraries(pt_ui PUBLIC pt_core Qt6::Widgets)

qt_add_executable(pt-renew WIN32 src/main.cpp)
target_link_libraries(pt-renew PRIVATE pt_ui)

foreach(target pt_core pt_ui pt-renew)
    if(MSVC)
        target_compile_options(${target} PRIVATE /utf-8 /W4 /permissive-)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endforeach()

if(BUILD_TESTING)
    find_package(Qt6 6.12 REQUIRED COMPONENTS Test)
    qt_add_executable(pt-shell-tests tests/ShellTests.cpp)
    set_target_properties(pt-shell-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-shell-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-shell-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-shell-tests COMMAND pt-shell-tests -o -,txt -o shell-test-results.txt,txt)
    set_tests_properties(pt-shell-tests PROPERTIES TIMEOUT 60)
endif()

install(TARGETS pt-renew RUNTIME DESTINATION .)
