import numpy as np

class GaussLegendreQuadrture():
    def __init__(self, k):
        if k == 1:
            A = np.array([[0, 2]], dtype=np.float)
        if k == 2:
            A = np.array([
                [-0.5773502691896257645091488, 	1.0000000000000000000000000],
                [0.5773502691896257645091488, 	1.0000000000000000000000000]], dtype=np.float)
        if k == 3:
            A = np.array([
                [-0.7745966692414833770358531, 	0.5555555555555555555555556],
                [0, 	                        0.8888888888888888888888889],
                [0.7745966692414833770358531, 	0.5555555555555555555555556]], dtype=np.float)
        if k == 4:
            A = np.array([
                [-0.8611363115940525752239465, 	0.3478548451374538573730639],
                [-0.3399810435848562648026658, 	0.6521451548625461426269361],
                [0.3399810435848562648026658, 	0.6521451548625461426269361],
                [0.8611363115940525752239465, 	0.3478548451374538573730639]], dtype=np.float)
        if k == 5:
            A = np.array([
                [-0.9061798459386639927976269, 	0.2369268850561890875142640],
                [-0.5384693101056830910363144, 	0.4786286704993664680412915],
                [0, 	                        0.5688888888888888888888889],
                [0.5384693101056830910363144, 	0.4786286704993664680412915],
                [0.9061798459386639927976269, 	0.2369268850561890875142640]], dtype=np.float)
        if k == 6:
            A = np.array([
                [-0.9324695142031520278123016, 	0.1713244923791703450402961],
                [-0.6612093864662645136613996, 	0.3607615730481386075698335],
                [-0.2386191860831969086305017, 	0.4679139345726910473898703],
                [ 0.2386191860831969086305017, 	0.4679139345726910473898703],
                [ 0.6612093864662645136613996, 	0.3607615730481386075698335],
                [ 0.9324695142031520278123016, 	0.1713244923791703450402961]], dtype=np.float)
        if k == 7:
            A = np.array([
                [-0.9491079123427585245261897, 	0.1294849661688696932706114]
                [-0.7415311855993944398638648, 	0.2797053914892766679014678],
                [-0.4058451513773971669066064, 	0.3818300505051189449503698],
                [ 0,                            0.4179591836734693877551020],
                [ 0.4058451513773971669066064, 	0.3818300505051189449503698],
                [ 0.7415311855993944398638648, 	0.2797053914892766679014678],
                [ 0.9491079123427585245261897, 	0.1294849661688696932706114]], dtype=np.float)
        if k == 8:
            A = np.array([
                [-0.9602898564975362316835609, 	0.1012285362903762591525314],
                [-0.7966664774136267395915539, 	0.2223810344533744705443560],
                [-0.5255324099163289858177390, 	0.3137066458778872873379622],
                [-0.1834346424956498049394761, 	0.3626837833783619829651504],
                [ 0.1834346424956498049394761, 	0.3626837833783619829651504],
                [ 0.5255324099163289858177390, 	0.3137066458778872873379622],
                [ 0.7966664774136267395915539, 	0.2223810344533744705443560],
                [ 0.9602898564975362316835609, 	0.1012285362903762591525314]], dtype=np.float)
        if k == 9:
            A = np.array([
                [-0.9681602395076260898355762, 	0.0812743883615744119718922],
                [-0.8360311073266357942994298, 	0.1806481606948574040584720],
                [-0.6133714327005903973087020, 	0.2606106964029354623187429],
                [-0.3242534234038089290385380, 	0.3123470770400028400686304],
                [ 0, 	                        0.3302393550012597631645251],
                [ 0.3242534234038089290385380, 	0.3123470770400028400686304],
                [ 0.6133714327005903973087020, 	0.2606106964029354623187429],
                [ 0.8360311073266357942994298, 	0.1806481606948574040584720],
                [ 0.9681602395076260898355762, 	0.0812743883615744119718922]], dtype=np.float)

        if k == 10:
            A = np.array([
                [-0.9739065285171717200779640, 	0.0666713443086881375935688],
                [-0.8650633666889845107320967, 	0.1494513491505805931457763],
                [-0.6794095682990244062343274, 	0.2190863625159820439955349],
                [-0.4333953941292471907992659, 	0.2692667193099963550912269],
                [-0.1488743389816312108848260, 	0.2955242247147528701738930],
                [ 0.1488743389816312108848260, 	0.2955242247147528701738930],
                [ 0.4333953941292471907992659, 	0.2692667193099963550912269],
                [ 0.6794095682990244062343274, 	0.2190863625159820439955349],
                [ 0.8650633666889845107320967, 	0.1494513491505805931457763],
                [ 0.9739065285171717200779640, 	0.0666713443086881375935688]], dtype=np.float)

        if k == 11:
            A = np.array([
                [-0.9782286581460569928039,   0.0556685671161736664828],
                [-0.8870625997680952990752,   0.1255803694649046246347],
                [-0.7301520055740493240934,   0.1862902109277342514261],
                [-0.5190961292068118159257,   0.2331937645919904799185],
                [-0.2695431559523449723315,   0.2628045445102466621807],
                [0,                           0.272925086777900630714],
                [0.2695431559523449723315,    0.2628045445102466621807],
                [0.5190961292068118159257,    0.2331937645919904799185],
                [0.7301520055740493240934,    0.1862902109277342514261],
                [0.8870625997680952990752,    0.1255803694649046246347],
                [0.9782286581460569928039,    0.0556685671161736664828]], dtype=np.float)

        if k == 12:
            A = np.array([
                [-0.9815606342467192506906,   0.0471753363865118271946],
                [-0.9041172563704748566785,   0.1069393259953184309603],
                [-0.769902674194304687037,    0.1600783285433462263347],
                [-0.5873179542866174472967,   0.2031674267230659217491],
                [-0.3678314989981801937527,   0.233492536538354808761],
                [-0.1252334085114689154724,   0.2491470458134027850006],
                [0.1252334085114689154724,    0.2491470458134027850006],
                [0.3678314989981801937527,    0.233492536538354808761],
                [0.5873179542866174472967,    0.203167426723065921749],
                [0.7699026741943046870369,    0.160078328543346226335],
                [0.9041172563704748566785,    0.1069393259953184309603],
                [0.9815606342467192506906,    0.0471753363865118271946]], dtype=np.float)
                

        numpts = A.shape[0]
        self.quadpts = np.zeros((numpts, 2), dtype=np.float)
        self.quadpts[:, 0] = (A[:,0] + 1)/2.0
        self.quadpts[:, 1] = 1 - self.quadpts[:, 0]
        self.weights = A[:, 1]/2

    def get_number_of_quad_points(self):
        return self.quadpts.shape[0] 

    def get_gauss_point_and_weight(self, i):
        return self.quadpts[i,:], self.weights[i] 

