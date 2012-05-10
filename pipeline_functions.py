#!/usr/bin/python

"""
This is Mindboggle's NiPype pipeline!

Example usage:

from pipeline import create_mindboggle_flow
wf = create_mindboggle_flow()
wf.inputs.feature_extractor.curvature_file = '/projects/mindboggle/data/ManualSurfandVolLabels/subjects/KKI2009-14/surf/lh.curv'
wf.inputs.feature_extractor.surface_file = '/projects/mindboggle/data/ManualSurfandVolLabels/subjects/KKI2009-14/surf/lh.pial'
wf.run() # doctest: +SKIP


Authors:  Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

def extract_sulci(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    """Extract sulci

    extract_sulci
    """
    from glob import glob
    import subprocess as sp
    cmd = 'feature = extract/sulci/extract.py'
    cmd = ['python', cmd, '%s'%surface_file, '%s'%depth_map]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join(['extract.py failed', o, e]))
    #output_file = glob('file1.vtk').pop()
    #feature_files = glob('*.vtk')
    #return feature_files
    return sulci

def extract_fundi(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    """Extract fundi

    extract_fundi
    """
    from glob import glob
    import subprocess as sp
    cmd = 'feature = extract/fundi/extract.py'
    cmd = ['python', cmd, '%s'%surface_file, '%s'%depth_map]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join(['extract.py failed', o, e]))
    return fundi

def extract_pits(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    """Extract pits

    extract_pits
    """
    from glob import glob
    import subprocess as sp
    cmd = 'feature = extract/pits/extract.py'
    cmd = ['python', cmd, '%s'%surface_file, '%s'%depth_map]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join(['extract.py failed', o, e]))
    return pits

def extract_medial(surface_file, depth_map, mean_curvature_map, gauss_curvature_map):
    """Extract medial

    extract_medial
    """
    from glob import glob
    import subprocess as sp
    cmd = 'feature = extract/medial/extract.py'
    cmd = ['python', cmd, '%s'%surface_file, '%s'%depth_map]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join(['extract.py failed', o, e]))
    return medial

def register_to_template(subject_id):
    """Register surface to template

    
    """
    from glob import glob
    import subprocess as sp
    cmd = 'feature = register/surfaces_to_template.py'
    cmd = ['python', cmd, '%s%s'%(subjects_directory, subject_id),
           '%s'%template_directory, '%s'%template_name, '%s'%registration_append]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join([cmd + ' failed', o, e]))
    #return

def multiatlas_label_via_template(subjects_directory, subject_id, 
                                  output_directory, atlas_list):
    """Transform the labels from multiple atlases via the template
    
    """
    from glob import glob
    import subprocess as sp
    cmd = ['python', cmd, '%s%s'%(subjects_directory, subject_id),
           '%s'%output_directory, '%s'%atlas_list]
    proc = sp.Popen(cmd)
    o, e = proc.communicate()
    if proc.returncode > 0 :
        raise Exception('\n'.join([cmd + ' failed', o, e]))
    #return 

def measure_position(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_position
    if type(feature) is np.ndarray:
        measurement = measure_position(feature)
    return measurement

def measure_extent(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_extent
    if type(feature) is np.ndarray:
        measurement = measure_extent(feature)
    return measurement

def measure_depth(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_depth
    if type(feature) is np.ndarray:
        measurement = measure_(feature)
    return measurement

def measure_curvature(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_curvature
    if type(feature) is np.ndarray:
        measurement = measure_curvature(feature)
    return measurement

def measure_LaplaceBeltrami(feature):
    """Measure

    measure_()
    """
    from measure.py import measure_LaplaceBeltrami
    if type(feature) is np.ndarray:
        measurement = measure_LaplaceBeltrami(feature)
    return measurement

def write_features_to_database(feature):
    """Write to database

    write_to_database()
    """
    from write_to_database.py import features_to_database
    if type(feature) is np.ndarray:
        features_to_database(feature)
    success = 'True'
    return success

def write_measures_to_database(measurement):
    """Write to database

    write_to_database()
    """
    from write_to_database.py import measures_to_database
    if type(measurement) is np.ndarray:
        measures_to_database(measurement)
    success = 'True'
    return success


