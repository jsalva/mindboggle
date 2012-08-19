#!/usr/bin/python
"""
Extract fundus curves from surface mesh patches (folds).

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

#==================
# Extract all fundi
#==================
def extract_fundi(index_lists_folds, n_folds, neighbor_lists,
                  vertices, faces, depths, mean_curvatures, min_directions,
                  min_fold_size=50, thr=0.5, min_distance=5, return_arrays=1):
    """
    Extract all fundi.

    A fundus is a connected set of high-likelihood vertices in a surface mesh.

    Inputs:
    ------
    vertices:  [#vertices x 3]
    faces:  vertices for polygons [#faces x 3] numpy array
    depths:  depth values [#vertices x 1] numpy array
    mean_curvatures:  mean curvature values [#vertices x 1] numpy array
    min_directions:  directions of minimum curvature [3 x #vertices] numpy array
    fraction_folds:  fraction of vertices considered to be folds
    min_fold_size:  minimum fold size from which to find a fundus
    thr:  likelihood threshold
    min_distance:  minimum distance
    return_arrays: return numpy arrays instead of lists of lists below (1=yes, 0=no)

    Output:
    ------
    fundi:  numpy array of fundi
    fundus_lists:  list of lists of vertex indices (see return_arrays)
    likelihoods:  numpy array of likelihood values

    Calls:
    -----
    compute_likelihood()
    find_anchors()
    connect_points()

    """

    import numpy as np
    from time import time

    from extract.fundi_hmmf.compute_likelihood import compute_likelihood
    from extract.fundi_hmmf.find_points import find_anchors
    from extract.fundi_hmmf.connect_points import connect_points

    # Make sure arguments are numpy arrays
    if type(faces) != np.ndarray:
        faces = np.array(faces)
    if type(depths) != np.ndarray:
        depths = np.array(depths)
    if type(mean_curvatures) != np.ndarray:
        mean_curvatures = np.asarray(mean_curvatures)
    if type(min_directions) != np.ndarray:
        min_directions = np.asarray(min_directions)
    if type(vertices) != np.ndarray:
        vertices = np.asarray(vertices)

    # For each fold...
    print("Extract a fundus from each of {} folds...".format(n_folds))
    t1 = time()
    fundus_lists = []
    n_vertices = len(depths)
    Z = np.zeros(n_vertices)
    likelihoods = Z.copy()

    for i_fold, indices_fold in enumerate(index_lists_folds):

        print('  Fold {} of {}:'.format(i_fold + 1, n_folds))

        # Compute fundus likelihood values
        fold_likelihoods = compute_likelihood(depths[indices_fold],
                                              mean_curvatures[indices_fold])
        likelihoods[indices_fold] = fold_likelihoods

        # If the fold has enough high-likelihood vertices, continue
        likelihoods_thr = sum(fold_likelihoods > thr)
        print('    Computed fundus likelihood values: {} > {} (minimum: {})'.
              format(likelihoods_thr, thr, min_fold_size))
        if likelihoods_thr > min_fold_size:

            # Find fundus points
            fold_indices_anchors = find_anchors(vertices[indices_fold, :],
                                                fold_likelihoods,
                                                min_directions[indices_fold],
                                                min_distance, thr)
            indices_anchors = [indices_fold[x] for x in fold_indices_anchors]
            n_anchors = len(indices_anchors)
            if n_anchors > 1:

                # Connect fundus points and extract fundus
                print('    Connect {} fundus points...'.format(n_anchors))
                t2 = time()
                likelihoods_fold = Z.copy()
                likelihoods_fold[indices_fold] = fold_likelihoods

                H = connect_points(indices_anchors, faces, indices_fold,
                                   likelihoods_fold, thr, neighbor_lists)
                fundus_lists.append(H.tolist())
                print('      ...Connected {} fundus points ({:.2f} seconds)'.
                      format(n_anchors, time() - t2))
            else:
                fundus_lists.append([])
        else:
            fundus_lists.append([])

    fundi = np.ones(n_vertices)
    for fundus in fundus_lists:
        if len(fundus) > 0:
            fundi += fundus

    print('  ...Extracted fundi ({:.2f} seconds)'.format(time() - t1))

    if return_arrays:
        return fundi, np.array(fundus_lists), likelihoods
    else:
        return fundi, fundus_lists, likelihoods
