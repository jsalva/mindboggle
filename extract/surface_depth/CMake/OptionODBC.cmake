OPTION (VTK_USE_ODBC "Build the ODBC database interface" OFF)
IF (VTK_USE_ODBC)
  FIND_PACKAGE( ODBC REQUIRED )
ENDIF (VTK_USE_ODBC)
