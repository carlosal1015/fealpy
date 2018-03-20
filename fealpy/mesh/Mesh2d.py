import numpy as np
from scipy.sparse import coo_matrix, csc_matrix, csr_matrix, spdiags, eye, tril, triu
from .mesh_tools import unique_row, find_node, find_entity, show_mesh_2d
from ..common import ranges
from types import ModuleType

class Mesh2d():
    """ The base class of TriangleMesh and QuadrangleMesh
        
        The class is just a abstract class, and you can not use it directly.
    """
    def number_of_nodes(self):
        return self.node.shape[0]

    def number_of_edges(self):
        return self.ds.NE

    def number_of_cells(self):
        return self.ds.NC

    def number_of_vertices_of_cells(self):
        return self.ds.number_of_vertices_of_cells()

    def number_of_edges_of_cells(self):
        return self.ds.number_of_vertices_of_cells()

    def geo_dimension(self):
        return self.node.shape[1]

    def top_dimension(self):
        return 2

    def barycenter(self, entity='cell', index=None):
        node = self.node
        if entity == 'cell':
            cell = self.ds.cell
            if index is None:
                bc = np.sum(node[cell, :], axis=1)/cell.shape[1]
            else:
                bc = np.sum(node[cell[index], :], axis=1)/cell.shape[1]
        elif entity == 'edge':
            edge = self.ds.edge
            if index is None:
                bc = np.sum(node[edge, :], axis=1)/edge.shape[1]
            else:
                bc = np.sum(node[edge[index], :], axis=1)/edge.shape[1]
        elif entity == 'node':
            if index is None:
                bc = node
            else:
                bc = node[index]
        else:
            raise ValueError('the entity `{}` is not correct!'.format(entity)) 
        return bc

    def area(self):
        #TODO: 3D Case
        NC = self.number_of_cells()
        node = self.node
        edge = self.ds.edge
        edge2cell = self.ds.edge2cell
        isInEdge = (edge2cell[:, 0] != edge2cell[:, 1])
        w = np.array([[0, -1], [1, 0]], dtype=np.int)
        v= (node[edge[:, 1], :] - node[edge[:, 0], :])@w
        val = np.sum(v*node[edge[:, 0], :], axis=1)
        a = np.bincount(edge2cell[:, 0], weights=val, minlength=NC)
        a+= np.bincount(edge2cell[isInEdge, 1], weights=-val[isInEdge], minlength=NC)
        a /=2
        return a

    def cell_area(self):
        #TODO: 3D Case
        NC = self.number_of_cells()
        node = self.node
        edge = self.ds.edge
        edge2cell = self.ds.edge2cell
        isInEdge = (edge2cell[:, 0] != edge2cell[:, 1])
        w = np.array([[0, -1], [1, 0]], dtype=np.int)
        v= (node[edge[:, 1], :] - node[edge[:, 0], :])@w
        val = np.sum(v*node[edge[:, 0], :], axis=1)
        a = np.bincount(edge2cell[:, 0], weights=val, minlength=NC)
        a+= np.bincount(edge2cell[isInEdge, 1], weights=-val[isInEdge], minlength=NC)
        a /=2
        return a

    def edge_length(self):
        edge = self.ds.edge
        node = self.node
        v = node[edge[:, 1]] - node[edge[:, 0]]
        length = np.sqrt(np.sum(v**2, axis=-1))
        return length

    def entity(self, dim=2):
        if dim == 2:
            return self.ds.cell
        elif dim == 1:
            return self.ds.edge
        elif dim == 0:
            return self.node
        else:
            raise ValueError('dim must be in [0, 1, 2]!')

    def entity_measure(self, dim=2):
        if dim == 2:
            return self.cell_area()
        elif dim == 1:
            return self.edge_length()

    def edge_length(self, index=None):
        if index is None:
            v = node[edge[:,1],:] - node[edge[:,0],:]
        else:
            v = node[edge[index,1],:] - node[edge[index,0],:]
        length = np.sqrt(np.sum(v**2,axis=1))
        return length

    def edge_frame(self, index=None):
        t = self.edge_unit_tagent(index=index)
        w = np.array([(0,-1),(1,0)])
        n = v@w
        return n, t

    def edge_unit_normal(self, index=None):
        #TODO: 3D Case
        v = self.edge_unit_tagent(index=index)
        w = np.array([(0,-1),(1,0)])
        return v@w

    def edge_unit_tagent(self, index=None):
        edge = self.ds.edge
        node = self.node
        NE = self.number_of_edges()
        if index is None:
            v = node[edge[:,1],:] - node[edge[:,0],:]
            length = np.sqrt(np.sum(v**2,axis=1))
            v /= length.reshape(-1, 1)
        else:
            v = node[edge[index,1],:] - node[edge[index,0],:]
            length = np.sqrt(np.sum(v**2, axis=1))
            v /= length.reshape(-1, 1)
        return v

    def edge_normal(self, index=None):
        v = self.edge_tagent(index=index)
        w = np.array([(0,-1),(1,0)])
        return v@w

    def edge_tagent(self, index=None):
        node = self.node
        edge = self.ds.edge
        if index is None:
            v = node[edge[:,1],:] - node[edge[:,0],:]
        else:
            v = node[edge[index,1],:] - node[edge[index,0],:]
        return v 

    def add_plot(self, plot,
            nodecolor='w', edgecolor='k',
            cellcolor=[0.5, 0.9, 0.45], aspect='equal',
            linewidths=1, markersize=2,  
            showaxis=False, showcolorbar=False, cmap='rainbow'):

        if isinstance(plot, ModuleType):
            fig = plot.figure()
            fig.set_facecolor('white')
            axes = fig.gca() 
        else:
            axes = plot
        return show_mesh_2d(axes, self,
                nodecolor=nodecolor, edgecolor=edgecolor,
                cellcolor=cellcolor, aspect=aspect,
                linewidths=linewidths, markersize=markersize,  
                showaxis=showaxis, showcolorbar=showcolorbar, cmap=cmap)

    def find_node(self, axes, node=None,
            index=None, showindex=False,
            color='r', markersize=200, 
            fontsize=24, fontcolor='k'):

        if node is None:
            node = self.node
        find_node(axes, node, 
                index=index, showindex=showindex, 
                color=color, markersize=markersize,
                fontsize=fontsize, fontcolor=fontcolor)


    def find_edge(self, axes, 
            index=None, showindex=False,
            color='g', markersize=400, 
            fontsize=24, fontcolor='k'):

        find_entity(axes, self, entity='edge',
                index=index, showindex=showindex, 
                color=color, markersize=markersize,
                fontsize=fontsize, fontcolor=fontcolor)

    def find_cell(self, axes, 
            index=None, showindex=False,
            color='y', markersize=800, 
            fontsize=24, fontcolor='k'):
        
        find_entity(axes, self, entity='cell',
                index=index, showindex=showindex, 
                color=color, markersize=markersize,
                fontsize=fontsize, fontcolor=fontcolor)

    def print(self):
        print("Point:\n", self.node)
        print("Cell:\n", self.ds.cell)
        print("Edge and Edge2cell:\n", np.concatenate((self.ds.edge, self.ds.edge2cell), axis=1))
        print("Cell2edge:\n", self.ds.cell_to_edge())

class Mesh2dDataStructure():
    """ The topology data structure of mesh 2d
        This is just a abstract class, and you can not use it directly. 
    """

    def __init__(self, N, cell):
        self.N = N
        self.NC = cell.shape[0]
        self.cell = cell
        self.construct()

    def reinit(self, N, cell):
        self.N = N
        self.NC = cell.shape[0]
        self.cell = cell
        self.construct()

    def clear(self):
        self.edge = None
        self.edge2cell = None

    def number_of_vertices_of_cells(self):
        return self.V

    def number_of_edges_of_cells(self):
        return self.E

    def total_edge(self):
        NC = self.NC

        cell = self.cell
        localEdge = self.localEdge

        totalEdge = cell[:, localEdge].reshape(-1, 2)
        return np.sort(totalEdge, axis=1)

    def construct(self):  
        """ Construct edge and edge2cell from cell
        """
        NC = self.NC
        E = self.E

        totalEdge = self.total_edge()
        _, i0, j = unique_row(totalEdge)
        NE = i0.shape[0]
        self.NE = NE

        self.edge2cell = np.zeros((NE, 4), dtype=np.int)

        i1 = np.zeros(NE, dtype=np.int) 
        i1[j] = np.arange(E*NC)

        self.edge2cell[:, 0] = i0//E 
        self.edge2cell[:, 1] = i1//E
        self.edge2cell[:, 2] = i0%E 
        self.edge2cell[:, 3] = i1%E 

        cell = self.cell
        localEdge = self.localEdge
        edge2cell = self.edge2cell
        self.edge = cell[edge2cell[:, [0]], localEdge[edge2cell[:, 2]]]

    def cell_to_node(self):
        """ 
        """
        N = self.N
        NC = self.NC
        V = self.V

        cell = self.cell

        I = np.repeat(range(NC), V)
        val = np.ones(self.V*NC, dtype=np.bool)
        cell2node = csr_matrix((val, (I, cell.flatten())), shape=(NC, N), dtype=np.bool)
        return cell2node

    def cell_to_edge(self, sparse=False):
        """ The neighbor information of cell to edge
        """
        NE = self.NE
        NC = self.NC
        E = self.E

        edge2cell = self.edge2cell

        if sparse == False:
            cell2edge = np.zeros((NC, E), dtype=np.int)
            cell2edge[edge2cell[:, 0], edge2cell[:, 2]] = np.arange(NE)
            cell2edge[edge2cell[:, 1], edge2cell[:, 3]] = np.arange(NE)
            return cell2edge
        else:
            val = np.ones(2*NE, dtype=np.bool)
            I = edge2cell[:, [0, 1]].flatten()
            J = np.repeat(range(NE), 2)
            cell2edge = csr_matrix(
                    (val, (I, J)), 
                    shape=(NC, NE), dtype=np.bool)
            return cell2edge 

    def cell_to_edge_sign(self, sparse=False):
        NC = self.NC
        E = self.E

        edge2cell = self.edge2cell
        if sparse == False:
            cell2edgeSign = np.zeros((NC, E), dtype=np.bool)
            cell2edgeSign[edge2cell[:, 0], edge2cell[:, 2]] = True
        else:
            val = np.ones(NE, dtype=np.bool)
            cell2edgeSign = csr_matrix(
                    (val, (edge2cell[:, 0], range(NE))),
                    shape=(NC, NE), dtype=np.bool)
        return cell2edgeSign

    def cell_to_cell(self, return_sparse=False, return_boundary=True, return_array=False):
        """ Consctruct the neighbor information of cells
        """
        if return_array:                                                             
             return_sparse = False
             return_boundary = False
 
        NC = self.NC
        E = self.E
        edge2cell = self.edge2cell
        if (return_sparse == False) & (return_array == False):
            E = self.E
            cell2cell = np.zeros((NC, E), dtype=np.int)
            cell2cell[edge2cell[:, 0], edge2cell[:, 2]] = edge2cell[:, 1]
            cell2cell[edge2cell[:, 1], edge2cell[:, 3]] = edge2cell[:, 0]
            return cell2cell
        NE = self.NE
        val = np.ones((NE,), dtype=np.bool)
        if return_boundary:
            cell2cell = coo_matrix(
                    (val, (edge2cell[:, 0], edge2cell[:, 1])),
                    shape=(NC, NC), dtype=np.bool)
            cell2cell += coo_matrix(
                    (val, (edge2cell[:, 1], edge2cell[:, 0])),
                    shape=(NC, NC), dtype=np.bool)
            return cell2cell.tocsr()
        else:
            isInEdge = (edge2cell[:, 0] != edge2cell[:, 1])
            cell2cell = coo_matrix(
                    (val[isInEdge], (edge2cell[isInEdge, 0], edge2cell[isInEdge, 1])),
                    shape=(NC, NC), dtype=np.bool)
            cell2cell += coo_matrix(
                    (val[isInEdge], (edge2cell[isInEdge, 1], edge2cell[isInEdge, 0])),
                    shape=(NC, NC), dtype=np.bool)
            cell2cell = cell2cell.tocsr()
            if return_array == False:
                return cell2cell
            else:
                nn = cell2cell.sum(axis=1).reshape(-1)
                _, adj = cell2cell.nonzero()
                adjLocation = np.zeros(NC+1, dtype=np.int32)
                adjLocation[1:] = np.cumsum(nn)
                return adj.astype(np.int32), adjLocation

    def edge_to_node(self, sparse=False):
        N = self.N
        NE = self.NE

        edge = self.edge
        if sparse == False:
            return edge
        else:
            edge = self.edge
            I = np.repeat(range(NE), 2)
            J = edge.flatten()
            val = np.ones(2*NE, dtype=np.bool)
            edge2node = csr_matrix((val, (I, J)), shape=(NE, N), dtype=np.bool)
            return edge2node

    def edge_to_edge(self, sparse=False):
        edge2node = self.edge_to_node()
        return edge2node*edge2node.tranpose()

    def edge_to_cell(self, sparse=False):
        if sparse==False:
            return self.edge2cell
        else:
            NC = self.NC
            NE = self.NE
            I = np.repeat(range(NF), 2)
            J = self.edge2cell[:, [0, 1]].flatten()
            val = np.ones(2*NE, dtype=np.bool)
            face2cell = csr_matrix((val, (I, J)), shape=(NE, NC), dtype=np.bool)
            return face2cell 

    def node_to_node(self, return_array=False):
        """ The neighbor information of nodes
        """
        N = self.N
        NE = self.NE
        edge = self.edge
        I = edge.flatten()
        J = edge[:,[1,0]].flatten()
        val = np.ones((2*NE,), dtype=np.bool)
        node2node = csr_matrix((val, (I, J)), shape=(N, N),dtype=np.bool)
        if return_array == False:
            return node2node 
        else:
            nn = node2node.sum(axis=1).reshape(-1)
            _, adj = node2node.nonzero()
            adjLocation = np.zeros(N+1, dtype=np.int32)
            adjLocation[1:] = np.cumsum(nn)
            return adj.astype(np.int32), adjLocation

    def node_to_node_in_edge(self, N, edge):
        I = edge.flatten()
        J = edge[:, [1, 0]].flatten()
        val = np.ones(2*edge.shape[0], dtype=np.bool)
        node2node = csr_matrix((val, (I, J)), shape=(N, N), dtype=np.bool)
        return node2node

    def node_to_edge(self):
        N = self.N
        NE = self.NE
        
        edge = self.edge
        I = edge.flatten()
        J = np.repeat(range(NE), 2)
        val = np.ones(2*NE, dtype=np.bool)
        node2edge = csr_matrix((val, (I, J)), shape=(N, NE), dtype=np.bool)
        return node2edge

    def node_to_cell(self, localidx=False):
        """
        """
        N = self.N
        NC = self.NC
        V = self.V

        cell = self.cell

        I = cell.flatten() 
        J = np.repeat(range(NC), V)

        if localidx == True:
            val = ranges(V*np.ones(NC, dtype=np.int), start=1) 
            node2cell = csr_matrix((val, (I, J)), shape=(N, NC), dtype=np.int)
        else:
            val = np.ones(V*NC, dtype=np.bool)
            node2cell = csr_matrix((val, (I, J)), shape=(N, NC), dtype=np.bool)
        return node2cell


    def boundary_node_flag(self):
        N = self.N
        edge = self.edge
        isBdEdge = self.boundary_edge_flag()
        isBdPoint = np.zeros((N,), dtype=np.bool)
        isBdPoint[edge[isBdEdge,:]] = True
        return isBdPoint

    def boundary_edge_flag(self):
        edge2cell = self.edge2cell
        return edge2cell[:, 0] == edge2cell[:, 1]

    def boundary_edge(self):
        edge = self.edge
        return edge[self.boundary_edge_index()]

    def boundary_cell_flag(self):
        NC = self.NC
        edge2cell = self.edge2cell
        isBdCell = np.zeros((NC,), dtype=np.bool)
        isBdEdge = self.boundary_edge_flag()
        isBdCell[edge2cell[isBdEdge,0]] = True
        return isBdCell 

    def boundary_node_index(self):
        isBdPoint = self.boundary_node_flag()
        idx, = np.nonzero(isBdPoint)
        return idx 

    def boundary_edge_index(self):
        isBdEdge = self.boundary_edge_flag()
        idx, = np.nonzero(isBdEdge)
        return idx 

    def boundary_cell_index(self):
        isBdCell = self.boundary_cell_flag()
        idx, = np.nonzero(isBdCell)
        return idx 

