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
The main function is majority_vote() and calls vote_labels().


Authors:
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com
Forrest Bao  .  forrest.bao@gmail.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

##############################################################################
#   Template-based, multi-atlas registration
##############################################################################

def register_template(hemi, sphere_file, transform,
                      templates_path, template):
    """
    Register surface to template with FreeSurfer's mris_register
    """
    import os
    from nipype.interfaces.base import CommandLine

    template_file = os.path.join(templates_path, hemi + '.' + template)
    output_file = hemi + '.' + transform
    cli = CommandLine(command='mris_register')
    cli.inputs.args = ' '.join(['-curv', sphere_file,
                                template_file, output_file])
    cli.cmdline
    cli.run()

    return transform

def transform_atlas_labels(hemi, subject, transform,
                           subjects_path, atlas, atlas_string):
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

    import os
    from nipype.interfaces.freesurfer import SurfaceTransform

    sxfm = SurfaceTransform()
    sxfm.inputs.hemi = hemi
    sxfm.inputs.target_subject = subject
    sxfm.inputs.source_subject = atlas

    # Source file
    sxfm.inputs.source_annot_file = os.path.join(subjects_path,
                                                 atlas, 'label',
                            hemi + '.' + atlas_string + '.annot')
    # Output annotation file
    output_file = os.path.join(os.getcwd(), hemi + '.' + atlas + '.' + \
                               atlas_string + '_to_' + subject + '.annot')
    sxfm.inputs.out_file = output_file

    # Arguments: strings within registered files
    args = ['--srcsurfreg', transform,
            '--trgsurfreg', transform]
    sxfm.inputs.args = ' '.join(args)

    sxfm.run()

    return output_file

##############################################################################
#   Multi-atlas labeling
##############################################################################

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

    consensus_vertices = []
    for vertex in xrange(n_vertices):
        votes = Counter([label_lists[i][vertex] for i in xrange(n_atlases)])

        labels_max[vertex] = votes.most_common(1)[0][0]
        label_votes[vertex] = votes.most_common(1)[0][1]
        label_counts[vertex] = len(votes)
        if len(votes) == n_atlases:
            consensus_vertices.append(vertex)

    print("Voting done.")

    return labels_max, label_votes, label_counts, consensus_vertices

def majority_vote_label(surface_file, annot_files):
    """
    Load a VTK surface and corresponding FreeSurfer annot files.
    Write majority vote labels, and label counts and votes as VTK files.

    Runs function: vote_labels()

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

    import os
    import nibabel as nb
    import pyvtk
    from multiatlas_labeling import vote_labels

    # Load multiple label sets
    print("Load annotation files...")
    label_lists = []
    for annot_file in annot_files:
        labels, colortable, names = nb.freesurfer.read_annot(annot_file)
        label_lists.append(labels)
    print("Annotations loaded.")

    # Vote on labels for each vertex
    labels_max, label_votes, label_counts,\
    consensus_vertices = vote_labels(label_lists)

    # Save files
    VTKReader = pyvtk.VtkData(surface_file)
    Vertices =  VTKReader.structure.points
    Faces =     VTKReader.structure.polygons

    output_stem = os.path.join(os.getcwd(), os.path.basename(surface_file.strip('.vtk')))
    maxlabel_file = output_stem + '.labels.max.vtk'
    labelcounts_file = output_stem + '.labelcounts.vtk'
    labelvotes_file = output_stem + '.labelvotes.vtk'

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
                  pyvtk.PointData(pyvtk.Scalars(labels_max,\
                                  name='Max (majority labels)'))).\
          tofile(maxlabel_file, 'ascii')

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
                  pyvtk.PointData(pyvtk.Scalars(label_counts,\
                                  name='Counts (number of different labels)'))).\
          tofile(labelcounts_file, 'ascii')

    pyvtk.VtkData(pyvtk.PolyData(points=Vertices, polygons=Faces),\
                  pyvtk.PointData(pyvtk.Scalars(label_votes,\
                                  name='Votes (number of votes for majority labels)'))).\
          tofile(labelvotes_file, 'ascii')

    return maxlabel_file, labelcounts_file, labelvotes_file, consensus_vertices
