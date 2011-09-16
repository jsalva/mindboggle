# Generated by CMake 2.8.4

IF("${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" GREATER 2.4)
  # Information for CMake 2.6 and above.
  SET("MapReduceMPI_LIB_DEPENDS" "general;-lgdi32;general;mpistubs;")
  SET("mpistubs_LIB_DEPENDS" "general;-lgdi32;general;vtksys;")
  SET("vtkCharts_LIB_DEPENDS" "general;-lgdi32;general;vtkHybrid;general;vtkViews;general;vtkIO;general;vtkftgl;general;vtkfreetype;")
  SET("vtkCommon_LIB_DEPENDS" "general;-lgdi32;general;vtksys;general;wsock32;")
  SET("vtkDICOMParser_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkFiltering_LIB_DEPENDS" "general;-lgdi32;general;vtkCommon;")
  SET("vtkGenericFiltering_LIB_DEPENDS" "general;-lgdi32;general;vtkFiltering;general;vtkGraphics;")
  SET("vtkGeovis_LIB_DEPENDS" "general;-lgdi32;general;vtkWidgets;general;vtkViews;general;vtkproj4;general;glu32;general;opengl32;")
  SET("vtkGraphics_LIB_DEPENDS" "general;-lgdi32;general;vtkFiltering;general;vtkverdict;")
  SET("vtkHybrid_LIB_DEPENDS" "general;-lgdi32;general;vtkRendering;general;vtkIO;general;vtkexoIIc;general;vtkftgl;")
  SET("vtkIO_LIB_DEPENDS" "general;-lgdi32;general;vtkFiltering;general;vtkDICOMParser;general;vtkNetCDF;general;vtkNetCDF_cxx;general;vtkmetaio;general;vtksqlite;general;vtkpng;general;vtkzlib;general;vtkjpeg;general;vtktiff;general;vtkexpat;general;vtksys;")
  SET("vtkImaging_LIB_DEPENDS" "general;-lgdi32;general;vtkFiltering;")
  SET("vtkInfovis_LIB_DEPENDS" "general;-lgdi32;general;vtkWidgets;general;vtklibxml2;general;vtkalglib;")
  SET("vtkNetCDF_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkNetCDF_cxx_LIB_DEPENDS" "general;-lgdi32;general;vtkNetCDF;")
  SET("vtkRendering_LIB_DEPENDS" "general;-lgdi32;general;vtkGraphics;general;vtkImaging;general;vtkIO;general;vtkftgl;general;vtkfreetype;general;opengl32;")
  SET("vtkViews_LIB_DEPENDS" "general;-lgdi32;general;vtkInfovis;")
  SET("vtkVolumeRendering_LIB_DEPENDS" "general;-lgdi32;general;vtkRendering;general;vtkIO;general;opengl32;")
  SET("vtkWidgets_LIB_DEPENDS" "general;-lgdi32;general;vtkRendering;general;vtkHybrid;general;opengl32;")
  SET("vtkalglib_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkexoIIc_LIB_DEPENDS" "general;-lgdi32;general;vtkNetCDF;")
  SET("vtkexpat_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkfreetype_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkftgl_LIB_DEPENDS" "general;-lgdi32;general;opengl32;general;vtkfreetype;")
  SET("vtkjpeg_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtklibxml2_LIB_DEPENDS" "general;-lgdi32;general;vtkzlib;general;-lpthread;")
  SET("vtkmetaio_LIB_DEPENDS" "general;-lgdi32;general;vtkzlib;general;vtksys;general;comctl32;general;wsock32;")
  SET("vtkpng_LIB_DEPENDS" "general;-lgdi32;general;vtkzlib;")
  SET("vtkproj4_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtksqlite_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtksys_LIB_DEPENDS" "general;-lgdi32;general;ws2_32;")
  SET("vtktiff_LIB_DEPENDS" "general;-lgdi32;general;vtkzlib;general;vtkjpeg;")
  SET("vtkverdict_LIB_DEPENDS" "general;-lgdi32;")
  SET("vtkzlib_LIB_DEPENDS" "general;-lgdi32;")
ELSE("${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" GREATER 2.4)
  # Information for CMake 2.4 and lower.
  SET("MapReduceMPI_LIB_DEPENDS" "-lgdi32;mpistubs;")
  SET("mpistubs_LIB_DEPENDS" "-lgdi32;vtksys;")
  SET("vtkCharts_LIB_DEPENDS" "-lgdi32;vtkHybrid;vtkViews;vtkIO;vtkftgl;vtkfreetype;")
  SET("vtkCommon_LIB_DEPENDS" "-lgdi32;vtksys;wsock32;")
  SET("vtkDICOMParser_LIB_DEPENDS" "-lgdi32;")
  SET("vtkFiltering_LIB_DEPENDS" "-lgdi32;vtkCommon;")
  SET("vtkGenericFiltering_LIB_DEPENDS" "-lgdi32;vtkFiltering;vtkGraphics;")
  SET("vtkGeovis_LIB_DEPENDS" "-lgdi32;vtkWidgets;vtkViews;vtkproj4;glu32;opengl32;")
  SET("vtkGraphics_LIB_DEPENDS" "-lgdi32;vtkFiltering;vtkverdict;")
  SET("vtkHybrid_LIB_DEPENDS" "-lgdi32;vtkRendering;vtkIO;vtkexoIIc;vtkftgl;")
  SET("vtkIO_LIB_DEPENDS" "-lgdi32;vtkFiltering;vtkDICOMParser;vtkNetCDF;vtkNetCDF_cxx;vtkmetaio;vtksqlite;vtkpng;vtkzlib;vtkjpeg;vtktiff;vtkexpat;vtksys;")
  SET("vtkImaging_LIB_DEPENDS" "-lgdi32;vtkFiltering;")
  SET("vtkInfovis_LIB_DEPENDS" "-lgdi32;vtkWidgets;vtklibxml2;vtkalglib;")
  SET("vtkNetCDF_LIB_DEPENDS" "-lgdi32;")
  SET("vtkNetCDF_cxx_LIB_DEPENDS" "-lgdi32;vtkNetCDF;")
  SET("vtkRendering_LIB_DEPENDS" "-lgdi32;vtkGraphics;vtkImaging;vtkIO;vtkftgl;vtkfreetype;opengl32;")
  SET("vtkViews_LIB_DEPENDS" "-lgdi32;vtkInfovis;")
  SET("vtkVolumeRendering_LIB_DEPENDS" "-lgdi32;vtkRendering;vtkIO;opengl32;")
  SET("vtkWidgets_LIB_DEPENDS" "-lgdi32;vtkRendering;vtkHybrid;opengl32;")
  SET("vtkalglib_LIB_DEPENDS" "-lgdi32;")
  SET("vtkexoIIc_LIB_DEPENDS" "-lgdi32;vtkNetCDF;")
  SET("vtkexpat_LIB_DEPENDS" "-lgdi32;")
  SET("vtkfreetype_LIB_DEPENDS" "-lgdi32;")
  SET("vtkftgl_LIB_DEPENDS" "-lgdi32;opengl32;vtkfreetype;")
  SET("vtkjpeg_LIB_DEPENDS" "-lgdi32;")
  SET("vtklibxml2_LIB_DEPENDS" "-lgdi32;vtkzlib;-lpthread;")
  SET("vtkmetaio_LIB_DEPENDS" "-lgdi32;vtkzlib;vtksys;comctl32;wsock32;")
  SET("vtkpng_LIB_DEPENDS" "-lgdi32;vtkzlib;")
  SET("vtkproj4_LIB_DEPENDS" "-lgdi32;")
  SET("vtksqlite_LIB_DEPENDS" "-lgdi32;")
  SET("vtksys_LIB_DEPENDS" "-lgdi32;ws2_32;")
  SET("vtktiff_LIB_DEPENDS" "-lgdi32;vtkzlib;vtkjpeg;")
  SET("vtkverdict_LIB_DEPENDS" "-lgdi32;")
  SET("vtkzlib_LIB_DEPENDS" "-lgdi32;")
ENDIF("${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" GREATER 2.4)
