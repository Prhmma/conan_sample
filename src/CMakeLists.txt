 cmake_minimum_required(VERSION 3.16.2)
 project(playWithConan)
 
 add_executable(main main.cpp)
 target_link_libraries(main ${CONAN_LIBS})