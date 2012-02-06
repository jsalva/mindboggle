# This file includes all function for curvauture/convexity-based basin extraction
 
from numpy import mean, std, median, array, zeros, eye, flatnonzero, sign, matrix, zeros_like
import os.path
import cPickle 


#-----------------Begin function definitions------------------------------------------------------------- 

def fcNbrLst(FaceDB, Hemi):
    '''Get a neighbor list of faces, also the vertex not shared with current face
    
    Data structure:
    
    NbrLst: a list of size len(FaceDB)
    NbrLst[i]: two lists of size 3 each. 
    NbrLst[i][0] = [F0, F1, F2]: F0 is the neighbor of face i facing V0 where [V0, V1, V2] is face i. And so forth.  
    NbrLst[i][1] = [V0p, V1p, V2p]: V0p is the vertex of F0 that is not shared with face i        
    
    '''
    
    
    NbrFile = Hemi + '.fc.nbr'

    if os.path.exists(NbrFile):
        #return fileio.loadFcNbrLst(NbrFile)
        print "loading  face nbr lst from:" , NbrFile
        Fp = open(NbrFile, 'r')
        NbrLst = cPickle.load(Fp)
        Fp.close()
        return NbrLst        

    print "calculating face neighbor list"
    
    FaceNo = len(FaceDB)
    
    NbrLst = []
    [NbrLst.append([[-1,-1,-1], [-1,-1,-1]]) for i in xrange(FaceNo)]  
    
    Done =[]
    [Done.append(0) for i in xrange(FaceNo)]
    
    for i in xrange(0, FaceNo):
#    for i in xrange(0, 2600+1):
#        print i
        Face = FaceDB[i]
#        [V0, V1, V2] = Face
#        Found = 0  # if Found  == 1, no need to try other faces
        for j in xrange(i+1, FaceNo):
            AnotherFace = FaceDB[j]

            for Idx in xrange(0,2):
                ChkFc1 = Face[Idx]
                for ChkFc2 in Face[Idx+1:3]:
                    if ChkFc1 in AnotherFace:
                        if ChkFc2 in AnotherFace:
                            NbrID1 = 3 - Face.index(ChkFc1) - Face.index(ChkFc2)   # determine it's F0, F1 or F2.  
                            NbrLst[i][0][NbrID1] = j
                    
                            NbrID2 = 3 - AnotherFace.index(ChkFc1) - AnotherFace.index(ChkFc2)   # determine it's F0, F1 or F2.
                            NbrLst[j][0][NbrID2] = i
                    
#                        Vp1 = AnotherFace[NbrID2]# determine V{0,1,2}p
#                        Vp2 = Face[NbrID1]# determine V{0,1,2}p
                            NbrLst[i][1][NbrID1] = AnotherFace[NbrID2]
                            NbrLst[j][1][NbrID2] = Face[NbrID1]
                    
                            Done[i] += 1
                            Done[j] += 1
                    
            if Done[i] ==3:
                break  # all three neighbors of Face has been found 

    Fp = open(NbrFile, 'w')
    
# Commented 2011-11-27 23:54     
#    for i in xrange(0, len(FaceDB)
#        for j in NbrLst[i]:
#            Fp.write(str(j[0]) + '\t' + str(j[1]) + '\t' + str(j[2]) + '\t')
#        Fp.write('\n')
# End of Commented 2011-11-27 23:54

    cPickle.dump(NbrLst, Fp)

    Fp.close()
                    
    return NbrLst

def vrtxNbrLst(VrtxNo, FaceDB, Hemi):
    """Given the number of vertexes and the list of faces, find the neighbors of each vertex, in list formate. 
    """

    NbrFile = Hemi + '.vrtx.nbr'
        
    if os.path.exists(NbrFile):
        #return fileio.loadVrtxNbrLst(NbrFile) # change to cPickle
        print "Loading vertex nbr lst from:", NbrFile
        Fp = open(NbrFile, 'r')  # need to use cPickle
        NbrLst = cPickle.load(Fp)
        Fp.close()
        return NbrLst
       
    print "Calculating vertex neighbor list"
    
    NbrLst = [[] for i in xrange(0, VrtxNo)]
        
    for Face in FaceDB:
        [V0, V1, V2] = Face
        
        if not V1 in NbrLst[V0]:
            NbrLst[V0].append(V1)
        if not V2 in NbrLst[V0]:
            NbrLst[V0].append(V2)

        if not V0 in NbrLst[V1]:
            NbrLst[V1].append(V0)
        if not V2 in NbrLst[V1]:
            NbrLst[V1].append(V2) 

        if not V0 in NbrLst[V2]:
            NbrLst[V2].append(V1)
        if not V1 in NbrLst[V2]:
            NbrLst[V2].append(V1)
    
    Fp = open(NbrFile, 'w')  # need to use cPickle

# Commented 2011-11-27 23:54    
#    for i in xrange(0, VrtxNo):
#        [Fp.write(str(Vrtx) + '\t') for Vrtx in NbrLst[i]]
#        Fp.write('\n')    
# End of Commented 2011-11-27 23:54
    cPickle.dump(NbrLst, Fp)

    Fp.close()

    return NbrLst

def compnent(FaceDB, Basin, NbrLst, PrefixBasin):
    '''Get connected component, in each of all basins, represented as faces and vertex clouds
    
    Parameters
    -----------
    
    NbrLst : list
        neighbor list of faces, NOT VERTEXES
    
    '''
    
    FcCmpntFile = PrefixBasin + '.cmpnt.face' 
    VrtxCmpntFile = PrefixBasin + '.cmpnt.vrtx'
        
    if os.path.exists(FcCmpntFile) and os.path.exists(VrtxCmpntFile):
#        return fileio.loadCmpnt(FcCmpntFile), fileio.loadCmpnt(VrtxCmpntFile)
        print "Loading Face Components from:", FcCmpntFile
        Fp = open(FcCmpntFile, 'r')
        FcCmpnt = cPickle.load(Fp)
        Fp.close()
        
        print "Loading Vertex Components from:", VrtxCmpntFile
        Fp = open(VrtxCmpntFile, 'r')
        VrtxCmpnt = cPickle.load(Fp)
        Fp.close()
        return FcCmpnt, VrtxCmpnt
        
    print "calculating face and vertex components"
    
    Visited = [False for i in xrange(0, len(Basin))]
    
    FcCmpnt, VrtxCmpnt = [], [] 
    
    while not allTrue(Visited):
        Seed = dfsSeed(Visited, Basin)# first basin face that is not True in Visited
#        print Seed
        Visited, FcMbr, VrtxMbr = dfs(Seed, Basin, Visited, NbrLst, FaceDB)# DFS to fine all connected members from the Seed
        FcCmpnt.append(FcMbr)
        VrtxCmpnt.append(VrtxMbr)
            
#    fileio.writeCmpnt(FcCmpnt, FcCmpntFile)
#    fileio.writeCmpnt(VrtxCmpnt, VrtxCmpntFile)
    Fp = open(FcCmpntFile, 'w')
    cPickle.dump(FcCmpnt, Fp)
    Fp.close()
    Fp = open(VrtxCmpntFile, 'w')
    cPickle.dump(VrtxCmpnt, Fp)
    Fp.close()
                
    return FcCmpnt, VrtxCmpnt

def judgeFace1(FaceID, FaceDB, CurvatureDB, Threshold = 0):
    """Check whether a face satisfies the zero-order criterion
    
    If all three vertexes of a face have negative curvature, return True. O/w, False.
    
    Input
    ======
    
        FaceID: integer
                the ID of a face, indexing from 0
        
        FaceDB: list
                len(FaceDB) == number of faces in the hemisphere
                FaceDB[i]: a 1-D list of the IDs of three vertexes that consist of the i-th face
                
        CurvatureDB: list
                len(CurvatureDB) == number of vertexes in the hemisphere
                CurvatureDB[i]: integer, the curvature of the i-th vertex 
    
    """
    
    [V0, V1, V2] = FaceDB[FaceID]
    if (CurvatureDB[V0] > Threshold) and (CurvatureDB[V1] > Threshold) and (CurvatureDB[V2] > Threshold):
        return True
    else:
        return False

def sulciCover(SulciList, FaceDB):
    '''Add a polygon cover for an extracted sulcus
    '''
    pass

def basin(FaceDB, CurvatureDB, Prefix, Threshold = 0):
    '''Given a list of faces and per-vertex curvature value, return a list of faces comprising basins
    '''
    Basin = []
    Left = []
    for FaceID in xrange(0, len(FaceDB)):
        if judgeFace1(FaceID, FaceDB, CurvatureDB, Threshold = Threshold):
            Basin.append(FaceID)
        else:
            Left.append(FaceID)
            
#    BasinFile = Prefix + '.basin'   
#    fileio.writeList(BasinFile, Basin)
#    GyriFile = Prefix + '.gyri'   
#    fileio.writeList(GyriFile, Left)
    
    return Basin, Left

def allTrue(List):
    '''Check whether a logical list contains non-True elements. 
    '''    
    for Bool in List:
        if not Bool:
            return False
    return True

def dfsSeed(Visited, Basin):
    '''Given a list of faces comprising the basins, find a face that has not been visited which will be used as the seeding point for DFS.
    '''
    for i in xrange(0, len(Visited)):
        if not Visited[i]:
            return Basin[i]
             
def dfs(Seed, Basin, Visited, NbrLst, FaceDB):
    '''Return all members (faces and vertexes) of the connected component that can be found by DFS from a given seed point
    
    Parameters
    -----------
    
    NbrLst : list
        neighbor list of faces, NOT VERTEXES    
     
    '''
    Queue = [Seed]
    FcMbr = []  # members that are faces of this connected component
    VrtxMbr = [] # members that are vertex of this connected component
    while Queue != []:
#        print Queue
        Seed = Queue.pop()
        if Seed in Basin:
            if not Visited[Basin.index(Seed)]:
                Visited[Basin.index(Seed)] = True
                FcMbr.append(Seed)
                for Vrtx in FaceDB[Seed]:
                    if not (Vrtx in VrtxMbr):
                        VrtxMbr.append(Vrtx)
                Queue += NbrLst[Seed][0]
            
    return Visited, FcMbr, VrtxMbr

def pmtx(Adj):
    '''Print a matrix as shown in MATLAB stdio
    '''
    
    for j in xrange(0,25):
        print j,
    print '\n'
     
    for i in xrange(0, 25):
        print i,
        for j in xrange(0, 25):
            print Adj[i,j],
        print '\n'    

def all_same(items):
    return all(x == items[0] for x in items)

def pits(CurvDB, VrtxNbrLst, Threshold = 0):  # activated Forest 2011-05-30 1:22
    '''Watershed algorithm to find pits (lowest point in each pond) and pond hierarchies.
     
    Docs for this function is detailed in GDoc
     
    '''
    
    print "Extracting pits"
    
    S, P, Child, M, B, End, L  = [], [], {}, -1, [], {}, 10
    C = [-1 for i in xrange(0, len(VrtxNbrLst))]
    Curv=dict([(i, CurvDB[i]) for i in xrange(0, len(CurvDB))])
    for Vrtx, Cvtr in sorted(Curv.iteritems(), key=lambda (k,v): (v,k)):
        S.append(Vrtx)
    
    while len(S) >0 and L> Threshold:  # changed from L > 0 to L > Threshold, Forrest 2011- 06-10 08:25
        V = S.pop()
        L = CurvDB[V]
        P.append(V)
        Nbrs = list(set(VrtxNbrLst[V]))
        
        WetNbr = []
        NbrCmpnt = []
        for Nbr in Nbrs:
            if Nbr in P:
                WetNbr.append(Nbr)
                if C[Nbr] != -1:
                    NbrCmpnt.append(C[Nbr])
        
        if len(WetNbr) == 1: # if the vetex has one neighbor that is already wet     
            [Nbr] = WetNbr
            if End[C[Nbr]]:
                C[V] = Child[C[Nbr]]
            else:
                C[V] = C[Nbr]
#                print C[Nbr], "==>", C[V] 
        elif len(WetNbr) >1 and all_same(NbrCmpnt): # if the vertex has more than one neighbors which are in the same component
            if End[NbrCmpnt[0]]:
                C[V] = Child[NbrCmpnt[0]]
            else:
                C[V] = NbrCmpnt[0]
        elif len(WetNbr) >1 and not all_same(NbrCmpnt):  # if the vertex has more than one neighbors which are NOT in the same component
            M += 1
            C[V] = M
            for Nbr in WetNbr:
                Child[C[Nbr]] = M
                End[C[Nbr]] = True
            End[M] = False
        else:
            M += 1
#            if L < Threshold:  # I forgot why i wrote selection structure. But it seems to be UNecessary now. Forrest 2011-06-10 06:25 
#                B.append(V)
            B.append(V)
            End[M] = False
            C[V] = M
    return B, C, Child

def getBasin(MapBasin, mapExtract, Mesh, PrefixBasin, PrefixExtract, Mesh2, Threshold = 0):
    '''Load curvature and surface file and output sulci into SulciFile
    
    This is a general framework for feature extraction
    
    Input
    =====   
        MapBasin: list
            a per-vertex map, e.g., curvature map, for extract sulcal basin

        mapExtract: list
            a per-vertex map, e.g., travel depth map, for extract PITS from the surface
            
        Mesh: 2-tuple of lists
            the first list has coordinates of vertexes while the second defines triangles on the mesh
            This is a mandatory surface, normally a non-inflated surface. 
            
        Mesh2: 2-tuple of lists
            the first list has coordinates of vertexes while the second defines triangles on the mesh
            This is an optional surface, normally an inflated surface.
            Default = []

        FileBasin: string
            path to the per-vertex file that is used to threshold the surface
        
        FilePits: string
            path to the per-vertex file that is used to extract pits
            
        SurfFile: string
            path to a surface file

        SurfFile2: string
            path to the 2nd surface file
            
        Threshold: integer
            the value to threshold the surface

    '''
      
    [Vertexes, Face] = Mesh
    if Mesh2 != []:
        [Vertexes2, Face2] = Mesh2
        
    Basin, Gyri = basin(Face, MapBasin, PrefixBasin, Threshold = Threshold)
    # End of 2nd curvature file is only used to provide POINTDATA but not to threshold the surface  Forrest 2011-10-21
        
    BasinFile = PrefixBasin + '.basin'
    GyriFile = PrefixBasin + '.gyri'
    
    LastSlash=len(PrefixBasin)-PrefixBasin[::-1].find('/')
    Hemi =  PrefixBasin[:PrefixBasin[LastSlash:].find('.')+LastSlash]# path up to which hemisphere, e.g., /home/data/lh

    VrtxNbr = vrtxNbrLst(len(Vertexes), Face, Hemi)
    FcNbr   = fcNbrLst(Face, Hemi)
    FcCmpnt, VrtxCmpnt = compnent(Face, Basin, FcNbr, PrefixBasin)
    
    # write component ID as LUT into basin file. 
    CmpntLUT = [-1 for i in xrange(0, len(MapBasin))]
    for CmpntID, Cmpnt in enumerate(VrtxCmpnt):
        for Vrtx in Cmpnt:
            CmpntLUT[Vrtx] = CmpntID
    # end of write component ID as LUT into basin file.

    Pits, Parts, Child = pits(mapExtract, VrtxNbr, Threshold = 0.5 - mean(MapBasin))

#    FPits = open(PrefixExtract + '.pits', 'w')
#    cPickle.dump(Pits, FPits)
#    FPits.close()
#    PitsFile = PrefixExtract + '.pits'
#    fileio.writeList(PitsFile, Pits)

    # dump basin
    print "writing basins into VTK files"
## commented to use pyvtk API's to output, Forrest 2011-01-08 
#    VTKFile = BasinFile + '.' + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'
#    libvtk.fcLst2VTK(VTKFile, SurfFile, BasinFile, LUT=[mapThreshold, Parts, CmpntLUT], LUTname=['PerVertex', 'hierarchy', 'CmpntID'])
## end of commented to use pyvtk API's to output, Forrest 2011-01-08 

# basin pyvtk output
    from pyvtk import PolyData, PointData, Scalars, VtkData
    Face = [map(int,i) for i in Face]# this is a temporal fix. It won't cause precision problem because sys.maxint is 10^18.
    Vertexes = map(list, Vertexes)
    Structure = PolyData(points=Vertexes, polygons=[Face[Idx] for Idx in Basin])
    Pointdata = PointData(Scalars(MapBasin,name='PerVertex'), Scalars(CmpntLUT,name='CmpntID'),\
                          Scalars(Parts,name='hierarchy'))
    VtkData(Structure, Pointdata).tofile(PrefixBasin + '.basin.vtk','ascii')
# end of basin pyvtk output

## commented to use pyvtk API's to output, Forrest 2011-01-08    
#    VTKFile = GyriFile + '.' + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'
#    libvtk.fcLst2VTK(VTKFile, SurfFile, GyriFile)
## end of commented to use pyvtk API's to output, Forrest 2011-01-08
    
    VtkData(PolyData(points=Vertexes, polygons=[Face[Idx] for Idx in Gyri])).tofile(PrefixBasin + '.gyri.vtk','ascii')
            
    if Mesh2 != []: 
        VtkData(PolyData(points=Vertexes2, polygons=[Face2[Idx] for Idx in Basin])).tofile(PrefixBasin + '.basin.2nd.vtk','ascii')
        VtkData(PolyData(points=Vertexes2, polygons=[Face2[Idx] for Idx in Gyri])).tofile(PrefixBasin + '.gyri.2nd.vtk','ascii')
## commented to use pyVTK         
#        VTKFile = BasinFile + "." + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'
#        libvtk.fcLst2VTK(VTKFile, SurfFile2, BasinFile, LUT=[mapThreshold, Parts, CmpntLUT], LUTname=['PerVertex', 'hierarchy', 'CmpntID'])
#    
#        VTKFile = GyriFile + '.' + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'
#        libvtk.fcLst2VTK(VTKFile, SurfFile2, GyriFile)
## end of commented to use pyvtk
        
    # End of dump basin

    # write Pits
    print "writing pits into VTK files"
## commented to use pyvtk API's to output, Forrest 2011-01-08
#    VTKFile = PitsFile + "." + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'  
#    libvtk.vrtxLst2VTK(VTKFile, SurfFile, PitsFile)
## commented to use pyvtk API's to output, Forrest 2011-01-08

    VtkData(PolyData(points=Vertexes, vertices=Pits)).tofile(PrefixExtract + '.pits.vtk','ascii')
    
## a testing code to write pits and basin all together
 
## end of a testing code to write pits and basin all together

    if Mesh2 != []:
        VtkData(PolyData(points=Vertexes2, vertices=Pits)).tofile(PrefixExtract + '.pits.2nd.vtk','ascii')
#        VTKFile = PitsFile + "." + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'
#        libvtk.vrtxLst2VTK(VTKFile, SurfFile2, PitsFile)
    # End of write pits
    
    # output tree hierarchies of basal components
    print "writing hierarchies of basal components"
    WetFile = PrefixExtract + '.pits.hier'
    WetP = open(WetFile,'w')
    for LowComp, HighComp in Child.iteritems():
        WetP.write(str(LowComp) + '\t' + str(HighComp) + '\n')
    WetP.close()
    # end of output tree hierarchies of basal components
    
# End of Get pits Forrest 2011-05-30 10:16

# a monolithic code output each component
#    Dic = {}
#    for CID, Cmpnt in enumerate(FcCmpnt):
#        Dic[CID] = len(Cmpnt)
#    
#    #Dic = sorted(Dic.iteritems(), key= lambda (k,v,) : (v,k))
#    Counter = 1
#    for CID, Size in sorted(Dic.iteritems(), key=lambda (k,v): (v,k)):  
##        print Size
#        Rank = len(FcCmpnt) - Counter +1
#        Fp = open(BasinFile + '.' + SurfFile[-1*SurfFile[::-1].find('.'):] + '.' + str(Rank) +'-th.vtk','w')
#        Vertex, Face = fileio.readSurf(SurfFile)
#        FundiList = FcCmpnt[CID]
#        libvtk.wrtFcFtr(Fp, Vertex, Face, FundiList)
#        Fp.close()
#        Counter += 1
    
# a monolithic code output each component


           
#---------------End of function definitions---------------------------------------------------------------  
