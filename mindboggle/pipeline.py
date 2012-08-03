#!/usr/bin/python
"""
This is Mindboggle's Nipype pipeline!

For more information about Mindboggle,
see the website: http://www.mindboggle.info
and read the README.

For information on Nipype: http://www.nipy.org/nipype/
http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3159964/


Authors:  Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

#=============================================================================
# Setup: import libraries and set file paths
#=============================================================================
#-----------------------------------------------------------------------------
# Import system Python libraries
#-----------------------------------------------------------------------------
import sys
from os import path, environ, makedirs, getcwd
from re import findall
#-----------------------------------------------------------------------------
# Paths
#-----------------------------------------------------------------------------
subjects = ['HLN-12-1'] #['MMRR-21-1']
subjects_path = environ['SUBJECTS_DIR']  # FreeSurfer subjects directory
base_path = '/projects/Mindboggle/mindboggle'  # mindboggle directory
results_path = '/projects/Mindboggle/results'  # Where to save output
temp_path = path.join(results_path, 'workingdir')  # Where to save temp files
code_path = path.join(base_path, 'mindboggle')
#-----------------------------------------------------------------------------
# Import Nipype Python libraries
#-----------------------------------------------------------------------------
from nipype.pipeline.engine import Workflow as workflow
from nipype.pipeline.engine import Node as node
from nipype.pipeline.engine import MapNode as mapnode
from nipype.interfaces.utility import Function as fn
from nipype.interfaces.utility import IdentityInterface as identity
from nipype.interfaces.io import DataGrabber as datain
from nipype.interfaces.io import DataSink as dataout
from nipype import config
config.enable_debug_mode()
#-----------------------------------------------------------------------------
# Import Mindboggle Python libraries
#-----------------------------------------------------------------------------
sys.path.append(code_path)
from utils.io_vtk import load_scalar, write_scalars, annot_to_vtk
from utils.io_file import read_list_strings, read_list_2strings
from utils.freesurfer2vtk import freesurfer2vtk
from label.multiatlas_labeling import register_template, \
           transform_atlas_labels, majority_vote_label
from label.aggregate_labels import aggregate_surface_labels
from measure.measure_functions import compute_depth, compute_curvature
from extract.fundi_hmmf.extract_folds import extract_folds
from extract.fundi_hmmf.extract_fundi import extract_fundi
from label.surface_labels_to_volume import write_label_file, \
           label_to_annot_file, fill_label_volume
from label.evaluate_volume_labels import measure_volume_overlap
#-----------------------------------------------------------------------------
# Debugging options
#-----------------------------------------------------------------------------
load_vtk_surfaces = False  # Load VTK surfaces (not FreeSurfer surfaces)
init_fs_labels = True  # Initialize with a FreeSurfer classifier atlas
do_evaluate_labels = True  # Compute volume overlap of auto vs. manual labels

##############################################################################
#
#   Mindboggle workflow combining:
#   * Multi-atlas labeling workflow
#   * Feature-based labeling workflow
#   * Shape analysis workflow
#   * Label evaluation workflow
#
##############################################################################
mbflow = workflow(name='Mindboggle_workflow')
mbflow.base_dir = temp_path
if not path.isdir(temp_path):  makedirs(temp_path)
# Paths within mindboggle base directory
templates_path = path.join(base_path, 'data', 'templates')
atlases_path = path.join(base_path, 'data', 'atlases')
label_string = 'labels.DKT25'
atlas_string = label_string + '.manual'

#=============================================================================
#   Inputs and outputs
#=============================================================================
#-----------------------------------------------------------------------------
# Iterate inputs over subjects, hemispheres
# (surfaces are assumed to take the form: lh.pial or lh.pial.vtk)
#-----------------------------------------------------------------------------
info = node(name = 'Inputs',
            interface = identity(fields=['subject', 'hemi']))
info.iterables = ([('subject', subjects), ('hemi', ['lh'])]) #,'rh'])])
#-----------------------------------------------------------------------------
# Location and structure of the surface inputs
#-----------------------------------------------------------------------------
surf = node(name = 'Surfaces',
            interface = datain(infields=['subject', 'hemi'],
                               outfields=['surface_files', 'sphere_files']))
surf.inputs.base_directory = subjects_path
surf.inputs.template = '%s/surf/%s.%s'
surf.inputs.template_args['surface_files'] = [['subject', 'hemi', 'pial']]
surf.inputs.template_args['sphere_files'] = [['subject', 'hemi', 'sphere']]
mbflow.connect([(info, surf, [('subject','subject'), ('hemi','hemi')])])
#-----------------------------------------------------------------------------
# Outputs
#-----------------------------------------------------------------------------
datasink = node(dataout(), name = 'Results')
datasink.inputs.base_directory = results_path
datasink.inputs.container = 'output'
if not path.isdir(results_path):  makedirs(results_path)
#-----------------------------------------------------------------------------
# Evaluation inputs: location and structure of atlas volumes
#-----------------------------------------------------------------------------
if do_evaluate_labels:
    atlas = node(name = 'Atlas',
               interface = datain(infields=['subject'],
                                  outfields=['atlas_file']))
    atlas.inputs.base_directory = atlases_path
    atlas.inputs.template = 'atlases/%s/aparcNMMjt+aseg.nii.gz'
    atlas.inputs.template_args['atlas_file'] = [['subject']]
    mbflow.connect([(info, atlas, [('subject','subject')])])
#-----------------------------------------------------------------------------
#   Convert surfaces to VTK
#-----------------------------------------------------------------------------
if not load_vtk_surfaces:
    convertsurf = mapnode(name = 'Convert_surface',
                          iterfield = ['in_file'],
                          interface = fn(function = freesurfer2vtk,
                          input_names = ['in_file'],
                          output_names = ['out_file']))
    mbflow.connect([(surf, convertsurf, [('surface_files','in_file')])])

##############################################################################
#
#   Multi-atlas labeling workflow
#
##############################################################################
atlasflow = workflow(name='Atlas_workflow')

#=============================================================================
#   Initialize labels with a classifier atlas
#=============================================================================
if init_fs_labels:
    fslabels = node(name = 'Convert_FreeSurfer_labels',
                    interface = fn(function = annot_to_vtk,
                    input_names = ['surface_file',
                                   'hemi',
                                   'subject',
                                   'subjects_path',
                                   'annot_name'],
                    output_names = ['fslabels_file']))
    fslabels.inputs.annot_name = 'aparc+aseg.annot'
    fslabels.inputs.subjects_path = subjects_path
    atlasflow.add_nodes([fslabels])
    mbflow.connect([(info, atlasflow,
                     [('hemi', 'Convert_FreeSurfer_labels.hemi'),
                      ('subject', 'Convert_FreeSurfer_labels.subject')])])
    mbflow.connect([(surf, atlasflow,
                     [('surface_files',
                       'Convert_FreeSurfer_labels.surface_file')])])
    #=============================================================================
    #   Aggregate labels
    #=============================================================================
    aggregate = node(name='Aggregate_labels',
                     interface = fn(function = aggregate_surface_labels,
                     input_names = ['vtk_file',
                                    'aggregate_labels_list',
                                    'label_string'],
                     output_names = ['aggregate_labels_vtk']))
    aggregate.inputs.aggregate_labels = path.join(atlases_path,
                                                  'labels.DKT31to25.txt')
    aggregate.inputs.label_string = label_string + '.vtk'
    atlasflow.connect([(fslabels, aggregate, [('fslabels_file', 'vtk_file')])])
    mbflow.connect([(atlasflow, datasink,
                     [('Aggregate_labels.aggregate_labels_vtk',
                       'labels.@aggregateFSlabels')])])

#=============================================================================
#   Initialize labels using multi-atlas registration
#=============================================================================
else:
    #-------------------------------------------------------------------------
    # Register surfaces to average template
    #-------------------------------------------------------------------------
    register = node(name = 'Register_template',
                    interface = fn(function = register_template,
                                   input_names = ['hemi',
                                                  'sphere_file',
                                                  'transform',
                                                  'templates_path',
                                                  'template'],
                                   output_names = ['transform']))
    template = 'OASIS-TRT-20'
    register.inputs.template = template + '.tif'
    register.inputs.transform = 'sphere_to_' + template + '_template.reg'
    register.inputs.templates_path = path.join(templates_path, 'freesurfer')
    atlasflow.add_nodes([register])
    mbflow.connect([(info, atlasflow, [('hemi', 'Register_template.hemi')]),
                    (surf, atlasflow, [('sphere_files',
                                        'Register_template.sphere_file')])])
    #-------------------------------------------------------------------------
    # Register atlases to subject via template
    #-------------------------------------------------------------------------
    transform = mapnode(name = 'Transform_atlas_labels',
                        iterfield = ['atlas'],
                        interface = fn(function = transform_atlas_labels,
                                       input_names = ['hemi',
                                                      'subject',
                                                      'transform',
                                                      'subjects_path',
                                                      'atlas',
                                                      'atlas_string'],
                                       output_names = ['output_file']))
    # Load atlas list
    atlas_list_file = path.join(atlases_path, 'atlases.txt')
    atlas_list = read_list_strings(atlas_list_file)

    transform.inputs.atlas = atlas_list
    transform.inputs.subjects_path = subjects_path
    transform.inputs.atlas_string = atlas_string
    atlasflow.add_nodes([transform])
    mbflow.connect([(info, atlasflow,
                     [('hemi', 'Transform_atlas_labels.hemi'),
                      ('subject', 'Transform_atlas_labels.subject')])])
    atlasflow.connect([(register, transform, [('transform', 'transform')])])
    #transform.inputs.transform = 'sphere_to_' + template + '_template.reg'
    #-----------------------------------------------------------------------------
    # Majority vote label
    #-----------------------------------------------------------------------------
    vote = node(name='Label_vote',
                interface = fn(function = majority_vote_label,
                               input_names = ['surface_file',
                                              'annot_files'],
                               output_names = ['maxlabel_file',
                                               'labelcounts_file',
                                               'labelvotes_file',
                                               'consensus_vertices']))
    atlasflow.add_nodes([vote])
    if load_vtk_surfaces:
        mbflow.connect([(surf, atlasflow,
                         [('surface_files', 'Label_vote.surface_file')])])
    else:
        mbflow.connect([(convertsurf, atlasflow,
                         [('out_file', 'Label_vote.surface_file')])])
    atlasflow.connect([(transform, vote, [('output_file', 'annot_files')])])
    mbflow.connect([(atlasflow, datasink,
                     [('Label_vote.maxlabel_file', 'labels.@max'),
                      ('Label_vote.labelcounts_file', 'labels.@counts'),
                      ('Label_vote.labelvotes_file', 'labels.@votes')])])
"""
##############################################################################
#
#   Feature-based labeling workflow
#
##############################################################################
featureflow = workflow(name='Feature_workflow')

#=============================================================================
#   Surface measurements
#=============================================================================
#-----------------------------------------------------------------------------
# Measure surface depth
#-----------------------------------------------------------------------------
depth = node(name='Compute_depth',
             interface = fn(function = compute_depth,
                            input_names = ['command',
                                           'surface_file'],
                            output_names = ['depth_file']))
depth_command = path.join(code_path,'measure', 'surface_measures',
                                    'bin', 'travel_depth', 'TravelDepthMain')
depth.inputs.command = depth_command
#-----------------------------------------------------------------------------
# Measure surface curvature
#-----------------------------------------------------------------------------
curvature = node(name='Compute_curvature',
                 interface = fn(function = compute_curvature,
                                input_names = ['command',
                                               'surface_file'],
                                output_names = ['mean_curvature_file',
                                                'gauss_curvature_file',
                                                'max_curvature_file',
                                                'min_curvature_file',
                                                'min_curvature_vector_file']))
curvature_command = path.join(code_path, 'measure', 'surface_measures',
                                         'bin', 'curvature', 'CurvatureMain')
curvature.inputs.command = curvature_command
#-----------------------------------------------------------------------------
# Add and connect nodes, save output files
#-----------------------------------------------------------------------------
featureflow.add_nodes([depth, curvature])
if load_vtk_surfaces:
    mbflow.connect([(surf, featureflow,
                     [('surface_files','Compute_depth.surface_file')])])
    mbflow.connect([(surf, featureflow,
                     [('surface_files','Compute_curvature.surface_file')])])
else:
    mbflow.connect([(convertsurf, featureflow,
                     [('out_file', 'Compute_depth.surface_file')])])
    mbflow.connect([(convertsurf, featureflow,
                 [('out_file', 'Compute_curvature.surface_file')])])
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
                   'surfaces.@min_curvature'),
                  ('Compute_curvature.min_curvature_vector_file',
                   'surfaces.@min_curvature_vectors')])])
#=============================================================================
#   Feature extraction
#=============================================================================
#-----------------------------------------------------------------------------
# Load depth and curvature files
#-----------------------------------------------------------------------------
load_depth = node(name='Load_depth',
                  interface = fn(function = load_scalar,
                                 input_names = ['filename'],
                                 output_names = ['Points',
                                                 'Faces',
                                                 'Scalars']))
load_depth.inputs.filename='/projects/Mindboggle/results/workingdir/Mindboggle_workflow/Feature_workflow/_hemi_lh_subject_HLN-12-1/Compute_depth/lh.pial.depth.vtk'
#featureflow.connect([(depth, load_depth,
#                      [('depth_file','filename')])])

load_curvature = node(name='Load_curvature',
                      interface = fn(function = load_scalar,
                                     input_names = ['filename'],
                                     output_names = ['Points',
                                                     'Faces',
                                                     'Scalars']))
featureflow.connect([(curvature, load_curvature,
                      [('mean_curvature_file','filename')])])

"""
"""
load_directions = node(name='Load_directions',
                       interface = fn(function = load_scalar,
                                      input_names = ['filename'],
                                      output_names = ['Points',
                                                      'Faces',
                                                      'Scalars']))
featureflow.connect([(curvature, load_directions,
                      [('min_curvature_vector_file','filename')])])

"""
"""
#-----------------------------------------------------------------------------
# Extract folds
#-----------------------------------------------------------------------------
folds = node(name='Extract_folds',
             interface = fn(function = extract_folds,
                            input_names = ['faces',
                                           'depths',
                                           'fraction_folds',
                                           'min_fold_size'],
                            output_names = ['folds',
                                            'n_folds',
                                            'indices_folds',
                                            'index_lists_folds',
                                            'neighbor_lists',
                                            'faces_folds',
                                            'LUTs',
                                            'LUT_names']))
fraction_folds = 0.5
min_fold_size = 50
folds.inputs.fraction_folds = fraction_folds
folds.inputs.min_fold_size = min_fold_size
featureflow.connect([(load_depth, folds, [('Faces','faces'),
                                          ('Scalars','depths')])])
"""
"""
#-----------------------------------------------------------------------------
# Extract fundi (curves at the bottoms of folds)
#-----------------------------------------------------------------------------
fundi = node(name='Extract_fundi',
             interface = fn(function = extract_fundi,
                            input_names = ['index_lists_folds',
                                           'n_folds',
                                           'neighbor_lists',
                                           'vertices',
                                           'faces',
                                           'depths',
                                           'mean_curvatures',
                                           'min_directions',
                                           'min_fold_size',
                                           'thr',
                                           'min_distance'],
                            output_names = ['fundi',
                                            'fundus_lists',
                                            'likelihoods']))
thr = 0.5
min_distance = 5.0
fundi.inputs.thr = thr
fundi.inputs.min_fold_size = min_fold_size
fundi.inputs.min_distance = min_distance
featureflow.connect([(folds, fundi, [('index_lists_folds','index_lists_folds'),
                                     ('n_folds','n_folds'),
                                     ('neighbor_lists','neighbor_lists'),
                                     ('faces_folds','faces')]),
                     (load_depth, fundi, [('Points','vertices'),
                                          ('Scalars','depths')]),
                     (load_curvature, fundi, [('Scalars','mean_curvatures')]),
                     (load_directions, fundi, [('Scalars','min_directions')])])

#-----------------------------------------------------------------------------
# Extract medial surfaces
#-----------------------------------------------------------------------------
medial = node(name='Extract_medial',
                 interface = fn(function = extract_midaxis,
                                input_names = ['depth_file',
                                               'mean_curv_file',
                                               'gauss_curv_file'],
                                output_names = ['midaxis']))
"""
"""
#-----------------------------------------------------------------------------
# Write folds, likelihoods, and fundi to VTK files
#-----------------------------------------------------------------------------
save_folds = node(name='Save_folds',
                  interface = fn(function = write_scalars,
                                 input_names = ['vtk_file',
                                                'Points',
                                                'Vertices',
                                                'Faces',
                                                'LUTs',
                                                'LUT_names'],
                                 output_names = ['vtk_file']))
save_folds.inputs.vtk_file = path.join(getcwd(), 'folds.vtk')
featureflow.connect([(load_depth, save_folds, [('Points','Points')])])
featureflow.connect([(folds, save_folds, [('indices_folds','Vertices'),
                                          ('faces_folds','Faces'),
                                          ('LUTs','LUTs'),
                                          ('LUT_names','LUT_names')])])

save_likelihoods = node(name='Save_likelihoods',
                        interface = fn(function = write_scalars,
                                       input_names = ['vtk_file',
                                                      'Points',
                                                      'Vertices',
                                                      'Faces',
                                                      'LUTs',
                                                      'LUT_names'],
                                       output_names = ['vtk_file']))
save_likelihoods.inputs.vtk_file = path.join(getcwd(), 'likelihoods.vtk')
save_likelihoods.inputs.LUT_names = ['likelihoods']
featureflow.connect([(load_depth, save_likelihoods, [('Points','Points')])])
featureflow.connect([(folds, save_likelihoods, [('indices_folds','Vertices'),
                                          ('faces_folds','Faces')])])
featureflow.connect([(fundi, save_likelihoods, [('likelihoods','LUTs')])])

save_fundi = node(name='Save_fundi',
                  interface = fn(function = write_scalars,
                                 input_names = ['vtk_file',
                                                'Points',
                                                'Vertices',
                                                'Faces',
                                                'LUTs',
                                                'LUT_names'],
                                 output_names = ['vtk_file']))
save_fundi.inputs.vtk_file = path.join(getcwd(), 'fundi.vtk')
save_fundi.inputs.LUT_names = ['fundi']
featureflow.connect([(load_depth, save_fundi, [('Points','Points')])])
featureflow.connect([(folds, save_fundi, [('indices_folds','Vertices'),
                                          ('faces_folds','Faces')])])
featureflow.connect([(fundi, save_fundi, [('fundi','LUTs')])])

mbflow.connect([(featureflow, datasink,
                 [('Save_folds.vtk_file','folds'),
                  ('Save_likelihoods.vtk_file','likelihoods'),
                  ('Save_fundi.vtk_file','fundi')])])

"""
"""
#=============================================================================
#   Label propagation
#=============================================================================
#-----------------------------------------------------------------------------
# Label propagation node
#-----------------------------------------------------------------------------
propagate = node(name='Propagate_labels',
                    interface = fn(
                                     function = propagate_labels,
                                     input_names=['labels', 'fundi'],
                                     output_names=['labels']))

#-----------------------------------------------------------------------------
# Volume label propagation node
#-----------------------------------------------------------------------------
propagate_volume = node(name='Propagate_volume_labels',
                           interface = fn(
                                            function = propagate_volume_labels,
                                            input_names = ['labels'],
                                            output_names = ['volume_labels']))

#-----------------------------------------------------------------------------
# Labeled surface patch and volume extraction nodes
#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
# Connect registration and extraction to label propagation nodes
#-----------------------------------------------------------------------------
featureflow.connect([(transform, propagate, [('labels','labels')]),
                     (extract_fundi, propagate, [('fundi','fundi')])])

# Connect label propagation to labeled surface patch and volume extraction nodes
featureflow.connect([(propagate, propagate_volume, [('labels', 'labels')])])

featureflow.connect([(propagate_volume, extract_region, [('labels', 'labels')])])
featureflow.connect([(propagate, extract_patch, [('labels', 'labels')])])

#=============================================================================
#   Feature segmentation / identification
#=============================================================================
#-----------------------------------------------------------------------------
# Feature segmentation nodes
#-----------------------------------------------------------------------------
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
#
#   Shape analysis workflow
#
##############################################################################
shapeflow = workflow(name='Shape_workflow')

#-----------------------------------------------------------------------------
# Shape measurement nodes
#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
# Connect labeled surface patches and volumes to shape measurement nodes
#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
# Connect feature to shape measurement nodes
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
# Database nodes
#-----------------------------------------------------------------------------
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

#-----------------------------------------------------------------------------
# Connect surface maps to database nodes
#-----------------------------------------------------------------------------
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
if do_evaluate_labels:
    evalflow = workflow(name='Evaluation_workflow')

    #=============================================================================
    #   Filling a volume (e.g., gray matter) mask with labels
    #=============================================================================
    #-------------------------------------------------------------------------
    # Write .label files for surface vertices
    #-------------------------------------------------------------------------
    writelabels = mapnode(name='Write_label_files',
                          iterfield = ['label_number', 'label_name'],
                          interface = fn(function = write_label_file,
                                         input_names = ['hemi',
                                                        'surface_file',
                                                        'label_number',
                                                        'label_name'],
                                         output_names = ['label_file']))
    # List of cortical labels
    ctx_labels_file = path.join(atlases_path, label_string + '.txt')
    ctx_label_numbers, ctx_label_names = read_list_2strings(ctx_labels_file)

    writelabels.inputs.label_number = ctx_label_numbers
    writelabels.inputs.label_name = ctx_label_names
    evalflow.add_nodes([writelabels])
    mbflow.connect([(info, evalflow, [('hemi', 'Write_label_files.hemi')])])
    if init_fs_labels:
        evalflow.connect([(fslabels, writelabels,
                           [('fslabels_file','surface_file')])])
    else:
        evalflow.connect([(vote, writelabels,
                           [('maxlabel_file','surface_file')])])
    #-------------------------------------------------------------------------
    # Write .annot file from .label files
    #-------------------------------------------------------------------------
    writeannot = node(name='Write_annot_file',
                      interface = fn(function = label_to_annot_file,
                                     input_names = ['hemi',
                                                    'subjects_path',
                                                    'subject',
                                                    'label_files',
                                                    'colortable'],
                                     output_names = ['annot_name',
                                                     'annot_file']))
    writeannot.inputs.subjects_path = subjects_path
    writeannot.inputs.colortable = path.join(atlases_path, label_string + '.txt')
    evalflow.add_nodes([writeannot])
    mbflow.connect([(info, evalflow,
                     [('hemi', 'Write_annot_file.hemi')])])
    mbflow.connect([(info, evalflow,
                     [('subject', 'Write_annot_file.subject')])])
    evalflow.connect([(writelabels, writeannot, [('label_file','label_files')])])
    mbflow.connect([(evalflow, datasink,
                     [('Write_annot_file.annot_file', 'labels.@max_annot')])])
    #-------------------------------------------------------------------------
    # Fill volume mask with surface vertex labels from .annot file
    #-------------------------------------------------------------------------
    fillvolume = node(name='Fill_volume_labels',
                      interface = fn(function = fill_label_volume,
                                     input_names = ['subject', 'annot_name'],
                                     output_names = ['output_file']))
    evalflow.add_nodes([fillvolume])
    mbflow.connect([(info, evalflow,
                     [('subject', 'Fill_volume_labels.subject')])])
    evalflow.connect([(writeannot, fillvolume,
                        [('annot_name','annot_name')])])
    mbflow.connect([(evalflow, datasink,
                     [('Fill_volume_labels.output_file',
                       'labels.@maxvolume')])])
    #-------------------------------------------------------------------------
    # Evaluate volume labels
    #-------------------------------------------------------------------------
    eval_labels = node(name='Evaluate_volume_labels',
                          interface = fn(function = measure_volume_overlap,
                                         input_names = ['labels',
                                                        'atlas_file',
                                                        'input_file'],
                                         output_names = ['overlaps']))
    evalflow.connect([(fillvolume, eval_labels,
                        [('output_file', 'input_file')])])
    mbflow.connect([(atlas, evalflow,
                   [('atlas_file', 'Evaluate_volume_labels.atlas_file')])])
    #------------
    # Load labels
    #------------
    labels_file = path.join(atlases_path, 'labels.DKT32.txt')
    labels = read_list_strings(labels_file)
    eval_labels.inputs.labels = labels
"""
##############################################################################
#
#    Run workflow
#
##############################################################################
if __name__== '__main__':

    mbflow.write_graph(graph2use='flat')
    mbflow.write_graph(graph2use='hierarchical')
    mbflow.run(updatehash=False)  #mbflow.run(updatehash=True)



