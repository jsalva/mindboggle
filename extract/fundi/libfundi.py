# This file contains all functions to extract fundus curves from per-vertex-value (e.g., curvature) map
# Last updated: 2011-08-09 Forrest Sheng Bao 

import readFreeSurfer as rfs
import libvtk, fileio, libbasin
import libfundifc as libskel
from numpy import mean, std, abs, matrix, zeros, flatnonzero, sign, array, argmin
import sys
from math import sqrt
sys.setrecursionlimit(30000)

def dist(VrtxCmpnts, VrtxNbrLst, CurvatureDB, DistFile=''): 
    '''Compute/load weighted adjacency matrixes of all connected sulcal components. 
        
    Parameters
    ===========
    
    Adj : list of list of integers/doubles
        adjacency matrix of a connected component
        
    Dist : list of list of integers 
        Dist[i][j] is the shortest distance between vertex i and vertex j
        Dist[i] is the Adj of the i-th connected component
        
    DistFile : string
        A path to filed extracted distance matrix
        
    CID : integer
        a component ID
    
    Cmpnt : list of integers
        global vertex IDs of all vertexes in a connected sulcal component 
        
    VrtxIdx : integer
        local (inner-componnent) ID of a vertex
         
    NbrIdx : integer
        local (inner-componnent) ID of a vertex's Nbr 
        
    CurvatureDB : list of doubles
            each element is the curvature value of a vertex 
    
    Notes
    =======
    
    Before HBM, this function uses graph power to weigh links between nodes. 
    Now (2011-07-17) it uses curvature to weigh. 
      
    '''    
   
    print "computing/loading weighted adjacency matrixes"
 
#    if DistFile != '' and os.path.exists(DistFile):
#        return fileio.readFltLsts(DistFile)
    # the block above is disabled because now computing adjacency matrix isn't time-consuming.
    # Forrest 2011-07-17
    
    Dists = [] 
    for CID, Cmpnt in enumerate(VrtxCmpnts):
        Num = len(Cmpnt)
#        print "\t component", CID+1, ": size", Num
        if Num > 1:
            
            Adj = matrix(zeros((Num, Num)))
            for VrtxIdx, Vrtx in enumerate(Cmpnt):
                for Nbr in VrtxNbrLst[Vrtx]:
                    if Nbr in Cmpnt:
                        NbrIdx = Cmpnt.index(Nbr)                        
                        LinkWeight = -1. * (CurvatureDB[Vrtx]  + CurvatureDB[Nbr]) 
                         
                        # add a double check here to ensure the matrix is diagonally symmetric
                        if   Adj[VrtxIdx, NbrIdx] == 0:
                            Adj[VrtxIdx, NbrIdx] = LinkWeight # 
                            # Adj[NbrIdx, VrtxIdx] = LinkWeight # write only once for checking later
                        elif Adj[VrtxIdx, NbrIdx] != 0 and Adj[VrtxIdx, NbrIdx] != LinkWeight:
                            print "error, Adj is not symmetric."
                        elif Adj[NbrIdx, VrtxIdx] != 0 and Adj[NbrIdx, VrtxIdx] != LinkWeight:
                            print "error, Adj is not symmetric."
             
            #Dist = [[int(i) for i in Row] for Row in list(array(Adj))]
            Dist = [[i for i in Row] for Row in list(array(Adj))]
#            for Row in list(array(Dist)):
#                for Element in Row:
#                    print Element
        
        else:
            Dist = [[1]]            
            
        Dists.append(list(Dist)) # I forgot why this line is needed Forrest 2011-07-17
        
#    if DistFile != '':
#        fileio.wrtLists(DistFile, Dists)
    return Dists

def downsample(SpecialAndRing, Special, VrtxCmpnts, NbrLst, Prob):
    '''Randomly delete vertexes on original mesh by probability Prob. 
    
    
    Parameters 
    =============
    
    SpecialAndRing: list of integers
        global IDs of special and 0-curvature vertexes
        It can be the same as Special, which means no vertexes other than 
        Special is considered must have in downsampled mesh
    
    Special : list of integers
        special vertexes that have to be in downsampled mesh. 
    
    VrtxCmpnts : list of lists of integers
        VrtxCmpnts[i] is a list of vertexes in the i-th connected component
        
    NbrLst : list of lists of integers
            neighbor list of vertexes
    
    Prob : float 
        The probability \in [0, 1] that a vertex is to be KEPT. 
        If it is 1, remove nothing.
        If it is 0, remove ALL. 
    
    N : list of lists of integers
        new vertexes to be left after downsampling
        
    L : list of lists of integers
        neighbor list of vertexes after downsampling
    
    Vrtx : integer
        a vertex id
    
    MinusVrtx : integer
        number of vertexes removed in mesh downsampling
    
    MinusEdge : integer
        number of edges removed in mesh downsampling
    
    Keep : list of integers
        vertexes to be kept 
    
    SpecialGroup: list of list of integers 
        each element is a list of Special vertexes in each connected component
    
    SpecialInThisGroup : list of integers
        a list of Special vertexes ID, used to represent all Special vertexes in a running component
    
    '''
    
    print "Downsampling mesh..."
    
    import random
    
    N = []
    L = [[] for i in xrange(0,len(NbrLst))]
    SpecialGroup = []
        

    for Cmpnt in VrtxCmpnts:
        for Vrtx in Cmpnt:
            L[Vrtx] = NbrLst[Vrtx]

    for CmpntID, Cmpnt in enumerate(VrtxCmpnts): # for each component
        MinusVrtx, MinusEdge = 0, 0
        NumMusthave = 0
        Keep = []
        SpecialInThisGroup = []
        for Vrtx in Cmpnt:   # for each vertex in the component
            if Vrtx in SpecialAndRing:
#                N[-1].append(Vrtx)
                NumMusthave += 1
                if Vrtx in Special:
                    SpecialInThisGroup.append(Vrtx)
                if not Vrtx in Keep:
                    Keep.append(Vrtx)
            elif not Vrtx in Keep: # The purpose of not Vrtx in Keep is to avoid removing vertexes that should not be removed, such as Musthave.
                if Prob <= random.random():  # REMOVE Vrtx
                    MinusVrtx += 1
                    for Nbr in NbrLst[Vrtx]:
                        if Nbr in Cmpnt:
                            # step 1: put Vrtx's neighbors, which are ALSO in Cmpnt, into N and thus delete Vrtx
                            if not Nbr in Keep:
                                Keep.append(Nbr) # yield more vertexes and edges removed
                            # step 2: delete edges ending at Vrtx
                            if Vrtx in L[Nbr]:
        #                        N[-1].append(Nbr) # yield less vertexes and edges removed
        #                        Left.append(Nbr)  # yield less vertexes and edges removed
                                L[Nbr].remove(Vrtx)
                                MinusEdge += 1
                    L[Vrtx] = [] # Vrtx has no neighbor now
                else: # KEEP this vertex
                    Keep.append(Vrtx)
                    
        N.append(Keep)
        SpecialGroup.append(SpecialInThisGroup)
        
#        if NumMusthave != len(SpecialInThisGroup):
#            print "more vertex in musthave\n"
#            exit(0)
#        print "\t component", CmpntID+1, ":", NumMusthave, "Specials. ", "Vtx #:", len(Cmpnt), "-", MinusVrtx,  "=>", len(Keep)

    return N, L, SpecialGroup

def prune(Path, Degree, TreeNbr, Terminal, Branching, Special, VrtxCmpnt):
    '''Prune an MST by deleting edges
    
    Parameters
    ===========
    Path : list of lists (2-tuple) of integers
        Each element of *Path* is a list of the two terminals of each pair of connected fundus vertexes
        Vertexes indexed LOCALLY, i.e., they are referred by their ID in currenct component   
    
    Degree : list of integers 
        Degrees of nodes in a component
        
    TreeNbr : list of list of integers
        Each element is a list of neighbors of a node. All LOCAL IDs.
        
    Terminal : list of integers
        Local IDs of nodes that are terminals. 
        
    Branching : list of integers
        Local IDs of nodes that are branching nodes. 
    
    Special : list of integers
        Local IDs of nodes that are special vertexes connected by MST 
        
    Trace : list of 2-tuples of integers
        Edges that are visited along the Path from one node to another
        
    Visited : list of integers
        Nodes that are visited along the Path from one node to another
        
    At : integer
        a node
        
    Previous : integer
        a node
        
    VrtxCmpnt: list of integers
        A list of vertexes in this component in global ID
        
    Returns
    ========
    Path : list of lists (2-tuple) of integers
        Each element of *Path* is a list of the two terminals of each pair of connected fundus vertexes
        Vertexes indexed LOCALLY, i.e., they are referred by their ID in currenct component
        This one is reduced 

    Note
    ======
    
    2011-10-04 Since we only want links between special vertexes, all links starting from
               a terminal must be removed. Only links between special vertexes are left. 
        
    ''' 
#    print "\t # of terminals:", len(Terminal)
#    print "\t\t Path:", Path
#    print "\t\t Special:", Special
    NodeColor = {} # to visualize visited nodes of different types
#    print "\t in prune(), # of specials", len(Special)
    for T in Terminal:
#        print "\t\t\t Tracing begins at ", T, 
        if len(Branching) < 1:
#            print "\t\t stop pruning at ", Terminal.index(T), "-th Terminal"
            break
        
        if T in Special:  # Forrest 2011-10-04   
            continue
        
        Trace= [ ]# store the trace visited from a terminal node to a branching node
        Visited = [] # store nodes that have been visited  
        At = T # the node of current position in tracing
        NodeColor[VrtxCmpnt[T]] = 1  
        while(not At in Branching and not At in Special):
            Visited.append(At)
            for Nbr in TreeNbr[At]:
                if not Nbr in Visited: # search toward the mainstream 
                    Trace.append((Nbr, At))
                    Previous = At  # the node visited before At in tracing
                    At = Nbr
                    break
#        print "\t\t\tTrace ", Trace
        # after the while loop, At stops at a branching node.
        # block below deactivated Forrest 2011-10-04 to remove all links from Terminal
        '''
        if not At in Special:   
            NodeColor[VrtxCmpnt[At]] = 2 # just a regular branching node 
            TreeNbr[At].remove(Previous)     
            for Pair in Trace:
                (Src, Dst) = Pair
                if Pair in Path:
                    Path.remove(Pair)
                else:  # it is possible the order of nodes is reversed in Path
                    Path.remove((Dst, Src)) 
                    
            Degree[At] -= 1
            if Degree[At] < 3:
                Branching.remove(At)
        elif At in Special and At in Branching: 
            NodeColor[VrtxCmpnt[At]] = 5 
        elif At in Special and At in Terminal:  
            NodeColor[VrtxCmpnt[At]] = 4
        else: # Special only
            NodeColor[VrtxCmpnt[At]] = 3
        '''    

        # Delete all links from non-special terminals Forrest 2011-10-04             
        NodeColor[VrtxCmpnt[At]] = 2 # just a regular branching node 
        TreeNbr[At].remove(Previous)     
        for Pair in Trace:
            (Src, Dst) = Pair
            if Pair in Path:
                Path.remove(Pair)
            else:  # it is possible the order of nodes is reversed in Path
                Path.remove((Dst, Src)) 

        if At in Branching:      # may stop at a Special-only node              
            Degree[At] -= 1
            if Degree[At] < 3:
                Branching.remove(At)
        # End of Delete all links from non-special terminals Forrest 2011-10-04
              
#    print "\t\t Final path: ", Path
    return Path, NodeColor

def nonZeroLn(List): # activated 2011-05-25 19:14
    '''Given a 2-D list, return number of 1-D lists that contains nonzero elements
    '''
    Counter = 0
    for L in List:
        for E in L:
            if E != 0:
                Counter += 1
                break
            
    return Counter

class Prim:  # modified from the code without license @http://hurring.com/scott/code/python/mst_prim/v0.1/mst_prim.py 
    INFINITY = 2**8  # this is large enough for current problem size
    vertices = 0
    
    def __init__(self, A, r):
        """
        Prepare the inputs for mst_prime
        """
        self.vertices = A[0].__len__();
        self.nonzeros = nonZeroLn(A)   # a new member, activated Forrest 2011-05-25 18:56
        self.init_adjacency(A)
        self.remove_route(A, r)
        self.degree = [0 for i in xrange(0, len(A))] # a new member , activated Forrest 2011-05-27 20:31
        self.tree_nbr= [[] for i in xrange(0, len(A))] # record nbrs of each node, Forrest 2011-09-24
    
    def mst_prim(self, A, w, i, path, degree, tree_nbr):
        """
        'A' is the adjacency matrix
        'w' is the list of all connected vertices (in order of discovery)
        'path' is a list of tuples showing (from, to)
        i : the ID of the connected component   # Forrest 2011-05-26 00:31
        """
       
        # Stop when we've added all nodes to the path
#        if (w.__len__() == self.vertices):  # old line.  But if some nodes are not connected, it goes into infinite recursion. Deactivated Forrest 2011-05-25 19:39
        if (w.__len__() == self.nonzeros):  # new way, activated Forrest 2011-05-25 19:42
            return (A, w, path, degree, tree_nbr)
        # Find minimum path coming OUT of the known vertexes            
        (vfrom, vto, vcost) = self.find_min(A, w)
        
        # increase the degreee for vertexes vfrom and vto
        degree[vfrom] += 1
        degree[vto] += 1
        
        # update tree_nbr list for vfrom and vto Forrest 2011-09-24 10:55
        tree_nbr[vfrom].append(vto)
        tree_nbr[vto].append(vfrom)
        
        # Mark down this vertex as being a part of the MST path
        w.append(vto)
        #path.append((vfrom,vto,vcost, i)) # commented, Forrest 2011-09-24
        path.append((vfrom, vto))
        
        self.remove_route(A, vto)
        
        return self.mst_prim(A, w, i, path, degree, tree_nbr)
    
    
    def init_adjacency(self, A):
        """
        Initialize adjacency list - set 0 = INFINITY
        """
        for i in range(0, self.vertices):
            for j in range(0, self.vertices):
                if A[i][j] == 0:
                    A[i][j] = 2**8
        
    def remove_route(self, A, v):
        """
        Once we've added a node to our path, set all routes
        to this node equal to INFINITY - to prevent loops
        """
        for i in range(0, self.vertices):
            A[i][v] = self.INFINITY
    
    def find_min(self, A, w):
        """
        Find the cheapest connection we can possibly make,
        given the partially-built MST 'w'
        'vfrom' vertex to connect from
        'vto' vertex to connect to
        'vcost' cost of connection
        """
        vcost = self.INFINITY
        vto = vfrom = -1
        for v in w:
            # Get array offset of minimum  of this vertex
            i = argmin(A[v])
            if A[v][i] < vcost:
                vcost = A[v][i]
                vto = i
                vfrom = v
        return (vfrom, vto, vcost)

    # The end of Class Prim


def fundiLength(Vrtx, Path):
    '''Estimate a fundiLength in accumulation of Euclidean distance of a given Path
    
    Notes
    ======
    
    Now since a path has only two nodes, it is very easy that we don't need to accumulate. 
     
    '''
    Length = 0
    for i in xrange(0, len(Path)-1):
        j = i+1 
        Length += sqrt( sum([ (Vrtx[i][k]-Vrtx[j][k])**2 for k in [0,1,2]]))
    
    return Length    

def mst(Adjs, VrtxCmpnts, SpecialGroup, NbrLst, Coordinates):
    '''Using Prim algorithm to connect nodes (including fundus vertexes) within each connected component
    
    Parameters
    ==========
    
    VrtxCmpnts : list of lists of integers
        VrtxCmpnts[i] is a list of vertexes in the i-th connected component
    
    SpecialGroup : list of lists of integers
        Special[i] is a list of Special vertexes in the i-th connected component
        Special[i] can be empty 
    
    NbrLst : list of list of integers
            neighbor list of vertexes
    
    Path : list of lists (2-tuple) of integers
        Each element of *Path* is a list of the two terminals of each pair of connected fundus vertexes
        Vertexes indexed LOCALLY, i.e., they are referred by their ID in currenct component  
    
    Adj : list of lists of integers
        adjacency matrix of fundus vertexes in one connected component
        
    Adjs : list of Adj's
        adjacency matrixes of all fundus vertexes on one hemisphere
        
    Coordinates : list of 3-tuples
        Coordinates of vertexes in GLOBAL index. 
        
    W : list of integers
        vertexes taht are already connected in Prim algorithm
        It has no use.  
        
    Segs : list of lists (2-tuple) of integers
        Vertexes indexed GLOBALLY, i.e., they are referred by their ID in the entire hemisphere
        
    Degree : list of integers 
        Degrees of nodes in a component
        
    TreeNbr : list of list of integers
        Each element is a list of neighbors of a node. All LOCAL IDs.
        
    Terminal : list of integers
        Local IDs of nodes that are terminals. 
        
    Branching : list of integers
        Local IDs of nodes that are branching nodes. 
        
    FundusLen : dictionary of integers
        Each key is a GLOBAL vertex ID. 
        The value of each key is the length of the fundus that the key is part of.
        
    FundusID : dictionary of integers
        Each key is a GLOBAL vertex ID. 
        The value of each key is the ID (equal to component ID) of the fundus that the key is part of.
      
    '''
    Segs = []
    Color = {}
    FundusLen, FundusID = {}, {}
    if len(Adjs) != len(VrtxCmpnts):
        print "Error, Adjs is not as long as VrtxCmpnts"
        exit()
    else:
        print "Connecting fundus vertexes in", len(VrtxCmpnts), "connected components."
        for i in xrange(0, len(Adjs)):  # For each component in the hemisphere
            print "\t MST on component",i+1, ",",
            if len(SpecialGroup[i]) < 2 :  # This compnent has no more than two vertexes to be connected
                print "\t Skipped. Too few Special vertexes."
            elif len(VrtxCmpnts[i]) >200: # For quick debugging ONLY. Forrest 2011-09-29 16:56 
                print "\t Skipped. Too many vertexes (all kinds). "
            else:
#                print "\t # of special points", len(SpecialGroup[i]) , 
                Root = VrtxCmpnts[i].index(SpecialGroup[i][0])  # always start MST from a special vertex 
#                Adj = Adjs[i]              # avoid creating new variable to speed up
#                Cmpnt = VrtxCmpnts[i]     # avoid creating new variable to speed up
                Num = len(Adjs[i])
                if Num > 1: # the Num < 1000 is for fast debugging  
                    M = Prim(Adjs[i], Root)  # starting from the Root 
                    (Adj, W, Path, Degree, TreeNbr) = M.mst_prim(Adjs[i], [Root], i, [], M.degree, M.tree_nbr) # starting from the Root
#                    Seg = [[VrtxCmpnts[i][Idx] for Idx in Pair] for Pair in Path]  # The Idx is LOCAL (i.e., within the connected component) index of a vertex.
                    
                    # pruning the MST Forrest 2011-09-24
                    Terminal, Branching =[], []
                    for Vrtx in xrange(0,Num):
                        if Degree[Vrtx] ==1:
                            Terminal.append(Vrtx)
                        elif Degree[Vrtx] > 2:
                            Branching.append(Vrtx)
                    
                    Special = [VrtxCmpnts[i].index(Vrtx) for Vrtx in SpecialGroup[i]] # converting global ID to local ID
                    Path, NodeColor = prune(Path, Degree, TreeNbr, Terminal, Branching, Special, VrtxCmpnts[i])
                    print len(Path), "links after pruning."
                    Length_of_fundus = fundiLength(Coordinates, Path)  # Add, Forrest 2011-11-01
                    
                    for Pair in Path:                    
#                        (Src, Dst, Cost, CID) = Pair # commented, Forrest 2011-09-24
                        (Src, Dst) = Pair # Forrest 2011-09-24
#                        Segs.append( [VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i] )
                        # pruning heuristic 1
#                        if Degree[Src] > 2 and Degree[Dst] ==1 and Cost < 4:
                            #Degree[Src] -= 1
#                        elif Degree[Dst] > 2 and Degree[Src] ==1  and Cost < 4:
                            #Degree[Dst] -= 1
                        # end of pruning heuristic 1
                        # pruning heuristic 2
#                        elif Degree[Src] ==1:
#                            OtherPairs, OtherTerminals = otherPaths(Dst, Pair, Degree[Dst], Path)
#                            Judge = [Cost < 1/3*OtherPair[2] for OtherPair in OtherPairs]
#                            Good = True
#                            for J in Judge:
#                                if J:  # if smaller do this. 
#                                    Good = False
#                                    Degree[Dst] -= 1
#                                    break
#                            if Good : # is no such a thing, do this:
#                                Segs.append( [VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i] ) # here local indexes are converted into global indexes
#                        elif Degree[Dst] ==1:
#                            OtherPairs, OtherTerminals = otherPaths(Src, Pair, Degree[Src], Path)
#                            Judge = [Cost < 1/3*OtherPair[2] for OtherPair in OtherPairs]
#                            Good = True
#                            for J in Judge:
#                                if J:  # if smaller, do this
#                                    Good = False
#                                    Degree[Src] -= 1
#                                    break
#                            if Good: # is no such a thing, do this:
#                                Segs.append( [VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i] ) # here local indexes are converted into global indexes
#                        # end of pruning heuristic 2
#                        # pruning heuristic 3
#                        elif Degree[Src] ==1:
#                            Results, Terminals = otherPaths(Src, Pair, Degree[Dst], Path)
#                            Good = True 
#                            for V in Terminals:
#                                if Degree[V] >1 :
#                                    Degree[Dst] -= 1
#                                    Good = False
#                                    break
#                            if Good: # is no such a thing, do this:
#                                Segs.append( [VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i] ) # here local indexes are converted into global indexes
#                        elif Degree[Dst] ==1:
#                            Results, Terminals = otherPaths(Dst, Pair, Degree[Dst], Path)
#                            Good = True 
#                            for V in Terminals:
#                                if Degree[V] >1 :
#                                    Degree[Src] -= 1
#                                    Good = False
#                                    break
#                            if Good: # is no such a thing, do this:
#                                Segs.append( [VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i] ) # here local indexes are converted into global indexes
                        # end of pruning heuristic 3
                        
#                        else: # no need to prune and thus put this segment into Segs directly                            
                            #Path = bfsReach([ VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst], Cost, i], VrtxCmpnts[i], NbrLst) # deactivated forrest 2011-07-17
                        #Path = [ VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst] ] # Forrest 2011-07-17, do NOT map links onto the mesh Commented 2011-10-21 
                        # FundusLen[VrtxCmpnts[i][Src]]=len(Path) # Forrest 2011-11-01 This is Manhattan distance
                        # FundusLen[VrtxCmpnts[i][Dst]]=len(Path) # Forrest 2011-11-01 This is Manhattan distance
                        FundusLen[VrtxCmpnts[i][Src]] = Length_of_fundus
                        FundusLen[VrtxCmpnts[i][Dst]] = Length_of_fundus
                        FundusID[VrtxCmpnts[i][Src]]= i # Remember, now FundusID starts from 0
                        FundusID[VrtxCmpnts[i][Dst]]= i # Remember, now FundusID starts from 0
                        Segs.append([VrtxCmpnts[i][Src], VrtxCmpnts[i][Dst]])
#                    Segs += Seg
#        print "number of segments: ", len(Segs)
                Color.update(NodeColor)
    return Segs, Color, FundusLen, FundusID

def lineUp(Special, NbrLst, VrtxCmpnts, VtxCoords, CurvFile, CurvatureDB):
    '''Form an MST of a set of vertexes and prune unwanted subtrees
    
    Parameters
    ===========
    
        Special : list of integers
            A list of special vertexes to be connected by MST 
            It can be all vertexes on original mesh
            
        NbrLst : list of list of integers
            neighbor list of vertexes
            
        VrtxCmpnts : list of list of integers
            each element of VrtxCmpnt is a list of vertexes that are in the same sulcal component
      
        Curve : list of integers
            vertexes on the curve segment form fundi  NOT LINED UP really now 04/12/2011
            
        VtxCoords : list of 3-tuples of doubles
            each element is the coordinate of a vertex element 
            
        CurvatureDB : list of doubles
            each element is the curvature value of a vertex 
            
        Links : list of list of 2-tuples of integers
            each element is a list of 2-tuples containing vertexes (in global ID) at two ends of an edge on MSTs
            Since the original mesh has been downsampled, each link in *Links* is a real edge on the mesh. 
    
        SpecialGroup: list of list of integers 
            each element is a list of Special vertexes in each connected component

        Ring : list of integers
            IDs of vertexes that have 0-curvature
            
        Curv: float
            curvature value of a vertex
            
        Idx: integer
            ID of a vertex
      
    Notes
    =======
    
        last updated: 2011-07-17 Forrest
        The function name lineUp does NOT reveal its purpose. Originally, this function is used to connect
        special vertexes via MST algorithm. But now MST is spanned on both special vertexes and common
        vertexes.  

    '''

    # Step 1: downsample the graph 
    Ring = []
#    for Idx, Curv in enumerate(CurvatureDB):
#        if abs(Curv) <0.01:
#            Ring.append(Idx)
    
    NewVrtxCmpnts, NewNbrLst, SpecialGroup = downsample(Special+Ring, Special, VrtxCmpnts, NbrLst, 0.3) 
        
    # step 2: prepare the distance matrix for FUNDUS vertex, for each fundus vertex, only 2 shortest edges are left
    #         Columns and rows for non-fundus vertexes are all zeros.
    DistFile = CurvFile + '.dist'
   
    Dists = dist(NewVrtxCmpnts, NewNbrLst, CurvatureDB, DistFile=DistFile)

    # Dists = zeroout(Dists, VrtxCmpnt, FundiList)  # only needed if MST only spans over special vertexes
    # Now Dists are weighted adjacency matrix of fundus vertexes in each component
    
#    fileio.wrtLists(DistFile+'.reduced', Dists)  # optional line, for debugging
#    Dists = fileio.readLists(DistFile+'.reduced')  # for fast debugging   only 
    # End of step 2
    
    # Step 3: use MST to connect all vertexes in NewVrtxCmpnts and dump into VTK format
    #FundusCmpnts = filterCmpnt(Nodes, VrtxCmpnts) # no need if Nodes are all vertexes on the mesh
    #FundusCmpnts = VrtxCmpnts # if MST will span via all nodes on the mesh
    #Links = mst(Dists, VrtxCmpnts, FundusCmpnts, NbrLst)  # deactivated Forrest 2011-07-21 because filters is done in downsample() 

    Links, NodeColor, FundusLen, FundusID = mst(Dists, NewVrtxCmpnts, SpecialGroup, NbrLst, VtxCoords) # Running version 
    #Links = mst(Dists, NewVrtxCmpnts, NewVrtxCmpnts, NbrLst) # debugging version
        
    return Links, NodeColor, FundusLen, FundusID

# End of functions to connect special vertexes ---

def stepFilter(L, Y, Z):
    '''Return L such that L[i]:= L[i] if L[i] > Y, else, Z. 
    
    '''
    for Idx, X in enumerate(L):
        if X>Y:
            L[Idx] = X 
    else:
            L[Idx] = Z

    return L

def fundiFromPits(Curvature, FeatureNames, MapFeature, Vrtx, Fc, SurfFile, PrefixBasin, PrefixExtract, SurfFile2):
    '''Connecting pits into fundus curves
    
    Parameters
    ============
    
        Curavture: list of floats
            i.e., MapExtract, a per-vertex value map used to find minimum cost path between vertexes
            
        FeatureNames: list of strings
            names of per-vertex features about the surface
            
        MapFeature: lists of lists of floats
            lists of list of per-vertex values that will be used as structure feature vectors, e.g., thickness
    
        Vrtx: list of 3-tuples of floats
            Each element is the X-, Y- and Z-cooridnates of a vertex on the surface, normally pial
            
        Fc: list of 3-tuples of integers
            Each element is the ids of 3 vertexes that form one triangle on the surface 
            
        SurfFile: string
            Path to the mandatory-provided surface file
            
        PrefixBasin: string
            Path to basin/thresholding related files, e.g., lh.curv
            
        PrefixExtract: string
            Path to save pits and fundi extraction related files, e.g., lh.curv.depth.        
    
    Notes
    ========
    
        Function and variable names are not fully changed yet. Names like curvature is bad. 
     
    '''

    LUTname, LUT = [], []
    for Idx, Name in enumerate(FeatureNames):
        Table = MapFeature[Idx]
        if Name == 'curv':
            LUT.append(stepFilter(Table, 0, 0))
            LUTname.append('curv')
        elif Name == 'sulc':  
            LUT.append(stepFilter(Table, 0, 0))
            LUTname.append('sulc')
        elif Name == 'thickness':  
            LUT.append(Table)  # no filtering for thickness
            LUTname.append('thickness')
    
    NbrLst = libbasin.vrtxNbrLst(len(Vrtx), Fc, SurfFile)   
        
    VrtxCmpntFile = PrefixBasin + '.cmpnt.vrtx'  # need to run libbasin first to get components
    VrtxCmpnt = fileio.loadCmpnt(VrtxCmpntFile) # need to run libbasin first to get components    
    
    # the code to lineup pits into fundi    
    
    PitsFile = PrefixExtract + '.pits'
    Pits = libvtk.loadFundiList(PitsFile)
    
    PSegs, NodeColor, FundusLen, FundusID = lineUp(Pits, NbrLst, VrtxCmpnt, Vrtx, PrefixExtract, Curvature) # changed 2011-07-21 00:23

    LenLUT = [0 for i in xrange(0,len(NbrLst))]
    for Key, Value in FundusLen.iteritems():
        LenLUT[Key] = Value               
    LUTname.append('fundusLength')
    LUT.append(LenLUT)
    
    FIDLUT = [-1 for i in xrange(0,len(NbrLst))] # value for gyri is now -1 Forrest 2011-11-01
    for Key, Value in FundusID.iteritems():
        FIDLUT[Key] = Value
    LUTname.append('fundusID')
    LUT.append(FIDLUT)

    print "Saving fundi from Pits into VTK"    
    FPits = PrefixExtract + '.fundi.from.pits'
    fileio.writeFundiSeg(FPits, PSegs)
    
    VTKFile = FPits + "." + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'
    libvtk.seg2VTK(VTKFile, SurfFile, FPits, LUT=LUT, LUTname=LUTname)
    if SurfFile2 != '':
        VTKFile = FPits + "." + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'            
        libvtk.seg2VTK(VTKFile, SurfFile2, FPits, LUT=LUT, LUTname=LUTname)

def getFundi(InputFiles, Type, Options):
    '''Loads input files of different types and extraction types,  and pass them to functions that really does fundi/pits/sulci extraction
    
    Parameters
    ===========
        Type: string 
            If Types == 'VTK-curv', 
            the VTK file should contain a triangular mesh with at least one per-vertex lookup table, e.g., depth map;
            the surface is thresholded using another map, e.g., curvature map, from FreeSurfer.
        
            If Types == 'FreeSurfer, 
            the VTK files should at least be a curvature/convexity and a surface file.
        
            If Type == 'vtk',
                The user needs to specify using which map to threshold the surface 
                and using which map to extract pits and fundi.  

        mapThreshold: list
            a list of per-vertex values that will be used to threshold the cortical surface to get sulcal basins, e.g., curvature/convexity 
            
        mapExtract: list
            a list of per-vertex values that will be used to extract fundi/pits, e.g., curvature/convexity
            
        mapFeature: lists of lists of floats
            lists of list of per-vertex values that will be used as structure feature vectors, e.g., thickness
            
        PrefixBasin: string
            the prefix for all outputs that are only related to basin extraction,
            e.g., connected components, basins and gyri. 
        
        PrefixExtract: string
            the prefix for all outputs that are the result of extraction,
            e.g., pits and fundi.
        
    
    Notes
    ======
    
        12/23/2011: We are now rewriting the interface from getFundi to libbasin.getBaisn, fundiFromPits and fundiFromSkel
        Now variables passed into them are data rather than file names
    
    '''
   
    if Type == 'FreeSurfer':
        
        [CurvFile, SurfFile, SurfFile2, CurvFile2, ThickFile] = InputFiles
        
        Curvature = fileio.readCurv(CurvFile)
        MapBasin = Curvature
        MapExtract = Curvature
        
        PrefixBasin = CurvFile
        PrefixExtract = CurvFile    
        
        MapFeature = [Curvature]
        FeatureNames = [CurvFile[(len(CurvFile) - CurvFile[::-1].find(".")):]]
        if CurvFile2 != '':
            Curvature2 = fileio.readCurv(CurvFile2)
            MapExtract = Curvature2
            MapFeature.append(Curvature2)
            FeatureNames.append(CurvFile2[(len(CurvFile2) - CurvFile2[::-1].find(".")):])
            PrefixExtract = CurvFile + '.' + CurvFile2[(len(CurvFile2) - CurvFile2[::-1].find(".")):]
        if ThickFile != '':
            Thickness = fileio.readCurv(ThickFile)
            MapFeature.append(Thickness)          
            FeatureNames.append('thickness')  

        Vertexes, Faces = fileio.readSurf(SurfFile) 
        Mesh = [Vertexes, Faces]
        if SurfFile2 != '':
            Vertexes2, Faces2 = fileio.readSurf(SurfFile2)
            Mesh2 = [Vertexes2, Faces2]
        else:
            Mesh2 = []        
#        Prefix = SurfFile[:-1*SurfFile[::-1].find('.')] # or CurvFile[:-1*CurvFile[::-1].find('.')] also works
    elif Type == 'vtk-curv':
        [DepthVTK, CurvFile, SurfFile2, ConvexityFile, ThickFile]= InputFiles
        
        import vtk 
        Reader = vtk.vtkDataSetReader()
        Reader.SetFileName(DepthVTK)
        Reader.ReadAllScalarsOn()
        Reader.Update()
        Data = Reader.GetOutput()
        Vertexes= [Data.GetPoint(i) for i in range(0, Data.GetNumberOfPoints())]
        Polys = Data.GetPolys()
        Polys = Polys.GetData()
        Faces=[ [Polys.GetValue(Idx) for Idx in range(4*i+1, 4*(i+1))]  for i in range(0, Data.GetNumberOfPolys())]
        
        Curvature = fileio.readCurv(CurvFile)
        
        PointData = Data.GetPointData()
        DepthMap = PointData.GetArray('scalars')
        
        Depth = [DepthMap.GetValue(i) for i in range(0, DepthMap.GetSize() )]
         
        MapBasin = Curvature        
        MapExtract = Depth
        
        PrefixBasin = DepthVTK[:-4] # drop suffix .vtk
        PrefixExtract = CurvFile + '.depth'

        MapFeature = [Curvature, Depth]
        FeatureNames = ['curvature','depth']
        if ConvexityFile != '':
            Convexity = fileio.readCurv(ConvexityFile)
            MapFeature.append(Convexity)
            FeatureNames.append('convexity')
        if ThickFile != '':
            Thickness = fileio.readCurv(ThickFile)
            MapFeature.append(Thickness)          
            FeatureNames.append('thickness')  
        
        Mesh = [Vertexes, Faces]
        if SurfFile2 != '':
            Vertexes2, Faces2 = fileio.readSurf(SurfFile2)
            Mesh2 = [Vertexes2, Faces2]
        else:
            Mesh2 = []
            
        SurfFile = 'lh.pial'  # this file name does not matter for vtk-curv
                
    elif Type == 'vtk': # pure VTK
        pass
        
    libbasin.getBasin(MapBasin, MapExtract, Mesh, PrefixBasin, PrefixExtract, SurfFile, Mesh2, Threshold=0, SurfFile2=SurfFile2)
    exit()
    fundiFromPits(MapExtract, FeatureNames, MapFeature, Vertexes, Faces, SurfFile, PrefixBasin, PrefixExtract, SurfFile2)
#        fundiFromSkel(MapExtract, FeatureNames, MapFeature, Vertexes, Faces, SurfFile, CurvFile, SurfFile2)

    
def fundiFromSkel(Curvature, FeatureNames, MapFeature, Vrtx, Fc, SurfFile, CurvFile, SurfFile2):
       
    LUTname, LUT = [], []
    for Idx, Name in enumerate(FeatureNames):
        Table = MapFeature[Idx]
        if Name == 'curv':
            LUT.append(stepFilter(Table, 0, 0))
            LUTname.append('curv')
        elif Name == 'sulc':  
            LUT.append(stepFilter(Table, 0, 0))
            LUTname.append('sulc')
        elif Name == 'thickness':  
            LUT.append(Table)  # no filtering for thickness
            LUTname.append('thickness')

    Prefix= CurvFile
            
    NbrLst = libbasin.fcNbrLst(Fc, SurfFile)  # Activated 2011-04-30, 21:46 
    
    Center = libskel.getCenter(Fc, Curvature) # get the per-face curvature

    Candidate, Strict = libskel.faceFundi(Fc, Curvature, NbrLst, Center, Skip2= True, Skip3 = True)

    VrtxNbrLst = libbasin.vrtxNbrLst(len(Vrtx), Fc, SurfFile) # activated on 2011-04-30 21:55
    
    FaceCmpntFile = CurvFile + '.cmpnt.face'
    FaceCmpnts = fileio.loadCmpnt(FaceCmpntFile)
    Clouds = libskel.fc2VrtxCmpnt(Fc, Candidate, FaceCmpnts) # step 1: Convert faces in to Vrtx, clustered by components    
    DTMap = libskel.myDT(Clouds, VrtxNbrLst)  # step 2: my own distance transformation
    
    DTLUT = [0 for i in xrange(0,len(VrtxNbrLst))]  # initialize the LUT for all vertexes in the surface as -1
    for i in xrange(0,len(Clouds)):
        for j in xrange(0,len(Clouds[i])):
            DTLUT[Clouds[i][j]] = DTMap[i][j]    

    LUTname.append('DT')
    LUT.append(DTLUT)

# output 2: Skeletons 
  
    Skeletons = libskel.faceToCurve(Fc, Candidate, FaceCmpnts, VrtxNbrLst) 

    Candidate = []
    for Skeleton in Skeletons:
        Candidate += Skeleton

    FCandidate = Prefix + '.skeletons'
    fileio.writeList(FCandidate, Candidate)
    
    print "\t Saving Skeletons into VTK files"
    
    VTKFile = FCandidate + "." + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'
    libvtk.vrtxLst2VTK(VTKFile, SurfFile, FCandidate)
    if SurfFile2 != '':
        VTKFile = FCandidate + "." + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'
        libvtk.vrtxLst2VTK(VTKFile, SurfFile2, FCandidate)
# End of output 2: Skeletons 

# output 3: fundus curves connected from skeletons 
                 
    VrtxCmpntFile = CurvFile + '.cmpnt.vrtx'
    VrtxCmpnt = fileio.loadCmpnt(VrtxCmpntFile)
    
    Candidate, NodeColor, FundusLen, FundusID = lineUp(Candidate, VrtxNbrLst, VrtxCmpnt, Vrtx, CurvFile, Curvature) # activated 2011-05-28 17:53

    print "\t Saving fundi from Skeleton into VTK files"
        
    LenLUT = [0 for i in xrange(0,len(NbrLst))]
    for Key, Value in FundusLen.iteritems():
        LenLUT[Key] = Value        
         
    LUTname.append('fundusLength')
    LUT.append(LenLUT)
    
    FIDLUT = [-1 for i in xrange(0,len(NbrLst))] # value for gyri is now -1 Forrest 2011-11-01
    for Key, Value in FundusID.iteritems():
        FIDLUT[Key] = Value

    LUTname.append('fundusID')
    LUT.append(FIDLUT)
        
    FCandidate = Prefix + '.fundi.from.skeletons'
    fileio.writeFundiSeg(FCandidate, Candidate)
    
    VTKFile = FCandidate + "." + SurfFile[-1*SurfFile[::-1].find('.'):] + '.vtk'
    libvtk.seg2VTK(VTKFile, SurfFile, FCandidate, LUT=LUT, LUTname=LUTname)
    if SurfFile2 != '':
        VTKFile = FCandidate + "." + SurfFile2[-1*SurfFile2[::-1].find('.'):] + '.vtk'
        libvtk.seg2VTK(VTKFile, SurfFile2, FCandidate, LUT=LUT, LUTname=LUTname)

# End of output 3: fundus curves connected from skeletons 