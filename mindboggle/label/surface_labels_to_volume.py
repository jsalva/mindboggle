#!/usr/bin/python

"""
Convert surface mesh labels to volume labels.

1. Write surface mesh labels FreeSurfer's .label file.
2. Use FreeSurfer's mris_label2annot and mri_aparc2aseg
   to convert these label files to .annot files and fill
   a gray matter volume with the labels.


Author:  Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

def write_label_file(hemi, surface_file, label_number, label_name):
    """
    Save a FreeSurfer .label file for a given label from the vertices
    of a labeled VTK surface mesh.

    """

    from os import path, getcwd, error
    import numpy as np
    import vtk

    scalar_name = "Max_(majority_labels)"

    # Check type:
    if type(surface_file) == str:
        pass
    elif type(surface_file) == list:
        surface_file = surface_file[0]
    else:
        error("Check format of " + surface_file)

    # Check type:
    if type(label_number) == int:
        pass
    elif type(label_number) == str:
        label_number = int(label_number)
    else:
        error("Check format of " + label_number)

    # Load surface
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(surface_file)
    reader.ReadAllScalarsOn()
    reader.Update()
    data = reader.GetOutput()
    d = data.GetPointData()
    labels = d.GetArray(scalar_name)

    # Write vertex index, coordinates, and 0
    count = 0
    npoints = data.GetNumberOfPoints()
    L = np.zeros((npoints,5))
    for i in range(npoints):
        label = labels.GetValue(i)
        if label == label_number:
            L[count,0] = i
            L[count,1:4] = data.GetPoint(i)
            count += 1

    # Save the label file
    if count > 0:
        #label_file = path.join(getcwd(), hemi + '.ctx-' + hemi + '-' +\
        #label_file = path.join(getcwd(), 'ctx-' + hemi + '-' +\
        label_file = path.join(getcwd(), \
                               hemi + '.' + label_name + '.label')
        f = open(label_file, 'w')
        f.writelines('#!ascii label\n' + str(count) + '\n')
        for i in range(npoints):
            if any(L[i,:]):
                printline = '{0} {1} {2} {3} 0\n'.format(
                             np.int(L[i,0]), L[i,1], L[i,2], L[i,3])
                f.writelines(printline)
            else:
                break
        f.close()
        return label_file

def label_to_annot_file(hemi, subjects_path, subject, label_files, colortable):
    """
    Convert FreeSurfer .label files as a FreeSurfer .annot file
    using FreeSurfer's mris_label2annot.

    """

    from os import path
    from nipype.interfaces.base import CommandLine
    from nipype import logging
    logger = logging.getLogger('interface')

    label_files = [f for f in label_files if f!=None]
    if label_files:
        annot_name = 'labels.max'
        annot_file = hemi + '.' + annot_name + '.annot'
        if path.exists(path.join(subjects_path, subject, 'label', annot_file)):
            cli = CommandLine(command='rm')
            cli.inputs.args = path.join(subjects_path, subject, \
                                        'label', annot_file)
            logger.info(cli.cmdline)
            cli.run()
        cli = CommandLine(command='mris_label2annot')
        cli.inputs.args = ' '.join(['--h', hemi, '--s', subject, \
                                    '--l', ' --l '.join(label_files), \
                                    '--ctab', colortable, \
                                    '--a', annot_name])
        logger.info(cli.cmdline)
        cli.run()
        return annot_name, annot_file

def fill_label_volume(subject, annot_name):
    """
    Propagate surface labels through a gray matter volume
    using FreeSurfer's mri_aparc2aseg

    """

    from os import path, getcwd
    from nipype.interfaces.base import CommandLine
    from nipype import logging
    logger = logging.getLogger('interface')

    print("Fill gray matter volume with surface labels using FreeSurfer...")

    output_file = path.join(getcwd(), annot_name + '.nii.gz')

    args = ['--s', subject,
            '--annot', annot_name,
            '--o', output_file]

    cli = CommandLine(command='mri_aparc2aseg')
    cli.inputs.args = ' '.join(args)
    logger.info(cli.cmdline)
    cli.run()

    return output_file
