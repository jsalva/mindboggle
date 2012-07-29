#!/usr/bin/python
"""
Compute likelihood and cost values for curves on a surface mesh.


Authors:
    Yrjo Hame  .  yrjo.hame@gmail.com
    Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np


#====================
# Likelihood function
#====================
def compute_likelihood(depths, curvatures):
    """
    Compute (fundus) curve likelihood values on a surface mesh.

    Inputs:
    ------
    depths: depth values in [0,1]: [#sulcus vertices x 1] numpy array
    curvatures: mean curvature values in [-1,1] [#sulcus vertices x 1] array

    Parameters:
    ----------
    slope_factor: used to compute the "gain" of the slope of sigmoidal values

    Output:
    ------
    likelihoods: likelihood values [#sulcus vertices x 1] numpy array

    """

   #==========================================
    # Normalize depth values to interval [0,1]
    # Curvature values retain their values
    # Compute the median absolute deviations
    #=========================================
    depths_norm = depths / max(depths)
    depth_avg = np.mean(depths_norm)
    depth_std = np.std(depths_norm)
    curve_std = np.std(curvatures) / 2  # divide by 2 because of [-1,1] interval

    #==========================================
    # Find slope for depth and curvature values
    #==========================================
    # Factor influencing "gain" or "sharpness" of the sigmoidal function below
    # slope_factor = abs(np.log((1. / x) - 1))  # 2.197224577 for x = 0.9
    #slope_factor = 2.197224577
    #gain_depth = slope_factor / (2 * depth_std)
    #gain_curve = slope_factor / (2 * curve_std)
    gain_depth = 1 / depth_std
    gain_curve = 1 / curve_std

    #==========================
    # Compute likelihood values
    #==========================
    # Map values with sigmoidal function to range [0,1]
    # Y(t) = 1/(1 + exp(-gain*(X - shift)), where shift lowers the values
    depth_sigmoid = 1 / (1.0 + np.exp(-gain_depth * (depths_norm - depth_avg)))
    curve_sigmoid = 1 / (1.0 + np.exp(-gain_curve * curvatures))

    likelihoods = depth_sigmoid * curve_sigmoid

    return likelihoods


#--------------
# Cost function
#--------------
def compute_cost(wL, wN, likelihood, hmmf, hmmf_neighbors):
    """
    Cost function for penalizing unlikely curve (fundus) vertices.

    This cost function penalizes vertices that do not have high likelihood
    values and have Hidden Markov Measure Field (HMMF) values different than
    their neighbors.

    cost = wL * hmmf * (1 - likelihood) +
           wN * sum(abs(hmmf - hmmf_neighbors)) / len(hmmf_neighbors)

    formerly:
    cost = hmmf * np.sqrt((wL - likelihood)**2) +
           wN * sum((hmmf - hmmf_neighbors)**2)

    term 1 promotes high likelihood values
    term 2 promotes smoothness of the HMMF values

    Inputs:
    ------
    wL: influence of likelihood on cost (term 1)
    wN: weight influence of neighbors on cost (term 2)
    likelihood: likelihood value in interval [0,1]
    hmmf: HMMF value
    hmmf_neighbors: HMMF values of neighboring vertices

    Output:
    ------
    cost

    """
    cost = hmmf * (wL - likelihood) + wN * sum((hmmf - hmmf_neighbors)**2)
    #return wL * hmmf * (1 - likelihood) + wN * sum((hmmf - hmmf_neighbors)**2)

#    wL = 1
#    wN = 1
#    return wL * hmmf * (1 - likelihood) +\
#           wN * sum(abs(hmmf - hmmf_neighbors)) / len(hmmf_neighbors)
    return cost

#==========================
# Median absolute deviation
#==========================
#def mad(x):
#    return np.median([abs(val - np.median(x)) for val in x])
