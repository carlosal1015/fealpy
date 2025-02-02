import numpy as np
from .Quadrature import Quadrature
from .GaussLegendreQuadrature import GaussLegendreQuadrature
from .TriangleQuadrature import TriangleQuadrature


class PrismQuadrature(Quadrature):
    def __init__(self, index, dtype=np.float):
        q0 = TriangleQuadrature(index)
        q1 = GaussLegendreQuadrature(index)
        bc0, ws0 = q0.get_quadrature_points_and_weights()
        bc1, ws1 = q1.get_quadrature_points_and_weights()
        self.quadpts = (bc0, bc1)
        self.weights = (ws0, ws1)

    def number_of_quadrature_points(self):
        n0 = self.quadpts[0].shape[0]
        n1 = self.quadpts[1].shape[1]
        return n0*n1 
