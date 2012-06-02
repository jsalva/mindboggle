#!/usr/bin/python

"""
Atlas-based functions for surface registration-based labeling:

1. Register to template
Register surface to template with FreeSurfer's mris_register.
Transform the labels from multiple atlases via a template 
(using FreeSurfer's mri_surf2surf).

2. Transform atlas labels
For each brain hemisphere (left and right) in a given subject, 
read in FreeSurfer *.annot files (multiple labelings) and output one VTK file 
of majority vote labels, representing a "maximum probability" labeling.
The main function is majority_vote() and calls relabel() and vote_labels().


Authors:  
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com
Forrest Bao  .  forrest.bao@gmail.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

use_linux_paths = 1

##############################################################################
#   Template-based, multi-atlas registration
##############################################################################

def register_to_template(hemi, sph_surface_file, template_transform,
                         template_name, templates_path):
    """
    Register surface to template with FreeSurfer's mris_register
    """
    from os import path, getcwd
    from nipype.interfaces.base import CommandLine
    from nipype import logging
    logger = logging.getLogger('interface')

    template_file = path.join(templates_path, hemi + '.' + template_name)
    output_file = hemi + '.' + template_transform
    cli = CommandLine(command='mris_register')
    cli.inputs.args = ' '.join(['-curv', sph_surface_file, 
                                template_file, output_file])
    logger.info(cli.cmdline)
    cli.run()
    
    return template_transform

if use_linux_paths:

    def transform_atlas_labels(hemi, subject_id, template_transform,
                               atlas_name, atlases_path, atlas_annot_name):
        """
        Transform the labels from multiple atlases via a template
        (using FreeSurfer's mri_surf2surf)
        """
        from os import system, path, getcwd

        source_annot_file = path.join(atlases_path, atlas_name, 'label',
                                      hemi + '.' + atlas_annot_name) 
        output_file = path.join(getcwd(), hemi + '.' + atlas_name + '_to_' + \
                                subject_id + '_' + atlas_annot_name)
        args = ['mri_surf2surf',
                '--hemi', hemi,
                '--srcsubject', atlas_name,
                '--trgsubject', subject_id,
                '--sval-annot', source_annot_file,
                '--tval', output_file,
                '--srcsurfreg', template_transform,
                '--trgsurfreg', template_transform]
        print(' '.join(args)); system(' '.join(args))
        return output_file

else:

    def transform_atlas_labels(hemi, subject_id, template_transform,
                               atlas_name, atlases_path, atlas_annot_name):
        """
        Transform the labels from a surface atlas via a template
        using FreeSurfer's mri_surf2surf (wrapped in NiPype)

        nipype.workflows.smri.freesurfer.utils.fs.SurfaceTransform
        wraps command **mri_surf2surf**:
        "Transform a surface file from one subject to another via a spherical registration.
        Both the source and target subject must reside in your Subjects Directory,
        and they must have been processed with recon-all, unless you are transforming
        to one of the icosahedron meshes."
        """
        from os import path, getcwd
        from nipype.interfaces.freesurfer import SurfaceTransform

        sxfm = SurfaceTransform()
        sxfm.inputs.hemi = hemi
        sxfm.inputs.target_subject = subject_id
        sxfm.inputs.source_subject = atlas_name

        # Source file
        sxfm.inputs.source_annot_file = path.join(atlases_path, 
                                        atlas_name, 'label',
                                        hemi + '.' + atlas_annot_name) 
        # Output annotation file
        output_file = path.join(getcwd(), hemi + '.' + atlas_name + '_to_' + \
                                subject_id + '_' + atlas_annot_name)
        sxfm.inputs.out_file = output_file

        # Arguments: strings within registered files
        args = ['--srcsurfreg', template_transform,
                '--trgsurfreg', template_transform]
        sxfm.inputs.args = ' '.join(args)

        sxfm.run()

        return output_file

##############################################################################
#   Multi-atlas labeling
##############################################################################

def relabel(label):
    """
    Return a pre-specified label assignment for a given input label.

    Parameters
    ==========
    label: integer label of a vertex

    Returns
    =======
    No variable. Direct return.

    Notes
    ===== 
    label combinations:

    2  = 2, 10, 23, 26
    3  = 3, 27  
    18 = 18, 19, 20
    
    Temporal (33) and frontal (32) poles, and bankstss (1) regions eliminated, 
    corresponding cortex absorbed by adjacent regions.

    Caudal (2), isthmus (10), posterior (23), and rostral anterior (26) cingulate 
    combined to form single cingulate region (2)
 
    Caudal (3) and rostral (27) middle frontal regions combined to form 
    single middle frontal region (3)
    
    Opercular (18), orbital (19), and triangular (20) inferior frontal regions 
    combined to form a single inferior frontal region (18)
    
    """
    
    if label == 10 or label == 23 or label == 26:
        return 2
    elif label == 27:
        return 3
    elif label == 19 or label == 20:
        return 18
    else:
        return label

def vote_labels(label_lists):
    """
    For each vertex, vote on the majority label.

    Parameters 
    ==========
    label_lists: list of lists of integers  (vertex labels assigned by each atlas)
    n_atlases: integer  (number of atlases / lists of labels)
    n_vertices: integer  (number of vertices / elements in each list)
        
    Returns
    =======
    labels_max: list of integers  (majority labels for vertices)
    label_counts: list of integers  (number of different labels for vertices)
    label_votes: list of integers  (number of votes for the majority labels) 

    Example of Counter:
    In [1]: from collections import Counter
    In [2]: X = [1,1,2,3,4,2,1,2,1,2,1,2]
    In [4]: Votes = Counter(X)
    In [7]: Votes
    Out[7]: Counter({1: 5, 2: 5, 3: 1, 4: 1})
    In [5]: Votes.most_common(1)
    Out[5]: [(1, 5)]
    In [6]: Votes.most_common(2)
    Out[6]: [(1, 5), (2, 5)]
    In [8]: len(Votes)
    Out[8]: 4

    """

    from collections import Counter
    
    print("Begin voting...")
    n_atlases = len(label_lists)  # number of atlases used to label subject
    n_vertices = len(label_lists[0])
    labels_max = [-1 for i in xrange(n_vertices)]  
    label_counts = [1 for i in xrange(n_vertices)]
    label_votes = [n_atlases for i in xrange(n_vertices)]

    for vertex in xrange(n_vertices):
        votes = Counter([label_lists[i][vertex] for i in xrange(n_atlases)])

        labels_max[vertex] = votes.most_common(1)[0][0]
        label_votes[vertex] = votes.most_common(1)[0][1]
        label_counts[vertex] = len(votes)

    print("Voting done.")

    return labels_max, label_votes, label_counts

def majority_vote_label(surface_file, annot_files):
    """
    Load a VTK surface and corresponding FreeSurfer annot files.
    Write majority vote labels, and label counts and votes as VTK files.

    Runs functions: relabel() and vote_labels()

    Parameters
    ==========
    surface_file: string  (name of VTK surface file)
    annot_files: list of strings  (names of FreeSurfer annot files)

    Returns 
    =======
    output_files: list of files containing majority vote labels,
                  number of different label counts, and
                  number of votes per majority label
    """

    import pyvtk
    from atlases import read_annot, relabel, vote_labels

    if_relabel = 1  # call relabel()

    # Load multiple label sets
    print("Load annotation files...")
    label_lists = []
    for annot_file in annot_files:
        labels, colortable, names = nb.freesurfer.read_annot(annot_file)
        if if_relabel:
            labels = map(relabel, labels)
        label_lists.append(labels)
    if if_relabel:
        print("Annotations loaded and labels reassigned.")
    else:
        print("Annotations loaded.")    
    
    # Vote on labels for each vertex
    labels_max, label_votes, label_counts = vote_labels(label_lists)

    # Check type:
    if type(surface_file) == str:
        pass
    elif type(surface_file) == list:
        surface_file = surface_file[0]
    else:
        import sys
        sys.error("Check format of " + surface_file)

    # Save files
    VTKReader = pyvtk.VtkData(surface_file)
    Vertices =  VTKReader.structure.points
    Faces =     VTKReader.structure.polygons

    file_stem = surface_file.strip('.vtk')
    maxlabel_file = file_stem + '.labels.max'
    labelcounts_file = file_stem + '.labelcounts'
    labelvotes_file = file_stem + '.labelvotes'

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
          pyvtk.PointData(pyvtk.Scalars(labels_max,\
                name='Max (majority labels)'))).\
          tofile(output_files[0], 'ascii')

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
          pyvtk.PointData(pyvtk.Scalars(label_counts,\
                name='Counts (number of different labels)'))).\
          tofile(output_files[1], 'ascii')

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
          pyvtk.PointData(pyvtk.Scalars(label_votes,\
                name='Votes (number of votes for majority labels)'))).\
          tofile(output_files[2], 'ascii')

    return maxlabel_file, labelcounts_file, labelvotes_file

def label_volume(output_file, mask_file, input_file):
    """
    Fill (e.g., gray matter) volume with surface labels using ANTS
    (ImageMath's PropagateLabelsThroughMask)

    Brian avants: 
    The initial box labels are propagated through the gray matter with
    gm-probability dependent speed. It uses the fast marching algorithm.
    You can control how tightly the propagation follows the gray matter
    label by adjusting the speed image -- e.g. a binary speed image
    will constrain the propagated label only to the gm.

    """
    from os import path, getcwd
    from nipype.interfaces.base import CommandLine
    from nipype import logging
    logger = logging.getLogger('interface')

    print("Fill gray matter volume with surface labels using ANTS...")

    output_file = path.join(getcwd(), output_file)

    args = ['3',
            output_file,
            'PropagateLabelsThroughMask',
            mask_file,
            input_file]

    cli = CommandLine(command='ImageMath')
    cli.inputs.args = ' '.join(args)
    logger.info(cli.cmdline)
    cli.run()

    return output_file

"""
NB: To fill gray matter with labels using FreeSurfer,
    we would need to save the labels as an .annot file 
    in the subject directory (annot_name).

def label_volume_FS(subject_id, annot_name, output_name):
    ""
    Propagate surface labels through a gray matter volume 
    using FreeSurfer's mri_aparc2aseg
    ""
    from os import path, getcwd
    from nipype.interfaces.base import CommandLine
    from nipype import logging
    logger = logging.getLogger('interface')

    print("Fill gray matter volume with surface labels using FreeSurfer...")

    output_file = path.join(getcwd(), output_name)

    args = ['--s', subject_id,
            '--annot', annot_name,
            '--o', output_file]

    cli = CommandLine(command='mri_aparc2aseg')
    cli.inputs.args = ' '.join(args)
    logger.info(cli.cmdline)
    cli.run()

    return output_file
"""
