import numpy as np
from scipy.sparse import coo_matrix, csc_matrix, csr_matrix
from scipy.sparse import spdiags, eye, tril, triu, bmat
from .mesh_tools import unique_row
from .Mesh3d import Mesh3d, Mesh3dDataStructure
from ..quadrature import TetrahedronQuadrature

class TetrahedronMeshDataStructure(Mesh3dDataStructure):
    localFace = np.array([(1, 2, 3),  (0, 3, 2), (0, 1, 3), (0, 2, 1)])
    localEdge = np.array([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
    localFace2edge = np.array([(5, 4, 3), (5, 1, 2), (4, 2, 0), (3, 0, 1)])
    index = np.array([
       (0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2),
       (1, 2, 0, 3), (1, 0, 3, 2), (1, 3, 2, 0),
       (2, 0, 1, 3), (2, 1, 3, 0), (2, 3, 0, 1),
       (3, 0, 2, 1), (3, 2, 1, 0), (3, 1, 0, 2)]);
    V = 4
    E = 6
    F = 4

    def __init__(self, N, cell):
        super(TetrahedronMeshDataStructure, self).__init__(N, cell)

    def face_to_edge_sign(self):
        face2edge = self.face_to_edge()
        edge = self.edge
        face2edgeSign = np.zeros((NF, FE), dtype=np.bool)
        n = [1, 2, 0]
        for i in range(3):
            face2edgeSign[:, i] = (face[:, n[i]] == edge[face2edge[:, i], 0])
        return face2edgeSign


class TetrahedronMesh(Mesh3d):
    def __init__(self, node, cell):
        self.node = node
        N = node.shape[0]
        self.ds = TetrahedronMeshDataStructure(N, cell)

        self.meshtype = 'tet'

        self.itype = cell.dtype
        self.ftype = node.dtype

        self.celldata = {}
        self.edgedata = {}
        self.facedata = {}
        self.nodedata = {}

    def vtk_cell_type(self):
        VTK_TETRA = 10
        return VTK_TETRA

    def integrator(self, k):
        return TetrahedronQuadrature(k)

    def delete_cell(self, threshold):
        NN = self.number_of_nodes()

        cell = self.entity('cell')
        node = self.entity('node')
        bc = self.entity_barycenter('cell')
        isKeepCell = ~threshold(bc)
        cell = cell[isKeepCell]

        isValidNode = np.zeros(NN, dtype=np.bool)
        isValidNode[cell] = True
        node = node[isValidNode]

        idxMap = np.zeros(NN, dtype=self.itype)
        idxMap[isValidNode] = range(isValidNode.sum())
        cell = idxMap[cell]
        self.node = node
        NN = len(node)
        self.ds.reinit(NN, cell)

    def direction(self, i):
        """ Compute the direction on every vertex of

        0 <= i < 4
        """
        node = self.node
        cell = self.ds.cell
        index = self.ds.index
        v10 = node[cell[:, index[3*i, 0]]] - node[cell[:, index[3*i, 1]]]
        v20 = node[cell[:, index[3*i, 0]]] - node[cell[:, index[3*i, 2]]]
        v30 = node[cell[:, index[3*i, 0]]] - node[cell[:, index[3*i, 3]]]
        l1 = np.sum(v10**2, axis=1, keepdims=True)
        l2 = np.sum(v20**2, axis=1, keepdims=True)
        l3 = np.sum(v30**2, axis=1, keepdims=True)

        return l1*np.cross(v20, v30) + l2*np.cross(v30, v10) + l3*np.cross(v10, v20)

    def volume(self):
        cell = self.ds.cell
        node = self.node
        v01 = node[cell[:,1]] - node[cell[:,0]]
        v02 = node[cell[:,2]] - node[cell[:,0]]
        v03 = node[cell[:,3]] - node[cell[:,0]]
        volume = np.sum(v03*np.cross(v01, v02), axis=1)/6.0
        return volume

    def face_normal(self):
        face = self.ds.face
        node = self.node
        v01 = node[face[:, 1], :] - node[face[:, 0], :]
        v02 = node[face[:, 2], :] - node[face[:, 0], :]
        nv = np.cross(v01, v02)
        return nv

    def face_unit_normal(self):
        face = self.ds.face
        node = self.node
        v01 = node[face[:, 1], :] - node[face[:, 0], :]
        v02 = node[face[:, 2], :] - node[face[:, 0], :]
        nv = np.cross(v01, v02)
        length = np.sqrt(np.square(nv).sum(axis=1))
        return nv/length.reshape(-1, 1)

    def cell_volume(self):
        cell = self.ds.cell
        node = self.node
        v01 = node[cell[:,1]] - node[cell[:,0]]
        v02 = node[cell[:,2]] - node[cell[:,0]]
        v03 = node[cell[:,3]] - node[cell[:,0]]
        volume = np.sum(v03*np.cross(v01, v02), axis=1)/6.0
        return volume

    def face_area(self):
        face = self.ds.face
        node = self.node
        v01 = node[face[:, 1], :] - node[face[:, 0], :]
        v02 = node[face[:, 2], :] - node[face[:, 0], :]
        nv = np.cross(v01, v02)
        area = np.sqrt(np.square(nv).sum(axis=1))/2.0
        return area

    def edge_length(self):
        edge = self.ds.edge
        node = self.node
        v = node[edge[:, 1]] - node[edge[:, 0]]
        length = np.sqrt(np.sum(v**2, axis=-1))
        return length


    def dihedral_angle(self):
        NC = self.number_of_cells()
        node = self.node
        cell = self.ds.cell
        localFace = self.ds.localFace
        n = [np.cross(node[cell[:, j],:] - node[cell[:, i],:],
            node[cell[:, k],:] - node[cell[:, i],:]) for i, j, k in localFace]
        l =[ np.sqrt(np.sum(ni**2, axis=1)) for ni in n]
        n = [ ni/li.reshape(-1, 1) for ni, li in zip(n, l)]
        localEdge = self.ds.localEdge
        angle = [(np.pi - np.arccos((n[i]*n[j]).sum(axis=1)))/np.pi*180 for i,j in localEdge[-1::-1]]
        return np.array(angle).T


    def bc_to_point(self, bc):
        node = self.node
        cell = self.ds.cell
        p = np.einsum('...j, ijk->...ik', bc, node[cell])
        return p 

    def circumcenter(self):
        node = self.node
        cell = self.ds.cell
        v = [ node[cell[:,0],:] - node[cell[:,i],:] for i in range(1,4)]
        l = [ np.sum(vi**2, axis=1, keepdims=True) for vi in v]
        d = l[2]*np.cross(v[0], v[1]) + l[0]*np.cross(v[1], v[2]) + l[1]*np.cross(v[2],v[0])
        volume = self.cell_volume()
        d /=12*volume.reshape(-1,1)
        c = node[cell[:,0],:] + d
        R = np.sqrt(np.sum(d**2,axis=1))
        return c, R

    def quality(self):
        s = self.face_area()
        cell2face = self.ds.cell_to_face()
        ss = np.sum(s[cell2face], axis=1)
        d = self.direction(0)
        ld = np.sqrt(np.sum(d**2, axis=1))
        vol = self.cell_volume()
        R = ld/vol/12.0
        r = 3.0*vol/ss
        return R/r/3.0

    def grad_quality(self):
        cell = self.ds.cell
        node = self.node

        N = self.number_of_nodes()
        NC = self.number_of_cells()

        s = self.face_area()
        cell2face = self.ds.cell_to_face()
        s = s[cell2face]

        ss = np.sum(s, axis=1)
        d = [self.direction(i) for i in range(4)]
        dd = np.sum(d[0]**2, axis=1)

        ld = np.sqrt(np.sum(d[0]**2, axis=1))
        vol = self.cell_volume()
        R = ld/vol/12.0
        r = 3.0*vol/ss
        q = R/r/3.0
        index = self.ds.index
        g = np.zeros((NC, 4, 3), dtype=self.ftype)
        w = np.zeros((NC, 4), dtype=self.ftype)
        for idx in range(12):
            i = index[idx, 0]
            j = index[idx, 1]
            k = index[idx, 2]
            m = index[idx, 3]
            vji = node[cell[:, i]] - node[cell[:, j]]
            w0 = 2.0*np.sum(np.cross(node[cell[:, i]] - node[cell[:, k]],
                node[cell[:, i]] - node[cell[:, m]])*d[i], axis=1)/dd
            w1 = 0.25*(np.sum((node[cell[:, i]] - node[cell[:,
                m]])*(node[cell[:, j]] - node[cell[:, m]]), axis=1)/s[:, k] 
                    + np.sum((node[cell[:, i]] - node[cell[:,
                        k]])*(node[cell[:, j]] - node[cell[:, k]]), axis=1)/s[:, m])/ss

            g[:, i, :] += (w0 + w1).reshape(-1, 1)*vji
            w[:, i] += (w0 + w1)

            w2 = (np.sum((node[cell[:, i]] - node[cell[:, m]])**2, axis=1) -
                    np.sum((node[cell[:, i]]-node[cell[:, k]])**2, axis=1))/dd 
            g[:, i, :] += w2.reshape(-1, 1)*np.cross(d[i], vji)
            g[:, i, :] += np.cross(node[cell[:, k]] + node[cell[:, j]] - 2*node[cell[:, m]], vji)/vol.reshape(-1, 1)/9.0

        g *= q.reshape(-1, 1, 1)
        w *= q.reshape(-1, 1)
        grad = np.zeros((N, 3), dtype=self.ftype)
        np.add.at(grad, cell.flatten(), g.reshape(-1, 3))
        wgt = np.zeros(N, dtype=self.ftype)
        np.add.at(wgt, cell.flat, w.flat)

        return grad/wgt.reshape(-1, 1)

    def grad_lambda(self):
        localFace = self.ds.localFace
        node = self.node
        cell = self.ds.cell
        NC = self.number_of_cells()
        Dlambda = np.zeros((NC, 4, 3), dtype=self.ftype)
        volume = self.volume()
        for i in range(4):
            j,k,m = localFace[i]
            vjk = node[cell[:,k],:] - node[cell[:,j],:]
            vjm = node[cell[:,m],:] - node[cell[:,j],:]
            Dlambda[:,i,:] = np.cross(vjm, vjk)/(6*volume.reshape(-1,1))
        return Dlambda

    def label(self, node=None, cell=None, cellidx=None):
        """单元顶点的重新排列，使得cell[:, :2] 存储了单元的最长边
        Parameter
        ---------

        Return
        ------
        cell ： in-place modify

        """

        rflag = False
        if node is None:
            node = self.entity('node')

        if cell is None:
            cell = self.entity('cell')
            rflag = True

        if cellidx is None:
            cellidx = np.arange(len(cell))

        NC = cellidx.shape[0]
        localEdge = self.ds.localEdge
        totalEdge = cell[cellidx][:, localEdge].reshape(
                -1, localEdge.shape[1])
        NE = totalEdge.shape[0]
        length = np.sum(
                (node[totalEdge[:, 1]] - node[totalEdge[:, 0]])**2,
                axis = -1)
        length += 0.1*np.random.rand(NE)*length
        cellEdgeLength = length.reshape(NC, 6)
        lidx = np.argmax(cellEdgeLength, axis=-1)

        flag = (lidx == 1)
        if  sum(flag) > 0:
            cell[cellidx[flag], :] = cell[cellidx[flag]][:, [2, 0, 1, 3]]

        flag = (lidx == 2)
        if sum(flag) > 0:
            cell[cellidx[flag], :] = cell[cellidx[flag]][:, [0, 3, 1, 2]]

        flag = (lidx == 3)
        if sum(flag) > 0:
            cell[cellidx[flag], :] = cell[cellidx[flag]][:, [1, 2, 0, 3]]

        flag = (lidx == 4)
        if sum(flag) > 0:
            cell[cellidx[flag], :] = cell[cellidx[flag]][:, [1, 3, 2, 0]]

        flag = (lidx == 5)
        if sum(flag) > 0:
            cell[cellidx[flag], :] = cell[cellidx[flag]][:, [3, 2, 1, 0]]

        if rflag == True:
            self.ds.construct()


    def uniform_bisect(self, n=1):
        for i in range(2*n):
            self.bisect()

    def bisect(self, isMarkedCell=None, data=None, returnim=False):

        NN = self.number_of_nodes()
        NC = self.number_of_cells()

        if isMarkedCell is None: # 加密所有的单元
            markedCell = np.arange(NC, dtype=self.itype)
        else:
            markedCell, = np.nonzero(isMarkedCell)

        # allocate new memory for node and cell
        node = np.zeros((9*NN, 3), dtype=self.ftype)
        cell = np.zeros((4*NC, 4), dtype=self.itype)

        node[:NN] = self.entity('node')
        cell[:NC] = self.entity('cell')
        # 用于存储网格节点的代数，初始所有节点都为第 0 代
        generation = np.zeros(NN + 6*NC, dtype=np.uint8)

        # 用于记录被二分的边及其中点编号
        cutEdge = np.zeros((8*NN, 3), dtype=self.itype)

        # 当前的二分边的数目
        nCut = 0

        # 非协调边的标记数组 
        nonConforming = np.ones(8*NN, dtype=np.bool)
        IM = eye(NN)
        while len(markedCell) != 0:
            # 标记最长边
            self.label(node, cell, markedCell)

            # 获取标记单元的四个顶点编号
            p0 = cell[markedCell, 0]
            p1 = cell[markedCell, 1]
            p2 = cell[markedCell, 2]
            p3 = cell[markedCell, 3]

            # 找到新的二分边和新的中点 
            nMarked = len(markedCell)
            p4 = np.zeros(nMarked, dtype=self.itype)

            if nCut == 0: # 如果是第一次循环 
                idx = np.arange(nMarked) # cells introduce new cut edges
            else:
                # all non-conforming edges
                ncEdge = np.nonzero(nonConforming[:nCut])
                NE = len(ncEdge)
                I = cutEdge[ncEdge][:, [2, 2]].reshape(-1)
                J = cutEdge[ncEdge][:, [0, 1]].reshape(-1)
                val = np.ones(len(I), dtype=np.bool)
                nv2v = csr_matrix(
                        (val, (I, J)),
                        shape=(NN, NN))
                i, j =  np.nonzero(nv2v[:, p0].multiply(nv2v[:, p1]))
                p4[j] = i
                idx, = np.nonzero(p4 == 0)

            if len(idx) != 0:
                # 把需要二分的边唯一化 
                NE = len(idx)
                cellCutEdge = np.array([p0[idx], p1[idx]])
                cellCutEdge.sort(axis=0)
                s = csr_matrix(
                    (
                        np.ones(NE, dtype=np.bool),
                        (
                            cellCutEdge[0, ...],
                            cellCutEdge[1, ...]
                        )
                    ), shape=(NN, NN), dtype=np.bool)
                # 获得唯一的边 
                i, j = s.nonzero()
                nNew = len(i)
                newCutEdge = np.arange(nCut, nCut+nNew)
                cutEdge[newCutEdge, 0] = i
                cutEdge[newCutEdge, 1] = j
                cutEdge[newCutEdge, 2] = range(NN, NN+nNew)
                node[NN:NN+nNew, :] = (node[i, :] + node[j, :])/2.0
                if returnim is True:
                    val = np.full(nNew, 0.5)
                    I = coo_matrix(
                            (val, (range(nNew), i)), shape=(nNew, NN),
                            dtype=self.ftype)
                    I += coo_matrix(
                            (val, (range(nNew), j)), shape=(nNew, NN),
                            dtype=self.ftype)
                    I = bmat([[eye(NN)], [I]], format='csr')
                    IM = I@IM

                nCut += nNew
                NN += nNew

                # 新点和旧点的邻接矩阵 
                I = cutEdge[newCutEdge][:, [2, 2]].reshape(-1)
                J = cutEdge[newCutEdge][:, [0, 1]].reshape(-1)
                val = np.ones(len(I), dtype=np.bool)
                nv2v = csr_matrix(
                        (val, (I, J)),
                        shape=(NN, NN))
                i, j =  np.nonzero(nv2v[:, p0].multiply(nv2v[:, p1]))
                p4[j] = i

            # 如果新点的代数仍然为 0
            idx = (generation[p4] == 0)
            cellGeneration = np.max(
                    generation[cell[markedCell[idx]]],
                    axis=-1)
            # 第几代点 
            generation[p4[idx]] = cellGeneration + 1
            cell[markedCell, 0] = p3
            cell[markedCell, 1] = p0
            cell[markedCell, 2] = p2
            cell[markedCell, 3] = p4
            cell[NC:NC+nMarked, 0] = p2
            cell[NC:NC+nMarked, 1] = p1
            cell[NC:NC+nMarked, 2] = p3
            cell[NC:NC+nMarked, 3] = p4
            NC = NC + nMarked
            del cellGeneration, p0, p1, p2, p3, p4

            # 找到非协调的单元 
            checkEdge, = np.nonzero(nonConforming[:nCut])
            isCheckNode = np.zeros(NN, dtype=np.bool)
            isCheckNode[cutEdge[checkEdge]] = True
            isCheckCell = np.sum(
                    isCheckNode[cell[:NC]],
                    axis= -1) > 0
            # 找到所有包含检查节点的单元编号 
            checkCell, = np.nonzero(isCheckCell)
            I = np.repeat(checkCell, 4)
            J = cell[checkCell].reshape(-1)
            val = np.ones(len(I), dtype=np.bool)
            cell2node = csr_matrix((val, (I, J)), shape=(NC, NN))
            i, j = np.nonzero(
                    cell2node[:, cutEdge[checkEdge, 0]].multiply(
                        cell2node[:, cutEdge[checkEdge, 1]]
                        ))
            markedCell = np.unique(i)
            nonConforming[checkEdge] = False
            nonConforming[checkEdge[j]] = True;


        self.node = node[:NN]
        cell = cell[:NC]
        self.ds.reinit(NN, cell)

        if returnim is True:
            return IM

    def uniform_refine(self, n=1):
        for i in range(n):
            N = self.number_of_nodes()
            NC = self.number_of_cells()
            NE = self.number_of_edges()

            node = self.node
            edge = self.ds.edge
            cell = self.ds.cell
            cell2edge = self.ds.cell_to_edge()

            edge2newNode = np.arange(N, N+NE)
            newNode = (node[edge[:,0],:]+node[edge[:,1],:])/2.0

            self.node = np.concatenate((node, newNode), axis=0)

            p = edge2newNode[cell2edge]
            newCell = np.zeros((8*NC, 4), dtype=self.itype)

            newCell[0:4*NC, 3] = cell.flatten('F')
            newCell[0:NC, 0:3] = p[:, [0, 2, 1]]
            newCell[NC:2*NC, 0:3] = p[:, [0, 3, 4]]
            newCell[2*NC:3*NC, 0:3] = p[:, [1, 5, 3]]
            newCell[3*NC:4*NC, 0:3] = p[:, [2, 4, 5]]

            l = np.zeros((NC, 3), dtype=self.ftype)
            node = self.node
            l[:, 0] = np.sum((node[p[:, 0]] - node[p[:, 5]])**2, axis=1)
            l[:, 1] = np.sum((node[p[:, 1]] - node[p[:, 4]])**2, axis=1)
            l[:, 2] = np.sum((node[p[:, 2]] - node[p[:, 3]])**2, axis=1)

            # Here one should connect the shortest edge
            # idx = np.argmax(l, axis=1)
            idx = np.argmin(l, axis=1)
            T = np.array([
                (1, 3, 4, 2, 5, 0),
                (0, 2, 5, 3, 4, 1),
                (0, 4, 5, 1, 3, 2)
                ])[idx]
            newCell[4*NC:5*NC, 0] = p[range(NC), T[:, 0]]
            newCell[4*NC:5*NC, 1] = p[range(NC), T[:, 1]]
            newCell[4*NC:5*NC, 2] = p[range(NC), T[:, 4]] 
            newCell[4*NC:5*NC, 3] = p[range(NC), T[:, 5]]

            newCell[5*NC:6*NC, 0] = p[range(NC), T[:, 1]]
            newCell[5*NC:6*NC, 1] = p[range(NC), T[:, 2]]
            newCell[5*NC:6*NC, 2] = p[range(NC), T[:, 4]] 
            newCell[5*NC:6*NC, 3] = p[range(NC), T[:, 5]]

            newCell[6*NC:7*NC, 0] = p[range(NC), T[:, 2]]
            newCell[6*NC:7*NC, 1] = p[range(NC), T[:, 3]]
            newCell[6*NC:7*NC, 2] = p[range(NC), T[:, 4]] 
            newCell[6*NC:7*NC, 3] = p[range(NC), T[:, 5]]

            newCell[7*NC:, 0] = p[range(NC), T[:, 3]]
            newCell[7*NC:, 1] = p[range(NC), T[:, 0]]
            newCell[7*NC:, 2] = p[range(NC), T[:, 4]] 
            newCell[7*NC:, 3] = p[range(NC), T[:, 5]]

            N = self.number_of_nodes()
            self.ds.reinit(N, newCell)

    def is_valid(self):
        vol = self.volume()
        return np.all(vol > 1e-15)

    def print(self):
        print("Node:\n", self.node)
        print("Cell:\n", self.ds.cell)
        print("Edge:\n", self.ds.edge)
        print("Face:\n", self.ds.face)
        print("Face2cell:\n", self.ds.face2cell)
        print("Cell2face:\n", self.ds.cell_to_face())


