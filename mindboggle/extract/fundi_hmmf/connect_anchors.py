#!/usr/bin/python
"""
Connect surface mesh vertices ("anchors").

Connect vertices according to Hidden Markov Measure Field (HMMF)
probability values.

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np
from find_neighbors import find_neighbors
from itertools import combinations as combos
from time import time

#--------------------
# Compute probability
#--------------------
def prob(wt_likelihood, likelihood, wt_neighbors, hmmf, hmmf_neighbors):
    """
    Compute Hidden Markov Measure Field (HMMF) probability for a given vertex.

    p = -hmmf * np.sqrt((wt_likelihood - likelihood)**2)
        - wt_neighbors * sum((hmmf - hmmf_neighbors)**2)

    term 1 promotes high likelihood values
    term 2 promotes smoothness of the HMMF values

    Inputs:
    ------
    wt_likelihood: weight influence of likelihood on probability (term 1)
    wt_neighbors: weight influence of neighbors on probability (term 2)
    likelihood: likelihood value
    hmmf: HMMF value
    hmmf_neighbors: HMMF values of neighboring vertices

    Output:
    ------
    p: probability

    """
    return -hmmf * abs(wt_likelihood - likelihood) - \
            wt_neighbors * sum((hmmf - hmmf_neighbors)**2)

#-----------------------
# Test for simple points
#-----------------------
def simple_test(faces, index, values, thr, neighbors, nlist):
    """
    Test to see if vertex is a "simple point".

    A simple point is a vertex that when removed from or added to an object
    (e.g., a curve) on a surface mesh does not alter the topology of the object.

    Inputs:
    ------
    faces: [#faces x 3] numpy array
    index: index of vertex
    values: values: [#vertices x 1] numpy array
    thr: threshold
    neighbors: list of indices of neighboring vertices
    nlist: 1 or 0 to indicate whether or not "neighbors"
           is a list of lists of neighbors for all vertices

    Output:
    ------
    sp: simple point or not? (1 or 0)

    Calls:
    -----
    find_neighbors()

    """

    # Find neighbors to the input vertex, and binarize them
    # into those greater than the likelihood threshold, thr,
    # and those less than or equal to thr ("inside" and "outside").
    # Count the number of "inside" and "outside" neighbors
    if nlist:
        I_neighbors = neighbors[index]
    else:
        I_neighbors = neighbors
    neighbor_values = values[I_neighbors]
    inside = [I_neighbors[i] for i,x in enumerate(neighbor_values) if x > thr]
    n_inside = len(inside)
    n_outside = len(I_neighbors) - n_inside

    print('n')
    print(n_inside)
    print(n_outside)

    # If the number of inside or outside neighbors is zero,
    # than the vertex IS NOT a simple point
    if n_outside * n_inside == 0:
        sp = 0
    # Or if either the number of inside or outside neighbors is one,
    # than the vertex IS a simple point
    elif n_outside == 1 or n_inside == 1:
        sp = 1
    # Otherwise, test to see if all of the inside neighbors share neighbors
    # with each other, in which case the vertex IS a simple point
    else:
        # Reset vertex value
        values[index] = -1

        # For each neighbor exceeding the threshold,
        # find its neighbors that also exceed the threshold,
        # then store these neighbors' indices in a sublist of "N"
        labels = range(1, n_inside + 1)
        N = []
        for i_in in range(n_inside):
            if nlist:
                new_neighbors = neighbors[inside[i_in]]
            else:
                new_neighbors = find_neighbors(faces, inside[i_in])
            new_neighbors = [x for x in new_neighbors if values[x] > thr]
            N.append(new_neighbors.extend([inside[i_in]]))

        # Consolidate labels of connected vertices:
        # Loop through neighbors (lists within "N"),
        # reassigning the labels for the lists until each label's
        # list(s) has a unique set of vertices
        change = 1
        while change > 0:
            change = 0

            # Loop through pairs of inside neighbors
            # and continue if their two labels are different
            #for i in range(n_inside - 1):
            #    for j in range(i + 1, n_inside):
            #        if labels[i] != labels[j]:
            Ipairs = [x for x in list(combos(range(n_inside), 2))
                      if labels[x[0]] != labels[x[1]]]
            for i, j in Ipairs:
                # Assign the two subsets the same label
                # if they share at least one vertex,
                # and continue looping
                if len([x for x in N[i] if x in N[j]]) > 0:
                    labels[i] = labels[j]
                    change = 1

        # The vertex is a simple point if all of its neighbors
        # (if any) share neighbors with each other (one unique label)
        D = []
        if len([D.append(x) for x in labels if x not in D]) == 1:
            sp = 1
        else:
            sp = 0

    return sp

#========================
# Connect anchor vertices
#========================
def connect_anchors(anchors, faces, indices, L, thr):
    """
    Connect anchor vertices in a surface mesh to create a curve.

    ????[Explain HMMF approach]

    Inputs:
    ------
    anchors: list of indices of vertices to connect
    faces: indices of triangular mesh vertices: [#faces x 3] numpy array
    indices: list of indices of vertices
    L: likelihood values: [#vertices in mesh x 1] numpy array
    thr: likelihood threshold

    Parameters:
    ----------
    prob() parameters:
      wt_likelihood: weight influence of likelihood on probability
      wt_neighbors: weight influence of neighbors on probability
    Probability gradient parameters:
      step_size
      mult_init
    Loop parameters:
      n_tries_no_change: #times the loop can continue even without any change
      max_count: maximum #iterations
    Parameters to speed up optimization:
      diff_threshold
      mult_incr
      C_threshold: minimum HMMF value to fix probabilities at very low values

    Output:
    ------
    fundus: [#vertices x 1] numpy array

    Calls:
    -----
    find_neighbors()
    prob()
    simple_test()

    """

    #-----------
    # Parameters
    #-------------------------------------------------------------------------
    # prob() parameters
    wt_likelihood = 1.1  # weight influence of likelihood on probability
    wt_neighbors = 0.4  # weight influence of neighbors on probability

    # Probability gradient parameters
    step_size = 0.05
    mult_init = 0.02

    # Loop parameters
    n_tries_no_change = 3  # #times loop can continue even without any change
    max_count = 350  # maximum number of iterations

    # Parameters to speed up optimization
    diff_thr = 0.0001
    mult_incr = 0.001
#    diff_thr = 0.001
#    mult_incr = 0.01
    C_thr = 0.01  # minimum HMMF value to fix probabilities at low values
    #-------------------------------------------------------------------------

    # Initialize all likelihood values within sulcus as greater than 0.5
    # and less than or equal to 1.0.
    # This is necessary to guarantee correct topology
    L_init = (L + 1.000001) / 2.0
    L_init[L == 0] = 0
    L_init[L_init > 1] = 1

    # Initialize array of connected vertices C
    # with likelihood values greater than thr and a 1 for each anchor vertex
    n_vertices = len(indices)
    Z = np.zeros(len(L))
    C = Z.copy()
    C[L_init > thr] = L_init[L_init > thr]
    C[anchors] = 1

    # Continue if there are at least two candidate vertices
    if sum(C > 0) >= 2:
        print('    {} initial candidate vertices'.format(sum(C > 0)))

        # Find neighbors for each vertex
        load_em = 1
        if load_em:
            import pickle
            load_path = "/drop/yrjo_code_io_data/"
            #pickle.dump(N, open(load_path + "N.p","wb"))
            N = pickle.load(open(load_path + "N.p","rb"))
        else:
            print('    Find neighbors for each vertex...')
            t0 = time()
            N = [[] for x in L]
            for i in indices:
                N[i] = find_neighbors(faces, i)
            print('      ...completed in {0:.2f} seconds'.format(time() - t0))

        # Assign probability values to each vertex
        print('    Assign a probability value to each vertex...')
        t0 = time()
        probs = Z.copy()
        probs[indices] = [prob(wt_likelihood, L[i], wt_neighbors, C[i], C[N[i]])
                          for i in indices]
        print('      ...completed in {0:.2f} seconds'.format(time() - t0))

        # Loop until count reaches max_count or until end_flag equals zero
        # (end_flag is used to allow the loop to continue even if there is
        #  no change for n_tries_no_change times)
        count = 0
        end_flag = 0
        Cnew = C.copy()
        while end_flag < n_tries_no_change and count < max_count:

            # Define a factor to multiply the probability gradient that will
            # increase the time-step size toward the end of the optimization
            mult = mult_init + count * mult_incr

            # Assign each vertex a locally optimal HMMF value (C[i])
            for i in indices:

                # Continue if HMMF value is greater than C_threshold
                # (to fix when at very low values, to speed up optimization)
                if C[i] > C_thr:

                    # Compute the (negative) probability gradient
                    # for the HMMF value
                    q = max([C[i] - step_size, 0])
                    prob_decr = prob(wt_likelihood, L[i],
                                     wt_neighbors, q, C[N[i]])
                    decr = mult * (prob_decr - probs[i]) / step_size

                    # Test to update the HMMF value for positive decrements:
                    if decr > 0:
                        # Update the HMMF value if just above the threshold
                        # such that the decrement makes it cross the threshold,
                        # and the vertex is not an anchor but a "simple point"
                        if C[i] > thr >= C[i] - decr:
                            if i in anchors:
                                update = 0
                            else:
                                Cnew_copy = Cnew.copy()
                                Cnew_copy[i] = C[i] - decr
                                update = simple_test(faces, i, Cnew_copy, thr,
                                                     N, nlist=1)
#                            print('{}: {} - {} = {}'.format(update, C[i],decr,C[i]-decr))
                        # Or update the HMMF value if far from the threshold
                        else:
#                            print('UPDATE1')
                            update = 1
                        # Update the HMMF and probability values
                        if update:
                            """
                            print('Cnew[i]')
                            print(Cnew[i])
                            """
                            decr = 0.10
                            Cnew[i] = max([C[i] - decr, 0])

                            """
                            print(Cnew[i])
                            Cthr = sum(Cnew>thr)
                            C0 = sum(Cnew>0)
                            Cavg = np.mean(Cnew[Cnew>0])
                            print('    {} Cthr {} C0 {} Cavg'.
                                  format(Cthr,C0,Cavg))
            #                            print('probs[i]')
#                            print(probs[i])
                            """
                            probs[i] = prob(wt_likelihood, L[i],
                                            wt_neighbors, Cnew[i], C[N[i]])
#                            print(probs[i])

                    # Test to update the HMMF value for negative decrements:
                    else:
                        # Or if the decrement is negative,
                        # update the HMMF value if so close to the threshold
                        # that the decrement makes it cross the threshold,
                        # and the vertex is a "simple point"
                        if C[i] - decr > thr >= C[i]:
                            Cnew_copy = Cnew.copy()
                            Cnew_copy[i] = C[i] - decr
                            Cnew_copy = 1 - Cnew_copy
                            update = simple_test(faces, i, Cnew_copy, thr,
                                                 N, nlist=1)
#                            print('NEG {}: {} - {} = {}'.format(update, C[i],decr,C[i]-decr))
                        # Or update the HMMF value if far from the threshold
                        else:
#                            print('UPDATE2')
                            update = 1
                        # Update the HMMF and probability values
                        if update:
                            Cnew[i] = min([C[i] - decr, 1])
                            probs[i] = prob(wt_likelihood, L[i],
                                            wt_neighbors, Cnew[i], C[N[i]])

            # Sum the probability values across all vertices
            # and tally the number of HMMF values with probability > thr.
            # After iteration 1, compare current and previous values.
            # If the values are similar, increment end_flag.
            sum_probs = sum(probs)
            n_points = sum(C > thr)
            if count > 0:
                if n_points == n_points_previous:
                    diff_prob = (sum_probs - sum_probs_previous) / n_vertices
                    if diff_prob < diff_thr:
                        end_flag += 1
                        print('    diff_prob: {}, flag: {}, count: {}'.
                              format(diff_prob, end_flag, count))

            Cmin = min(Cnew[Cnew>0])
            print('    {} Cmin with {} vertices...'.format(Cmin, n_points))

            # Reset for next iteration
            sum_probs_previous = sum_probs
            n_points_previous = n_points
            C = Cnew

            count += 1

        return C.tolist()
