#!/usr/bin/python
"""
Extract fundi.

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com  (original Matlab code)
Arno Klein  .  arno@mindboggle.info  (translated to Python)

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np

from extract_sulci import extract_sulci
from compute_fundus_likelihood import compute_fundus_likelihood
from find_neighbors import find_neighbors
from find_anchor_points import find_anchor_points
from connect_the_dots import connect_the_dots

#=================
# Extract a fundus
#=================
def extract_fundus(L, sulci, sulcus_index, vertices, faces,
                            min_distances, L_threshold=0.5,
                            min_sulcus_size=30, max_neighbors=15):
    """
    Extract a single fundus.

    A fundus is a connected set of high-likelihood vertices in a surface mesh.

    Inputs:
    ------
    L: fundus likelihood values [#vertices x 1] numpy array
    sulci: sulcus values [#vertices x 1] numpy array
    sulcus_index: sulcus number [int]
    vertices: [#vertices x 3] numpy array
    faces: vertices for polygons [#faces x 3] numpy array
    min_distances: [#vertices x 1] numpy array
    L_threshold: likelihood threshold
    min_sulcus_size: minimum sulcus size from which to find a fundus
    max_neighbors: maximum number of neighbors per sulcus vertex

    Output:
    ------
    fundus: binary assignments for connected vertices:????
            [#fundus vertices x 1] numpy array

    Calls:
    -----
    find_neighbors(): numpy array of indices
    find_anchor_points()
    connect_the_dots()

    """

    # Retain only likelihood values for the sulcus corresponding to sulcus_index
    L[sulci != sulcus_index] = 0

    # If the size of the sulcus is sufficiently large, continue
    if sum(L > L_threshold) > min_sulcus_size:

        # Find neighbors for each sulcus vertex and arrange as rows in an array
        sulcus_indices = np.where(L > 0)
        len_sulcus = len(sulcus_indices)
        sulcus_neighbors = np.zeros((len_sulcus, max_neighbors))
        for i in range(len_sulcus):
            neighbors = find_neighbors(faces, sulcus_indices(i))
            len_neighbors = len(neighbors)
            if len_neighbors > max_neighbors:
                sulcus_neighbors[i, range(max_neighbors)] = neighbors[0 : max_neighbors]
            else:
                sulcus_neighbors[i, range(len_neighbors)] = neighbors

        # Initialize all likelihood values within sulcus greater than 0.5
        # and less than or equal to 1.0.
        # This is necessary to guarantee correct topology
        L_init = (L + 1.000001) / 2.0
        L_init[L == 0] = 0
        L_init[L_init > 1] = 1

        # Find fundus points
        fundus_points = find_anchor_points(vertices, L, min_distances)
        if any(fundus_points):
            fundus = connect_the_dots(L, L_init, vertices, faces, fundus_points,
                                      sulcus_neighbors, sulcus_indices)
    else:
        print('Sulcus too small: ', str(sum(L > 0.5) > min_sulcus_size))
        fundus = np.zeros(len(L))

    return fundus

#==================
# Extract all fundi
#==================
def extract_all_fundi(vertices, faces, depths, mean_curvatures, min_directions, depth_threshold=0.2):
    """
    Extract all fundi.

    Inputs:
    ------
    vertices: [#vertices x 3] numpy array
    faces: vertices for polygons [#faces x 3] numpy array
    depths: depth values [#vertices x 1] numpy array
    mean_curvatures: mean curvature values [#vertices x 1] numpy array
    min_directions: directions of minimum curvature [3 x #vertices] numpy array
    depth_threshold: depth threshold for defining sulci

    Output:
    ------
    fundi: [#vertices x #sulci] numpy array
           Each column represents a fundus for a specific sulcus.
           Values range from 0 to 1; values above 0.5 are considered part of the fundus.

    Calls:
    -----
    extract_sulci()
    compute_fundus_likelihood()
    extract_fundus()

    """

    # Extract sulci
    print('Extract sulci...')
    sulci, n_sulci = extract_sulci(faces, depths, depth_threshold)

    # Compute fundus likelihood values
    print('Compute fundus likelihood values...')
    n_vertices = len(depths)
    L = np.zeros(n_vertices)
    for sulcus_index in range(1, n_sulci + 1):
        L = L + compute_fundus_likelihood(mean_curvatures, depths, sulci, sulcus_index)

    # Extract individual fundi and store them as
    print('Extract fundi...')
    fundi = np.zeros(n_vertices, n_sulci)
    for sulcus_index in range(1, n_sulci + 1):
        fundi[:, sulcus_index - 1] = extract_fundus(L, sulci, sulcus_index, vertices, faces, min_directions)

    return fundi
