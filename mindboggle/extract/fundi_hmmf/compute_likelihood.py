#!/usr/bin/python
"""
Compute fundus likelihood values.


Authors:
    Yrjo Hame  .  yrjo.hame@gmail.com
    Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np
from scipy.stats import scoreatpercentile

print_debug = 0

#=================================
# Compute fundus likelihood values
#=================================
def compute_likelihood(sulcus, sulcus_depths, sulcus_curvatures):
    """
    Compute fundus likelihood values.

    ????[Include an explanation of adaptive thresholding]

    Inputs:
    ------
    sulcus: sulcus values [#sulcus vertices x 1] numpy array
    sulcus_curvatures: mean curvature values [#sulcus vertices x 1] numpy array
    sulcus_depths: depth values [#sulcus vertices x 1] numpy array

    Parameters:
    ----------
    Adaptive thresholding:
      depth_threshold1: ????
      depth_threshold2: ????
      curvature_threshold: ????
      high_map_value: ????
    Increments to reduce computation time:
      increment1
      increment2

    Output:
    ------
    sulcus_likelihood: fundus likelihood values [#sulcus vertices x 1] numpy array

    """
    # Parameters for adaptive thresholding
    depth_threshold1 = 0.6
    depth_threshold2 = 0.05
    curvature_threshold = 0.3
    high_map_value = 0.9

    # Increments to reduce computation time
    depth_increment = 0.01
    curvature_increment = 0.0001

    slope_factor = np.log((1. / high_map_value) - 1)

    # Take the opposite of the curvature values
    sulcus_curvatures = -sulcus_curvatures

    # Find sulcus depths and curvature values
    len_sulcus = np.float(len(sulcus))

    """
    # Alternative to resetting the threshold values below?
    depth_found = scoreatpercentile(sulcus_depths, depth_threshold2)
    slope_depth = -slope_factor / (search - depth_found)
    # Map depth values with sigmoidal function to range [0,1]
    st_depths = 1 / (1 + np.exp(-slope_depth * (depths - depth_found)))
    """

    # Find depth value where less than depth_threshold1 of sulcus vertices are deeper
    mass_left = 1
    search = 0
    while mass_left > depth_threshold1:
        search += depth_increment
        mass_left = sum(sulcus_depths > search) / len_sulcus
    depth_found = search
    if print_debug:
        print(str(depth_threshold1) +
              ' of sulcus vertices are deeper than ' + str(search))

    # Find depth value where less than depth_threshold2 of sulcus vertices are deeper
    while mass_left > depth_threshold2:
        search += depth_increment
        mass_left = sum(sulcus_depths > search) / len_sulcus
    if search == depth_found:
        st_depths = np.zeros(len_sulcus)
    else:
        slope_depth = -slope_factor / (search - depth_found)
        # Map depth values with sigmoidal function to range [0,1]
        st_depths = 1 / (1 + np.exp(-slope_depth * (sulcus_depths - depth_found)))
    if print_debug:
        print(str(depth_threshold2) +
              ' of sulcus vertices are deeper than ' + str(search))

    # Find slope for curvature values
    mass_left = 1
    search = 0
    while mass_left > curvature_threshold:
        search += curvature_increment
        mass_left = sum(sulcus_curvatures > search) / len_sulcus
    if print_debug:
        print(str(curvature_threshold) +
              ' of sulcus vertices have greater curvature than ' + str(search))
    slope_curvature = -slope_factor / search
    # Prevent precsion errors
    if slope_curvature > 1000:
        if print_debug:
            print('(high slope curvature: ' + str(slope_curvature) + ')')
        sulcus_curvatures[sulcus_curvatures < 0] = np.Inf
        sulcus_curvatures[sulcus_curvatures > 0] = 0
    # Map curvature values with sigmoidal function to range [0,1]
    st_curvatures = 1 / (1 + np.exp(-slope_curvature * sulcus_curvatures))

    # Assign likelihood values to sulcus vertices
    sulcus_likelihood = st_depths * st_curvatures  # element-wise multiplication

    return sulcus_likelihood
