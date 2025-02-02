
import numpy as np
from numpy.linalg import norm
from scipy.sparse import coo_matrix, csc_matrix, csr_matrix, spdiags, eye
from scipy.sparse.linalg import cg, inv, dsolve, spsolve
import pyamg

from ..functionspace.vem_space import VirtualElementSpace2d
from ..boundarycondition import DirichletBC
from ..vem import doperator
from ..quadrature import IntervalQuadrature, PolygonMeshIntegralAlg, GaussLobattoQuadrature


class SFCVEMModel2d():
    def __init__(self, pde, mesh, p=1, q=6):
        """
        Initialize a vem model for the simplified friction problem.

        Parameters
        ----------
        self: PoissonVEMModel object
        pde:  PDE Model object
        mesh: PolygonMesh object
        p: int
        q: the number of degrees

        See Also
        --------

        Notes
        -----
        """
        self.space = VirtualElementSpace2d(mesh, p)
        self.mesh = self.space.mesh
        self.pde = pde

        self.integrator = mesh.integrator(q)
        self.area = self.space.smspace.area


        self.uh = self.space.function() # the solution 
        self.lh = self.space.function() # \lambda_h 

        self.integralalg = PolygonMeshIntegralAlg(
                self.integrator,
                self.mesh,
                area=self.area,
                barycenter=self.space.smspace.barycenter)

        self.mat = doperator.basic_matrix(self.space, self.area)


    def reinit(self, mesh, p=None):
        if p is None:
            p = self.space.p
        self.space = VirtualElementSpace2d(mesh, p)
        self.mesh = self.space.mesh

        self.uh = self.space.function()
        self.lh = self.space.function()

        self.area = self.space.smspace.area
        self.integralalg = PolygonMeshIntegralAlg(
                self.integrator,
                self.mesh,
                area=self.area,
                barycenter=self.space.smspace.barycenter)

        self.mat = doperator.basic_matrix(self.space, self.area)

    def project_to_smspace(self, uh=None, ptype='H1'):
        if uh is None:
            uh = self.uh
        p = self.space.p
        cell2dof, cell2dofLocation = self.space.dof.cell2dof, self.space.dof.cell2dofLocation
        cd = np.hsplit(cell2dof, cell2dofLocation[1:-1])
        g = lambda x: x[0]@uh[x[1]]
        S = self.space.smspace.function()
        if ptype is 'H1':
            S[:] = np.concatenate(list(map(g, zip(self.mat.PI1, cd))))
        elif ptype is 'L2':
            S[:] = np.concatenate(list(map(g, zip(self.mat.PI0, cd))))
        else:
            raise ValueError("ptype value should be H1 or L2! But you input %s".format(ptype))
        return S

    def residual_estimator(self):

        mesh = self.mesh
        NE = mesh.number_of_edges()
        node = mesh.entity('node')
        edge = mesh.entity('edge')

        fh = self.integralalg.fun_integral(self.pde.source, True)/self.area
        def f(x, cellidx):
            val = (self.S.laplace_value(x, cellidx) - self.S.value(x, cellidx) + fh[cellidx])
            return val**2

        e0 = self.area*self.integralalg.integral(f, celltype=True)

        edge2cell = self.mesh.ds.edge_to_cell()
        isBdEdge = (edge2cell[:, 0] == edge2cell[:, 1])

        # 计算内部边跳量
        bc = mesh.entity_barycenter('edge')
        isContactEdge = self.pde.is_contact(bc)
        n = mesh.edge_unit_normal()
        h = np.sqrt(np.sum((node[edge[:, 0]] - node[edge[:, 1]])**2, axis=-1))


        # 获取区间积分公式
        qf = IntervalQuadrature(3)
        bcs, ws = qf.quadpts, qf.weights
        points = np.einsum('ij, kjm->ikm', bcs, node[edge])

        # 内部边上的积分
        lgrad = self.S.grad_value(points, cellidx=edge2cell[:, 0])
        rgrad = self.S.grad_value(points, cellidx=edge2cell[:, 1])
        e1 = np.zeros(NE, dtype=mesh.ftype)

        t0 = np.einsum(
            'ijm, jm->j',
            lgrad[:, ~isBdEdge] - rgrad[:, ~isBdEdge],
            n[~isBdEdge])
        e1[~isBdEdge] = t0**2*h[~isBdEdge]


        # 接触边界上的积分 
        ipoints = self.space.interpolation_points()
        edge2dof = self.space.dof.edge_to_dof()

        eta = self.pde.eta
        points = ipoints[edge2dof[isContactEdge]]
        lh = self.lh[edge2dof[isContactEdge]]
        lgrad = self.S.grad_value(points, cellidx=edge2cell[isContactEdge, 0])

        t0 = np.einsum('ijm, im->ij', lgrad, n[isContactEdge]) + eta*lh
        e1[isContactEdge] += np.einsum('ij, i->i', t0**2, h[isContactEdge])

        e1 *= h

        np.add.at(e0, edge2cell[:, 0], e1)
        np.add.at(e0, edge2cell[~isBdEdge, 1], e1[~isBdEdge])
        return np.sqrt(e0)

    def high_order_term(self):
        space = self.space
        area = self.area
        mat = self.mat

        G = mat.G
        PI0 = mat.PI0
        PI1 = mat.PI1
        D = mat.D

        cell2dof, cell2dofLocation = space.dof.cell2dof, space.dof.cell2dofLocation
        uh = self.uh[cell2dof]
        DD = np.vsplit(D, cell2dofLocation[1:-1])
        uh = np.hsplit(uh, cell2dofLocation[1:-1])

        def f0(x):
            val = (np.eye(x[1].shape[1]) - x[0]@x[1])@x[2]
            return np.sum(val*val)
        psi0 = sum(map(f0, zip(DD, PI1, uh)))

        def f1(x):
            val = (np.eye(x[1].shape[1]) - x[0]@x[1])@x[2]
            return x[3]*np.sum(val*val)
        psi1 = sum(map(f1, zip(DD, PI0, uh, area)))

        return psi0, psi1


    def get_left_matrix(self):
        space = self.space
        area = self.area
        A = doperator.stiff_matrix(space, area, mat=self.mat)
        M = doperator.mass_matrix(space, area, mat=self.mat)
        return A+M

    def get_right_vector(self):
        f = self.pde.source
        integral = self.integralalg.integral
        return doperator.source_vector(
                integral,
                f,
                self.space,
                self.mat.PI0)

    def get_lagrangian_multiplier_vector(self, cedge, cedge2dof):
        p = self.space.p
        node = self.mesh.node
        v = node[cedge[:, 1]] - node[cedge[:, 0]]
        l = np.sqrt(np.sum(v**2, axis=1))
        qf = GaussLobattoQuadrature(p + 1)
        bcs, ws = qf.quadpts, qf.weights
        lh = self.lh
        bb = np.einsum('i, ji, j->ji', ws, lh[cedge2dof], l)

        gdof = self.space.number_of_global_dofs()
        b = np.bincount(cedge2dof.flat, weights=bb.flat, minlength=gdof)
        return b

    def solve(self, rho=1, maxit=10000, tol=1e-8, uh=None, lh=None):
        if uh is not None:
            self.uh[:] = uh[:]

        if lh is not None:
            self.lh[:] = lh[:]

        uh = self.uh
        lh = self.lh

        space = self.space
        mesh = self.mesh

        edge = mesh.ds.edge
        edge2dof = space.dof.edge_to_dof()
        bc = mesh.entity_barycenter(etype='edge')
        isContactEdge = self.pde.is_contact(bc)

        edge = edge[isContactEdge]
        edge2dof = edge2dof[isContactEdge]

        gdof = space.number_of_global_dofs()
        isContactDof = np.zeros(gdof, dtype=np.bool)
        isContactDof[edge2dof] = True

        bc = DirichletBC(self.space, self.pde.dirichlet,
                is_dirichlet_dof=self.pde.is_dirichlet)

        A = self.get_left_matrix()
        b = self.get_right_vector()

        k = 0
        eta = self.pde.eta

        AD = bc.apply_on_matrix(A)
        ml = pyamg.ruge_stuben_solver(AD)
        while k < maxit:
            b1 = self.get_lagrangian_multiplier_vector(edge, edge2dof)
            bd = bc.apply_on_vector(b - eta*b1, A)
            uh0 = uh.copy()
            lh0 = lh.copy()
            uh[:] = ml.solve(bd, x0=uh, tol=1e-12, accel='cg').reshape(-1)
            lh[isContactDof] = np.clip(lh[isContactDof] + rho*eta*uh[isContactDof], -1, 1)
            e0 = np.max(np.abs(uh - uh0))
            e1 = np.max(np.abs(lh - lh0))
            #print('k:', k, 'error:', e0, e1)
            if e0 < tol:
                break
            k += 1

        print('k:', k, 'error:', e0, e1)
        self.S = self.project_to_smspace(uh)

    def l2_error(self):
        e = self.uh - self.uI
        return np.sqrt(np.mean(e**2))

    def uIuh_error(self):
        e = self.uh - self.uI
        return np.sqrt(e@self.A@e)

    def L2_error(self, u):
        uh = self.S.value
        def f(x, cellidx):
            return (u(x, cellidx) - uh(x, cellidx))**2

        e = self.integralalg.integral(f, celltype=True)
        return np.sqrt(e.sum())

    def H1_semi_error(self, gu):
        guh = self.S.grad_value
        def f(x, cellidx):
            return (gu(x, cellidx) - guh(x, cellidx))**2
        e = self.integralalg.integral(f, celltype=True)
        return np.sqrt(e.sum())

