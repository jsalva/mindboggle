# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 2.8

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list

# Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# The program to use to edit the cache.
CMAKE_EDIT_COMMAND = /usr/bin/ccmake

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth

# Include any dependencies generated for this target.
include CMakeFiles/FsSurfaceReader.dir/depend.make

# Include the progress variables for this target.
include CMakeFiles/FsSurfaceReader.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/FsSurfaceReader.dir/flags.make

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o: CMakeFiles/FsSurfaceReader.dir/flags.make
CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o: FsSurfaceReader.cpp
	$(CMAKE_COMMAND) -E cmake_progress_report /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth/CMakeFiles $(CMAKE_PROGRESS_1)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building CXX object CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o"
	/usr/bin/c++   $(CXX_DEFINES) $(CXX_FLAGS) -o CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o -c /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth/FsSurfaceReader.cpp

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.i"
	/usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -E /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth/FsSurfaceReader.cpp > CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.i

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.s"
	/usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -S /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth/FsSurfaceReader.cpp -o CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.s

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.requires:
.PHONY : CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.requires

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.provides: CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.requires
	$(MAKE) -f CMakeFiles/FsSurfaceReader.dir/build.make CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.provides.build
.PHONY : CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.provides

CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.provides.build: CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o

# Object files for target FsSurfaceReader
FsSurfaceReader_OBJECTS = \
"CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o"

# External object files for target FsSurfaceReader
FsSurfaceReader_EXTERNAL_OBJECTS =

libFsSurfaceReader.a: CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o
libFsSurfaceReader.a: CMakeFiles/FsSurfaceReader.dir/build.make
libFsSurfaceReader.a: CMakeFiles/FsSurfaceReader.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --red --bold "Linking CXX static library libFsSurfaceReader.a"
	$(CMAKE_COMMAND) -P CMakeFiles/FsSurfaceReader.dir/cmake_clean_target.cmake
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/FsSurfaceReader.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/FsSurfaceReader.dir/build: libFsSurfaceReader.a
.PHONY : CMakeFiles/FsSurfaceReader.dir/build

CMakeFiles/FsSurfaceReader.dir/requires: CMakeFiles/FsSurfaceReader.dir/FsSurfaceReader.cpp.o.requires
.PHONY : CMakeFiles/FsSurfaceReader.dir/requires

CMakeFiles/FsSurfaceReader.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/FsSurfaceReader.dir/cmake_clean.cmake
.PHONY : CMakeFiles/FsSurfaceReader.dir/clean

CMakeFiles/FsSurfaceReader.dir/depend:
	cd /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth /home/arno/Documents/Projects/mindboggle/mindboggle/measure/surface_travel_depth/CMakeFiles/FsSurfaceReader.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/FsSurfaceReader.dir/depend

