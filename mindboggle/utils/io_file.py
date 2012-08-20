#!/usr/bin/python
"""
This Python library reads and writes different file types.

Authors:
Forrest Sheng Bao  .  http://fsbao.net
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

def write_list(filename, List):
    """
    Write a list in to a file, each line of which is a list element.
    """
    Fp = open(filename,'w')
    for Element in List:
        Fp.write(str(Element) + '\n')
    Fp.close()

def load_vertex_neighbor_list(filename):
    """
    Load neighbor list of vertexes from a file.

    Input
    ======
        filename: string
            the file from which neighbor list will be loaded

    """
    NbrLst = []
    Fp = open(filename, 'r')
    lines = Fp.readlines()
    for line in lines:
        NbrLst.append([int(i) for i in line.split()])
    Fp.close()
    return NbrLst

def load_faces_neighbor_list(filename):
    """
    Load neighbor list of faces from a file.

    Input
    ======
        filename: string
            the file from which neighbor list will be loaded

    """
    NbrLst = []
    Fp = open(filename, 'r')
    lines = Fp.readlines()
    for line in lines:
        six = [int(i) for i in line.split()]
        NbrLst.append([six[0:3], six[3:6]])
    Fp.close()
    return NbrLst

def write_line_segments(filename, line_paths):
    """
    Write a curve (e.g., fundus) as curve segments, each line contains a segment.
    consisting of the path from one (e.g., fundus) vertex to the nearest (e.g., fundus) vertex.
    """
    Fp = open(filename, 'w')
    for line_path in line_paths:
        if len(line_path) > 1:
            [Fp.write(str(line_path[i]) + '\t' + str(line_path[i+1]) + '\n') for i in xrange(0,len(line_path)-1)]

    Fp.close()

def write_distance_transform(filename, DT_map):
    """
    Write distance transform map into file, each line for a connected component.
    """

    Fp = open(filename, 'w')
    for DT_map in DT_map:
        [Fp.write(str(dist) + '\t') for dist in DT_map]
        Fp.write('\n')
    Fp.close()

def write_lists(filename, input_lists):
    """
    Output list of lists, each line in the file contains one element
    (also a list) of the top-level list.

    Parameters
    ==========

    input_lists : List of lists (2-D so far)
        Each element of input_lists is a 2-D list of equal or unequal size

    Notes
    ======

    2-D lists are seperated by a delimiter which is 4 dashes now: \n----\n

    """

    Fp = open(filename, 'w')
    for input_list in input_lists:
        for Row in input_list:
            for Element in Row:
                Fp.write(str(Element) + '\t')
            Fp.write('\n')
        Fp.write('----\n')
    Fp.close()

def read_columns(filename, n_columns):
    """
    Read n-column text file.

    Output a list of lists, one per column.
    """

    import re

    Fp = open(filename, 'r')
    lines = Fp.readlines()
    columns = [[] for x in range(n_columns)]
    for line in lines:
        if len(line) > 0:
            row = re.findall(r'\S+', line)
            if len(row) >= n_columns:
                for icolumn in range(n_columns):
                    columns[icolumn].append(row[icolumn])
            else:
                import os
                os.error('The number of columns in {} is less than {}.'.format(
                         filename, n_columns))
    Fp.close()

    return columns

def read_lists(filename):
    """The reverse function of write_lists

    Assume all data are supposed to be integers. Change if floats are needed.

    """
    Fp = open(filename, 'r')
    Lists = [[]]  # initially, there is one list in lists
    while True:
        Line = Fp.readline()
        if len(Line) < 1 :
            Fp.close()
            break
        else:
            if Line == "----\n":
                Lists.append([])
            else:
                Row = [int(i) for i in Line.split()]
                Lists[-1].append(Row)
    Fp.close()

    return Lists[:-1] # because last one is an empty list

def read_float_lists(filename):
    """Read in float type lists

    """
    Fp = open(filename, 'r')
    Lists = [[]]  # initially, there is one list in lists
    while True:
        Line = Fp.readline()
        if len(Line) < 1 :
            Fp.close()
            break
        else:
            if Line == "----\n":
                Lists.append([])
            else:
                Row = [float(i) for i in Line.split()]
                Lists[-1].append(Row)
    Fp.close()

    return Lists[:-1] # because last one is an empty list

def np_loadtxt(filename):
    """
    Load numpy array from text file.
    """

    from numpy import loadtxt

    return loadtxt(filename)

def string_vs_list_check(var):
    """
    Check type to make sure it is a string.

    (if a list, return the first element)
    """

    # Check type:
    if type(var) == str:
        return var
    elif type(var) == list:
        return var[0]
    else:
        import os
        os.error("Check format of " + var)
