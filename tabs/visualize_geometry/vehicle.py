import numpy as np
import pyvista as pv


def generate_vtk_object(pts):
    n_r, n_a = pts.shape[0], pts.shape[1]
    n = n_a * (n_r - 1)
    X = pts.reshape(n_r * n_a, 3).astype(float)
    cells = write_azimuthal_cell_values(X, n, n_a).astype(int)

    # Build PyVista quad faces: [4, a, b, c, d, ...]
    faces = np.empty((n, 5), dtype=int)
    faces[:, 0] = 4
    faces[:, 1:] = cells

    return pv.PolyData(X, faces.ravel())


def write_azimuthal_cell_values(f, n_cells, n_a):
    rlap = 0
    adjacent_cells = np.zeros((n_cells, 4))

    for i in range(n_cells):
        if i == (n_a - 1 + n_a * rlap):
            b = i - (n_a - 1)
            c = i + 1
            rlap += 1
        else:
            b = i + 1
            c = i + n_a + 1
        a = i
        d = i + n_a
        adjacent_cells[i, 0] = a
        adjacent_cells[i, 1] = b
        adjacent_cells[i, 2] = c
        adjacent_cells[i, 3] = d
    return adjacent_cells
