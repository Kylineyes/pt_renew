cmake_minimum_required(VERSION 3.24)
project(PtRenew VERSION 0.11.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.12 REQUIRED COMPONENTS Core Gui Widgets Concurrent)
include(CTest)

option(PT_ENABLE_ASYNC_EXPERIMENT "启用独立异步验收门闩与事件记录，禁止用于稳定发布" OFF)
if(PT_ENABLE_ASYNC_EXPERIMENT AND NOT WIN32)
    message(FATAL_ERROR "异步实验门闩当前只支持 Windows。")
endif()

add_library(pt_core STATIC
    src/application/BoardEditSession.h
    src/application/BoardEditSession.cpp
    src/application/CommandCatalog.cpp
    src/application/CommandCatalog.h
    src/application/ComponentTableModel.h
    src/application/ComponentTableModel.cpp
    src/domain/Measurement.h
    src/domain/DocumentInfo.h
    src/domain/PrimitiveId.h
    src/domain/BoardDocument.h
    src/domain/BoardDocument.cpp
    src/io/LegacyPcbReader.h
    src/io/LegacyPcbReader.cpp
    src/io/DosText.h
    src/domain/Netlist.h
    src/io/LegacyNetlistReader.h
    src/io/LegacyNetlistReader.cpp
    src/application/NetlistMapping.h
    src/application/NetlistMapping.cpp
    src/domain/FootprintLibrary.h
    src/io/LegacyLibraryReader.h
    src/io/LegacyLibraryReader.cpp
    src/io/LegacyPcbInspector.cpp
    src/io/LegacyPcbInspector.h
)
target_include_directories(pt_core PUBLIC src)
target_link_libraries(pt_core PUBLIC Qt6::Core)
if(PT_ENABLE_ASYNC_EXPERIMENT)
    target_sources(pt_core PRIVATE src/experiment/AsyncExperiment.cpp src/experiment/AsyncExperiment.h)
    target_compile_definitions(pt_core PUBLIC PT_ENABLE_ASYNC_EXPERIMENT=1)
endif()

add_library(pt_geometry STATIC
    src/geometry/BoardGeometry.h
    src/geometry/BoardGeometry.cpp
    src/geometry/EndpointSnapIndex.h
    src/geometry/EndpointSnapIndex.cpp
    src/geometry/CopperConnectivity.h
    src/geometry/CopperConnectivity.cpp
)
target_link_libraries(pt_geometry PUBLIC pt_core Qt6::Gui)

add_library(pt_ui STATIC
    src/ui/BoardCanvas.cpp
    src/ui/BoardCanvas.h
    src/ui/BoardRenderer.h
    src/ui/BoardRenderer.cpp
    src/ui/MainWindow.cpp
    src/ui/MainWindow.h
    src/ui/ComponentBrowser.h
    src/ui/ComponentBrowser.cpp
    src/ui/NetlistBrowser.h
    src/ui/NetlistBrowser.cpp
    src/ui/LibraryBrowser.h
    src/ui/LibraryBrowser.cpp
)
target_link_libraries(pt_ui PUBLIC pt_geometry Qt6::Widgets Qt6::Concurrent)

qt_add_executable(pt-renew WIN32 src/main.cpp)
target_link_libraries(pt-renew PRIVATE pt_ui)

add_executable(pt-library-check tools/InspectLibrary.cpp)
set_target_properties(pt-library-check PROPERTIES WIN32_EXECUTABLE FALSE)
target_link_libraries(pt-library-check PRIVATE pt_core)

add_executable(pt-netlist-check tools/InspectNetlist.cpp)
set_target_properties(pt-netlist-check PROPERTIES WIN32_EXECUTABLE FALSE)
target_link_libraries(pt-netlist-check PRIVATE pt_core)

add_executable(pt-copper-check tools/InspectCopper.cpp)
set_target_properties(pt-copper-check PROPERTIES WIN32_EXECUTABLE FALSE)
target_link_libraries(pt-copper-check PRIVATE pt_geometry)

foreach(target pt_core pt_geometry pt_ui pt-renew pt-library-check pt-netlist-check pt-copper-check)
    if(MSVC)
        target_compile_options(${target} PRIVATE /utf-8 /W4 /permissive-)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endforeach()

if(BUILD_TESTING)
    find_package(Python3 QUIET COMPONENTS Interpreter)
    if(Python3_Interpreter_FOUND)
        add_test(NAME pt-overlay-tests
            COMMAND "${Python3_EXECUTABLE}" -m unittest discover
                -s "${CMAKE_CURRENT_SOURCE_DIR}/tests" -p test_legacy_overlays.py)
        set_tests_properties(pt-overlay-tests PROPERTIES TIMEOUT 30)
        add_test(NAME pt-legacy-text-tests
            COMMAND "${Python3_EXECUTABLE}" -m unittest discover
                -s "${CMAKE_CURRENT_SOURCE_DIR}/tests" -p test_legacy_text.py)
        set_tests_properties(pt-legacy-text-tests PROPERTIES TIMEOUT 30)
    else()
        message(STATUS "未找到 Python 3：跳过覆盖模块及文字研究工具测试，Qt 应用构建不受影响。")
    endif()
    find_package(Qt6 6.12 REQUIRED COMPONENTS Test)
    if(PT_ENABLE_ASYNC_EXPERIMENT)
        qt_add_executable(pt-async-experiment-tests tests/AsyncExperimentTests.cpp)
        set_target_properties(pt-async-experiment-tests PROPERTIES WIN32_EXECUTABLE FALSE)
        target_link_libraries(pt-async-experiment-tests PRIVATE pt_ui Qt6::Test)
        if(MSVC)
            target_compile_options(pt-async-experiment-tests PRIVATE /utf-8 /W4 /permissive-)
        endif()
        add_test(NAME pt-async-experiment-tests COMMAND pt-async-experiment-tests -o -,txt -o async-experiment-results.txt,txt)
        set_tests_properties(pt-async-experiment-tests PROPERTIES TIMEOUT 45 ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
    endif()
    qt_add_executable(pt-editing-tests tests/EditingTests.cpp)
    set_target_properties(pt-editing-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-editing-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-editing-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-editing-tests COMMAND pt-editing-tests -o -,txt -o editing-test-results.txt,txt)
    set_tests_properties(pt-editing-tests PROPERTIES TIMEOUT 90)
    qt_add_executable(pt-shell-tests tests/ShellTests.cpp)
    set_target_properties(pt-shell-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-shell-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-shell-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-shell-tests COMMAND pt-shell-tests -o -,txt -o shell-test-results.txt,txt)
    set_tests_properties(pt-shell-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-pcb-tests tests/PcbTests.cpp)
    set_target_properties(pt-pcb-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-pcb-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-pcb-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-pcb-tests COMMAND pt-pcb-tests -o -,txt -o pcb-test-results.txt,txt)
    set_tests_properties(pt-pcb-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-selection-tests tests/SelectionTests.cpp)
    set_target_properties(pt-selection-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-selection-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-selection-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-selection-tests COMMAND pt-selection-tests -o -,txt -o selection-test-results.txt,txt)
    set_tests_properties(pt-selection-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-navigation-tests tests/NavigationTests.cpp)
    set_target_properties(pt-navigation-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-navigation-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-navigation-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-navigation-tests COMMAND pt-navigation-tests -o -,txt -o navigation-test-results.txt,txt)
    set_tests_properties(pt-navigation-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-endpoint-snap-tests tests/EndpointSnapTests.cpp)
    set_target_properties(pt-endpoint-snap-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-endpoint-snap-tests PRIVATE pt_ui Qt6::Test)
    if(MSVC)
        target_compile_options(pt-endpoint-snap-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-endpoint-snap-tests COMMAND pt-endpoint-snap-tests -o -,txt -o endpoint-snap-test-results.txt,txt)
    set_tests_properties(pt-endpoint-snap-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-library-tests tests/LibraryTests.cpp)
    set_target_properties(pt-library-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-library-tests PRIVATE pt_ui Qt6::Test)
    add_dependencies(pt-library-tests pt-library-check)
    if(MSVC)
        target_compile_options(pt-library-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-library-tests COMMAND pt-library-tests -o -,txt -o library-test-results.txt,txt)
    set_tests_properties(pt-library-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-netlist-tests tests/NetlistTests.cpp)
    set_target_properties(pt-netlist-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-netlist-tests PRIVATE pt_ui Qt6::Test)
    add_dependencies(pt-netlist-tests pt-netlist-check)
    if(MSVC)
        target_compile_options(pt-netlist-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-netlist-tests COMMAND pt-netlist-tests -o -,txt -o netlist-test-results.txt,txt)
    set_tests_properties(pt-netlist-tests PROPERTIES TIMEOUT 60)
    qt_add_executable(pt-copper-tests tests/CopperTests.cpp)
    set_target_properties(pt-copper-tests PROPERTIES WIN32_EXECUTABLE FALSE)
    target_link_libraries(pt-copper-tests PRIVATE pt_ui Qt6::Test)
    add_dependencies(pt-copper-tests pt-copper-check)
    if(MSVC)
        target_compile_options(pt-copper-tests PRIVATE /utf-8 /W4 /permissive-)
    endif()
    add_test(NAME pt-copper-tests COMMAND pt-copper-tests -o -,txt -o copper-test-results.txt,txt)
    set_tests_properties(pt-copper-tests PROPERTIES TIMEOUT 60)
endif()

install(TARGETS pt-renew RUNTIME DESTINATION .)
