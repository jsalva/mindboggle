#!/usr/bin/python

"""
This is Mindboggle's NiPype pipeline!

Example usage:

 # doctest: +SKIP


Authors:  Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import os
from nipype.pipeline.engine import Workflow as workflow
from nipype.pipeline.engine import Node as node
from nipype.pipeline.engine import MapNode as mapnode
from nipype.interfaces.utility import Function as fn
from nipype.interfaces.utility import IdentityInterface as identity
from nipype.interfaces.io import DataGrabber as datain
from nipype.interfaces.io import DataSink as dataout

from atlases import register_to_template, transform_atlas_labels,\
                    majority_vote_label
from label_volume import polydata2volume, label_volume, measure_overlap
from features import *

# Options
if_linux_paths = 0
if_freesurfer = 1
if_label_volume = 1
if_evaluate_labels = 1

# Paths
subjects_list = ['KKI2009-11'] #, 'KKI2009-14']
if if_linux_paths:
    subjects_path = '/usr/local/freesurfer/subjects'
else:
    subjects_path = '/Applications/freesurfer/subjects'
templates_path = '/projects/mindboggle/data/templates_freesurfer'
atlases_path = subjects_path

# File settings
hemis = ['lh','rh']
surface_types = ['pial'] #,'inflated']
template_id = 'KKI'
template_name = template_id + '_2.tif'
template_transform = 'sphere_to_' + template_id + '_template.reg'
atlas_name = 'aparcNMMjt'
labels_file = 'labels.txt' # Table with unique, non-zero labels

# Output directory
results_path = '/projects/mindboggle/results/'
working_path = results_path + 'workingdir'
if not os.path.isdir(results_path):
    os.makedirs(results_path)
if not os.path.isdir(working_path):
    os.makedirs(working_path)

# Commands
mbpath = '/projects/mindboggle/mindboggle/'
depth_command = mbpath+'measure/surface_measures/bin/travel_depth/TravelDepthMain'
curvature_command = mbpath+'measure/surface_measures/bin/curvature/CurvatureMain'
extract_fundi_command = mbpath+'extract/fundi/vtk_extract.py'
if if_linux_paths:
    imagemath = '/usr/local/bin/ImageMath'
else:
    #imagemath = '/usr/bin/ants/ImageMath'
    imagemath = '/Users/arno/Software/ANTS_1.9/bin/ImageMath'

# List of atlas subjects
atlas_list_file = os.path.join(atlases_path, 'MMRR.txt')
f = open(atlas_list_file)
atlas_list_lines = f.readlines()
atlas_names = [a.strip("\n") for a in atlas_list_lines if a.strip("\n")]

##############################################################################
#
#   Mindboggle workflow combining:
#   * Multi-atlas registration-based labeling workflow
#   * Feature-based labeling and shape analysis workflow
#   * Analytics
#
##############################################################################
mbflow = workflow(name='Mindboggle_workflow')
mbflow.base_dir = working_path

##############################################################################
#   Inputs and outputs
##############################################################################

# Iterate inputs over subjects, hemispheres, surface types
infosource = node(name = 'Inputs',
                  interface = identity(fields=['subject_id',
                                               'hemi',
                                               'surface_type',
                                               'volume_mask']))
infosource.iterables = ([('subject_id', subjects_list),
                         ('hemi', hemis)])

# Location and structure of the surface inputs
surfsource = node(name = 'Surfaces',
                  interface = datain(infields=['subject_id',
                                               'hemi'],
                                     outfields=['surface_files',
                                                'inf_surface_files',
                                                'sph_surface_files']))
surfsource.inputs.base_directory = subjects_path
surfsource.inputs.template = '%s/surf/%s.%s'
surfsource.inputs.template_args['surface_files'] = [['subject_id',
                                                     'hemi',
                                                     'pial']]
surfsource.inputs.template_args['inf_surface_files'] = [['subject_id',
                                                         'hemi',
                                                         'inflated']]
surfsource.inputs.template_args['sph_surface_files'] = [['subject_id',
                                                         'hemi',
                                                         'sphere']]
mbflow.connect([(infosource, surfsource,
                 [('subject_id','subject_id'),
                  ('hemi','hemi')])])

# Location and structure of the volume inputs
if if_label_volume:
    volsource = node(name = 'Volume',
                     interface = datain(infields=['subject_id',
                                                  'hemi'],
                                        outfields=['volume_file']))
    volsource.inputs.base_directory = subjects_path
    volsource.inputs.template = '%s/mri/%s.%s'
    volsource.inputs.template_args['volume_file'] = [['subject_id',
                                                      'hemi',
                                                      'ribbon.mgz']]
    mbflow.connect([(infosource, volsource,
                     [('subject_id','subject_id'),
                      ('hemi','hemi')])])

# Location and structure of the volume inputs
if if_evaluate_labels:
    atlassource = node(name = 'Atlas',
                       interface = datain(infields=['subject_id'],
                                          outfields=['atlas_file']))
    atlassource.inputs.base_directory = subjects_path
    atlassource.inputs.template = '%s/labels/%s.nii.gz'
    atlassource.inputs.template_args['atlas_file'] = [['subject_id',
                                                      'atlas_name']]
    mbflow.connect([(infosource, atlassource,
                     [('subject_id','subject_id')])])

# Outputs
datasink = node(dataout(), name = 'Results')
datasink.inputs.base_directory = results_path
datasink.inputs.container = 'output'

##############################################################################
#   Surface conversion to VTK
##############################################################################

# Convert FreeSurfer surfaces to VTK format and volumes to NIfTI format
if if_freesurfer:

    import nipype.interfaces.freesurfer as fs

    convertsurf = mapnode(name = 'Convert_surface',
                             iterfield = ['in_file'],
                             interface = fs.MRIsConvert(out_datatype='vtk'))
    mbflow.connect([(surfsource, convertsurf,
                     [('surface_files','in_file')])])

    convertvol = mapnode(name = 'Convert_volume',
                         iterfield = ['in_file'],
                         interface = fs.MRIConvert(out_type='niigz'))
    mbflow.connect([(volsource, convertvol,
                     [('volume_file','in_file')])])

##############################################################################
#
#   Multi-atlas registration-based labeling workflow
#
##############################################################################
atlasflow = workflow(name='Atlas_workflow')

##############################################################################
#   Multi-atlas registration
##############################################################################

# Template registration
register = node(name = 'Register_to_template',
                interface = fn(function = register_to_template,
                               input_names = ['hemi',
                                              'sph_surface_file',
                                              'template_name',
                                              'templates_path',
                                              'template_transform'],
                               output_names = ['template_transform']))
register.inputs.template_name = template_name
register.inputs.templates_path = templates_path
register.inputs.template_transform = template_transform

atlasflow.add_nodes([register])
mbflow.connect([(infosource, atlasflow,
                 [('hemi', 'Register_to_template.hemi')]),
                (surfsource, atlasflow,
                 [('sph_surface_files',
                   'Register_to_template.sph_surface_file')])])

# Atlas registration
transform = mapnode(name = 'Transform_atlas_labels',
                    iterfield = ['atlas_name'],
                    interface = fn(function = transform_atlas_labels,
                                   input_names = ['hemi',
                                                  'subject_id',
                                                  'template_transform',
                                                  'atlas_name',
                                                  'atlases_path',
                                                  'atlas_annot_name'],
                                   output_names = ['output_file']))
transform.inputs.atlas_name = atlas_names
transform.inputs.atlases_path = atlases_path
transform.inputs.atlas_annot_name = atlas_name + '.annot'

atlasflow.add_nodes([transform])
mbflow.connect([(infosource, atlasflow,
                 [('hemi', 'Transform_atlas_labels.hemi'),
                  ('subject_id', 'Transform_atlas_labels.subject_id')])])
atlasflow.connect([(register, transform, 
                    [('template_transform', 'template_transform')])])

# Majority vote labeling
vote = node(name='Majority_vote',
            interface = fn(function = majority_vote_label,
                           input_names = ['surface_file',
                                          'annot_files'],
                           output_names = ['maxlabel_file',
                                           'labelcounts_file',
                                           'labelvotes_file']))
atlasflow.add_nodes([vote])

if if_freesurfer:
    mbflow.connect([(convertsurf, atlasflow,
                     [('converted', 'Majority_vote.surface_file')])])
else:
    mbflow.connect([(surfsource, atlasflow,
                     [('surface_files', 'Majority_vote.surface_file')])])
atlasflow.connect([(transform, vote,
                    [('output_file', 'annot_files')])])
mbflow.connect([(atlasflow, datasink,
                 [('Majority_vote.maxlabel_file', 'labels.@max'),
                  ('Majority_vote.labelcounts_file', 'labels.@counts'),
                  ('Majority_vote.labelvotes_file', 'labels.@votes')])])

##############################################################################
#   Label propagation through a mask
##############################################################################

# Filling a volume (e.g., gray matter) mask with majority vote labels (ANTS)
if if_label_volume:

    # Put surface vertices in a volume
    surf2vol = node(name='Surface_to_volume',
                    interface = fn(function = polydata2volume,
                                   input_names = ['surface_file',
                                                  'volume_file',
                                                  'output_file',
                                                  'if_freesurfer'],
                                   output_names = ['output_file']))
    surf2vol.inputs.if_freesurfer = if_freesurfer
    surf2vol.inputs.output_file = 'labels.surf.nii.gz'

    atlasflow.add_nodes([surf2vol])
    atlasflow.connect([(vote, surf2vol,
                        [('maxlabel_file','surface_file')])])

    if if_freesurfer:
        mbflow.connect([(convertvol, atlasflow,
                         [('out_file','Surface_to_volume.volume_file')])])
    else:
        mbflow.connect([(volsource, atlasflow,
                         [('volume_file','Surface_to_volume.volume_file')])])

    # Fill volume mask with surface vertex labels
    fill_maxlabels = node(name='Fill_volume_maxlabels',
                          interface = fn(function = label_volume,
                                         input_names = ['command',
                                                        'input_file',
                                                        'mask_file',
                                                        'output_file'],
                                         output_names = ['output_file']))
    fill_maxlabels.inputs.command = imagemath
    fill_maxlabels.inputs.output_file = 'labels.max.nii.gz'

    atlasflow.add_nodes([fill_maxlabels])

    atlasflow.connect([(surf2vol, fill_maxlabels,
                        [('output_file', 'input_file')])])
    if if_freesurfer:
        mbflow.connect([(convertvol, atlasflow,
                         [('out_file','Fill_volume_maxlabels.mask_file')])])
        """
        NB: For volume label propagation using FreeSurfer,
            we would need to save the appropriate .annot file.

        maxlabel_volume_FS = node(name='Maxlabel_volume_FS',
                                  interface = fn(function = label_volume_annot,
                                                 input_names = ['subject_id',
                                                                'annot_name',
                                                                'output_name'],
                                                 output_names = ['output_file']))
        """
    else:
        mbflow.connect([(volsource, atlasflow,
                         [('volume_file','Fill_volume_maxlabels.mask_file')])])
    mbflow.connect([(atlasflow, datasink,
                     [('Fill_volume_maxlabels.output_file', 'labels.@maxvolume')])])

    ##########################################################################
    #   Evaluation of the volume maxlabels
    ##########################################################################

    # Evaluate volume labels
    eval_maxlabels = node(name='Evaluate_volume_maxlabels',
                          interface = fn(function = measure_overlap,
                                         input_names = ['labels_file',
                                                        'input_file',
                                                        'atlas_file',
                                                        'output_table'],
                                         output_names = ['output_table',
                                                         'avg_dice',
                                                         'avg_jacc']))
    eval_maxlabels.inputs.labels_file = labels_file
    eval_maxlabels.inputs.atlas_file = atlas_name + '.nii.gz'
    eval_maxlabels.inputs.output_table = 'labels.max.eval.csv'

    atlasflow.add_nodes([eval_maxlabels])

    atlasflow.connect([(fill_maxlabels, eval_maxlabels,
                        [('output_file', 'input_file')])])
    mbflow.connect([(atlasflow, datasink,
                     [('Evaluate_volume_maxlabels.output_table', 'labels.@eval')])])

##############################################################################
#
#   Feature-based labeling and shape analysis workflow
#
##############################################################################

featureflow = workflow(name='Feature_workflow')

##############################################################################
#   Surface calculations
##############################################################################

# Measure surface depth and curvature nodes
depth = node(name='Compute_depth',
             interface = fn(function = compute_depth,
                            input_names = ['command',
                                           'surface_file'],
                            output_names = ['depth_file']))
depth.inputs.command = depth_command

curvature = node(name='Compute_curvature',
                 interface = fn(function = compute_curvature,
                                input_names = ['command',
                                               'surface_file'],
                                output_names = ['mean_curvature_file',
                                                'gauss_curvature_file',
                                                'max_curvature_file',
                                                'min_curvature_file']))
curvature.inputs.command = curvature_command

# Add and connect nodes
featureflow.add_nodes([depth, curvature])

if if_freesurfer:
    mbflow.connect([(convertsurf, featureflow,
                   [('converted', 'Compute_depth.surface_file')])])
    mbflow.connect([(convertsurf, featureflow,
                   [('converted', 'Compute_curvature.surface_file')])])
else:
    # Connect input to surface depth and curvature nodes
    mbflow.connect([(atlasflow, featureflow, 
                     [('Surfaces.surface_files',
                       'Compute_depth.surface_file')])])
    mbflow.connect([(atlasflow, featureflow, 
                     [('Surfaces.surface_files',
                       'Compute_curvature.surface_file')])])

# Save
mbflow.connect([(featureflow, datasink,
                 [('Compute_depth.depth_file', 'surfaces.@depth')])])
mbflow.connect([(featureflow, datasink,
                 [('Compute_curvature.mean_curvature_file', 
                   'surfaces.@mean_curvature'),
                  ('Compute_curvature.gauss_curvature_file', 
                   'surfaces.@gauss_curvature'),
                  ('Compute_curvature.max_curvature_file', 
                   'surfaces.@max_curvature'),
                  ('Compute_curvature.min_curvature_file', 
                   'surfaces.@min_curvature')])])

##############################################################################
#   Feature extraction
##############################################################################
"""
# Extract features
fundi = node(name='Extract_fundi',
             interface = fn(function = extract_fundi,
                            input_names = ['command',
                                           'depth_file'],
                            output_names = ['fundi']))
fundi.inputs.command = extract_fundi_command
"""
"""
sulci = node(name='Extract_sulci',
                interface = fn(
                                 function = extract_sulci,
                                 input_names = ['depth_file',
                                                'mean_curv_file',
                                                'gauss_curv_file'],
                                 output_names = ['sulci']))

medial = node(name='Extract_medial',
                 interface = fn(
                                  function = extract_midaxis,
                                  input_names = ['depth_file',
                                                 'mean_curv_file',
                                                 'gauss_curv_file'],
                                  output_names = ['midaxis']))

# Connect surface depth to feature extraction nodes
featureflow.connect([(depth, fundi,
               [('depth_file', 'depth_file')])])
featureflow.connect([(fundi, datasink, 
               [('fundi', 'fundi')])])

featureflow.connect([(surfaces, sulcus_extraction, 
               [('depth_file', 'depth_file'),
                ('mean_curv_file', 'mean_curv_file'),
                ('gauss_curv_file', 'gauss_curv_file')])])
featureflow.connect([(surfaces, midaxis_extraction, 
               [('depth_file', 'depth_file'),
                ('mean_curv_file', 'mean_curv_file'),
                ('gauss_curv_file', 'gauss_curv_file')])])
"""
##############################################################################
#   Label propagation
##############################################################################
"""
# Label propagation node
propagate = node(name='Propagate_labels',
                    interface = fn(
                                     function = propagate_labels,
                                     input_names=['labels', 'fundi'],
                                     output_names=['labels']))

# Volume label propagation node
propagate_volume = node(name='Propagate_volume_labels',
                           interface = fn(
                                            function = propagate_volume_labels,
                                            input_names = ['labels'],
                                            output_names = ['volume_labels']))

# Labeled surface patch and volume extraction nodes
extract_patch = node(name='Extract_patch',
                        interface = fn(
                                         function = extract_patches,
                                         input_names=['labels'],
                                         output_names=['patches']))

extract_patch = node(name='Extract_region',
                        interface = fn(
                                         function = extract_patches,
                                         input_names=['labels'],
                                         output_names=['patches']))

# Connect registration and extraction to label propagation nodes
featureflow.connect([(transform, propagate, [('labels','labels')]),
                     (extract_fundi, propagate, [('fundi','fundi')])])

# Connect label propagation to labeled surface patch and volume extraction nodes
featureflow.connect([(propagate, propagate_volume, [('labels', 'labels')])])

featureflow.connect([(propagate_volume, extract_region, [('labels', 'labels')])])
featureflow.connect([(propagate, extract_patch, [('labels', 'labels')])])

##############################################################################
#   Feature segmentation / identification
##############################################################################

# Feature segmentation nodes
segment_sulci = node(name='Segment_sulci',
                        interface = fn(
                                         function = segment_sulci,
                                         input_names=['sulci','labels'],
                                         output_names=['segmented_sulci']))

segment_fundi = node(name='Segment_fundi',
                        interface = fn(
                                         function = segment_fundi,
                                         input_names=['fundi','labels'],
                                         output_names=['segmented_fundi']))

segment_medial = node(name='Segment_medial',
                         interface = fn(
                                          function = segment_medial,
                                          input_names=['medial','labels'],
                                          output_names=['segmented_medial']))

# Connect feature and feature segmentation nodes
featureflow.connect([(extract_sulci, segment_sulci, [('sulci','sulci')]),
              (extract_fundi, segment_fundi, [('fundi','fundi')]),
              (extract_medial, segment_medial, [('medial','medial')])])

# Connect label propagation and feature segmentation nodes
featureflow.connect([(propagate, segment_sulci, [('labels','labels')]),
              (propagate, segment_fundi, [('labels','labels')]),
              (segment_sulci, segment_medial, [('segmented_sulci','labels')])])
              
##############################################################################
#   Shape measurement
##############################################################################

# Shape measurement nodes
positions = node(interface = fn(input_names = ['segmented_sulci',
                                                 'segmented_fundi',
                                                 'segmented_midaxis', 
                                                 'pits', 
                                                 'patches', 
                                                 'regions'],
                                  output_names=['positions_sulci', 
                                                'positions_fundi',
                                                'positions_midaxis', 
                                                'positions_pits', 
                                                'positions_patches', 
                                                'positions_regions'],
                                  function = measure_positions),
                    name='Measure_positions')

extents = node(interface = fn(input_names = ['segmented_sulci',
                                               'segmented_fundi',
                                               'segmented_midaxis', 
                                               'pits', 
                                               'patches', 
                                               'regions'],
                                output_names=['extents_sulci', 
                                              'extents_fundi',
                                              'extents_midaxis', 
                                              'extents_pits',
                                              'extents_patches', 
                                              'extents_regions'],
                                function = measure_extents),
                    name='Measure_extents')

curvatures = node(interface = fn(input_names = ['segmented_sulci',
                                                  'segmented_fundi',
                                                  'segmented_midaxis', 
                                                  'pits', 
                                                  'patches', 
                                                  'regions'],
                                   output_names=['curvatures_sulci', 
                                                 'curvatures_fundi',
                                                 'curvatures_midaxis', 
                                                 'curvatures_pits',
                                                 'curvatures_patches', 
                                                 'curvatures_regions'],
                                   function = measure_curvatures),
                    name='Measure_curvatures')

depths = node(interface = fn(input_names = ['segmented_sulci',
                                              'segmented_fundi',
                                              'segmented_midaxis',
                                              'pits', 
                                              'patches', 
                                              'regions'],
                               output_names=['depths_sulci', 
                                             'depths_fundi',
                                             'depths_midaxis',
                                             'depths_pits',
                                             'depths_patches', 
                                             'depths_regions'],
                               function = measure_depths),
                 name='Measure_depths')

spectra = node(interface = fn(input_names = ['segmented_sulci',
                                               'segmented_fundi',
                                               'segmented_midaxis',
                                               'pits', 
                                               'patches', 
                                               'regions'],
                                output_names=['spectra_sulci',
                                              'spectra_fundi',
                                              'spectra_midaxis',
                                              'spectra_pits',
                                              'spectra_patches', 
                                              'spectra_regions'],
                                function = measure_spectra),
                  name='Measure_spectra')

# Connect labeled surface patches and volumes to shape measurement nodes
featureflow.connect([(patch_extraction,  positions, [('patches', 'patches')])])
featureflow.connect([(region_extraction, positions, [('regions', 'regions')])])
featureflow.connect([(patch_extraction,  extents, [('patches', 'patches')])])
featureflow.connect([(region_extraction, extents, [('regions', 'regions')])])
featureflow.connect([(patch_extraction,  depths, [('patches', 'patches')])])
featureflow.connect([(region_extraction, depths, [('regions', 'regions')])])
featureflow.connect([(patch_extraction,  curvatures, [('patches', 'patches')])])
featureflow.connect([(region_extraction, curvatures, [('regions', 'regions')])])
featureflow.connect([(patch_extraction,  spectra, [('patches', 'patches')])])
featureflow.connect([(region_extraction, spectra, [('regions', 'regions')])])

# Connect feature to shape measurement nodes
featureflow.connect([(sulcus_segmentation, positions, [('segmented_sulci', 'segmented_sulci')])])
featureflow.connect([(fundus_segmentation, positions, [('segmented_fundi', 'segmented_fundi')])])
featureflow.connect([(pit_extraction, positions, [('pits', 'pits')])])
featureflow.connect([(midaxis_segmentation, positions, [('segmented_midaxis', 'segmented_midaxis')])])

featureflow.connect([(sulcus_segmentation, extents, [('segmented_sulci', 'segmented_sulci')])])
featureflow.connect([(fundus_segmentation, extents, [('segmented_fundi', 'segmented_fundi')])])
featureflow.connect([(midaxis_segmentation, extents, [('segmented_midaxis', 'segmented_midaxis')])])

featureflow.connect([(sulcus_segmentation, curvatures, [('segmented_sulci', 'segmented_sulci')])])
featureflow.connect([(fundus_segmentation, curvatures, [('segmented_fundi', 'segmented_fundi')])])
featureflow.connect([(pit_extraction, curvatures, [('pits', 'pits')])])
featureflow.connect([(midaxis_segmentation, curvatures, [('segmented_midaxis', 'segmented_midaxis')])])

featureflow.connect([(sulcus_segmentation, depths, [('segmented_sulci', 'segmented_sulci')])])
featureflow.connect([(fundus_segmentation, depths, [('segmented_fundi', 'segmented_fundi')])])
featureflow.connect([(pit_extraction, depths, [('pits', 'pits')])])
featureflow.connect([(midaxis_segmentation, depths, [('segmented_midaxis', 'segmented_midaxis')])])

featureflow.connect([(sulcus_segmentation, spectra, [('segmented_sulci', 'segmented_sulci')])])
featureflow.connect([(fundus_segmentation, spectra, [('segmented_fundi', 'segmented_fundi')])])
featureflow.connect([(midaxis_segmentation, spectra, [('segmented_midaxis', 'segmented_midaxis')])])

##############################################################################
#    Store surface maps, features, and measures in database
##############################################################################

# Database nodes
maps_database = node(interface = fn(input_names = ['depth_file',
                                                     'mean_curv_file',
                                                     'gauss_curv_file'],
                                      output_names=['success'],
                                      function = write_surfaces_to_database),
                        name='Write_surfaces_to_database')

features_database = node(interface = fn(input_names = ['segmented_sulci',
                                                         'segmented_fundi',
                                                         'pits',
                                                         'segmented_midaxis'],
                                          output_names=['success'],
                                          function = write_features_to_database),
                            name='Write_features_to_database')

measures_database = node(interface = fn(input_names = ['positions_sulci',
                                                         'positions_fundi',
                                                         'positions_pits',
                                                         'positions_midaxis',
                                                         'positions_patches',
                                                         'positions_regions',
                                                         'extents_sulci',
                                                         'extents_fundi',
                                                         'extents_midaxis',
                                                         'extents_patches',
                                                         'extents_regions',
                                                         'curvatures_sulci',
                                                         'curvatures_fundi',
                                                         'curvatures_pits',
                                                         'curvatures_midaxis',
                                                         'curvatures_patches',
                                                         'curvatures_regions',
                                                         'depths_sulci',
                                                         'depths_fundi',
                                                         'depths_pits',
                                                         'depths_midaxis',
                                                         'depths_patches',
                                                         'depths_regions',
                                                         'spectra_sulci',
                                                         'spectra_fundi',
                                                         'spectra_midaxis',
                                                         'spectra_patches',
                                                         'spectra_regions'],
                                          output_names=['measures'],
                                          function = write_measures_to_database),
                            name='Write_measures_to_database')

measures_table = node(interface = fn(input_names = ['measures'],
                                       output_names=['success'],
                                       function = write_measures_to_table),
                         name='Write_measures_to_table')

# Connect surface maps to database nodes
featureflow.connect([(surfaces, maps_database, [('depth_file','depth_file'),
                                ('mean_curv_file','mean_curv_file'),
                                ('gauss_curv_file','gauss_curv_file')])])

# Connect feature to database nodes
featureflow.connect([(sulcus_segmentation, features_database, [('segmented_sulci', 'segmented_sulci')]),
              (fundus_segmentation, features_database, [('segmented_fundi', 'segmented_fundi')]),
              (pit_extraction, features_database, [('pits', 'pits')]),
              (midaxis_segmentation, features_database, 
                          [('segmented_midaxis', 'segmented_midaxis')])])

# Connect feature measures to database nodes
featureflow.connect([(positions, measures_database, [('positions_sulci', 'positions_sulci'),
                                              ('positions_fundi', 'positions_fundi'),
                                              ('positions_pits', 'positions_pits'),
                                              ('positions_midaxis', 'positions_midaxis')]),
              (extents, measures_database, [('extents_sulci', 'extents_sulci'),
                                            ('extents_fundi', 'extents_fundi'),
                                            ('extents_midaxis', 'extents_midaxis')]),
              (curvatures, measures_database, [('curvatures_sulci', 'curvatures_sulci'),
                                               ('curvatures_fundi', 'curvatures_fundi'),
                                               ('curvatures_pits', 'curvatures_pits'),
                                               ('curvatures_midaxis', 'curvatures_midaxis')]),
              (depths, measures_database, [('depths_sulci', 'depths_sulci'),
                                           ('depths_fundi', 'depths_fundi'),
                                           ('depths_pits', 'depths_pits'),
                                           ('depths_midaxis', 'depths_midaxis')]),
              (spectra, measures_database, [('spectra_sulci', 'spectra_sulci'),
                                            ('spectra_fundi', 'spectra_fundi'),
                                            ('spectra_midaxis', 'spectra_midaxis')])])

# Connect label measures to database nodes
featureflow.connect([(positions, measures_database, [('positions_patches', 'positions_patches'),
                                              ('positions_regions', 'positions_regions')]),
              (extents, measures_database, [('extents_patches', 'extents_patches'),
                                            ('extents_regions', 'extents_regions')]),
              (curvatures, measures_database, [('curvatures_patches', 'curvatures_patches'),
                                               ('curvatures_regions', 'curvatures_regions')]),
              (depths, measures_database, [('depths_patches', 'depths_patches'),
                                           ('depths_regions', 'depths_regions')]),
              (spectra, measures_database, [('spectra_patches', 'spectra_patches'),
                                            ('spectra_regions', 'spectra_regions')])])

# Connect measure to table nodes
featureflow.connect([(measures_database, measures_table, [('measures', 'measures')])])
"""
"""
##############################################################################
#
#   Label evaluation workflow
#
##############################################################################

evalflow = workflow(name='Evaluation_workflow')

##############################################################################
#   Surface calculations
##############################################################################

# Measure surface depth and curvature nodes
depth = node(name='Compute_depth',
             interface = fn(function = compute_depth,
                            input_names = ['command',
                                           'labels'],
                            output_names = ['overlap']))
depth.inputs.command = depth_command

mbflow.connect([(atlasflow, evalflow,
                 [('Majority_vote.output_files',
                   'Evaluation_workflow.maxlabels')])])

featureflow.connect([(propagate_volume, extract_region, [('labels', 'labels')])])
featureflow.connect([(propagate, extract_patch, [('labels', 'labels')])])
"""
##############################################################################
#    Run workflow
##############################################################################
if __name__== '__main__':

    mbflow.write_graph(graph2use='flat')
    mbflow.write_graph(graph2use='hierarchical')
    mbflow.run(updatehash=False)  #mbflow.run(updatehash=True)
