#!/usr/bin/python
"""
Compute fundus likelihood values.


Authors:
    Yrjo Hame  .  yrjo.hame@gmail.com
    Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np

verbose = 1  # 2 for debugging

#============================
# Compute score at percentile
#============================
# http://code.activestate.com/recipes/511478/ (r2)
# Alternative scipy implementation:
# from scipy.stats import scoreatpercentile
# depth_found = scoreatpercentile(depths, depth_threshold2)

def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    Inputs:
    ------
    N: list of values. Note N MUST BE already sorted
    percent: float value from 0.0 to 1.0
    key: optional key function to compute value from each element of N

    Output:
    ------
    percentile of the values

    """
    if len(N) == 0:
        return None

    k = (len(N)-1) * percent
    f = np.floor(k)
    c = np.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)

    return d0 + d1


#=================================
# Compute fundus likelihood values
#=================================
def compute_likelihood(depths, curvatures, fraction_below, slope_factor):
    """
    Compute fundus likelihood values.

    Inputs:
    ------
    curvatures: mean curvature values [#sulcus vertices x 1] numpy array
    depths: depth values [#sulcus vertices x 1] numpy array
    fraction_below: fraction of values from which to compute the percentile
    slope_factor: used to compute the "gain" of the slope of sigmoidal values

    Parameters:
    ----------
    high_map_value: used for computing the depth and curvature slope factors

    Output:
    ------
    likelihoods: likelihood values [#sulcus vertices x 1] numpy array

    Calls:
    -----
    percentile()

    """

    #=============================================
    # Find depth and curvature values greater than
    # the values of a fraction of the vertices
    #=============================================
    sort_depth = np.sort(depths)
    sort_curve = np.sort(curvatures)
    p_depth = percentile(sort_depth, fraction_below, key=lambda x:x)
    p_curve = percentile(sort_curve, fraction_below, key=lambda x:x)

    #==========================================
    # Find slope for depth and curvature values
    #==========================================
    # Factor influencing "gain" or "sharpness" of the sigmoidal function below
    # high_map_value = 0.9
    # slope_factor = abs(np.log((1. / high_map_value) - 1))  # = 2.1972246
    gain_depth = slope_factor / p_depth
    gain_curve = slope_factor / p_curve

    #==========================
    # Compute likelihood values
    #==========================
    # Map values with sigmoidal function to range [0,1]
    # Y(t) = 1/(1 + e(-k*(X - thr)),
    # where k is the gain factor, and thr is the slider term
    depth_values = 1 / (1.0 + np.exp(-gain_depth * (depths - p_depth)))
    curve_values = 1 / (1.0 + np.exp(-gain_curve * (curvatures - p_curve)))

    # Assign likelihood values to vertices
    likelihoods = depth_values * curve_values

    return likelihoods
