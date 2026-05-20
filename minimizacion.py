"""
minimizacion.py
---------------
Implementación del Método Simplex con Gran M para problemas de MINIMIZACIÓN.
Soporta restricciones de tipo >=, <=, y =.

Lógica pura — sin GUI. Diseñado para ser llamado desde gui.py.

Proyecto: Método Simplex — IO1, UAGRM 2026
"""

import numpy as np


# ─────────────────────────────────────────
#  CONSTANTE M (penalización Grande)
# ─────────────────────────────────────────
M = 1_000_000


def simplex_gran_m(c, A, b, tipos_restriccion):
    """
    Resuelve un problema de MINIMIZACIÓN usando el Método Simplex con Gran M.

    Parámetros
    ----------
    c : list[float]
        Coeficientes de la función objetivo (minimización).
        Ejemplo: [2300, 2000, 3200, 1350, 1650, 4000]

    A : list[list[float]]
        Matriz de coeficientes de las restricciones (m restricciones x n variables).

    b : list[float]
        Lados derechos de las restricciones. Deben ser >= 0.

    tipos_restriccion : list[str]
        Tipo de cada restriccion: '>=' | '<=' | '='
        Ejemplo: ['=', '>=', '>=', '>=', '>=']

    Retorna
    -------
    dict con claves:
        'estado'      : 'optimo' | 'no_factible' | 'no_acotado'
        'x'           : list[float] -- valores de las variables originales
        'z'           : float       -- valor optimo de la funcion objetivo
        'iteraciones' : int         -- cantidad de iteraciones realizadas
        'mensaje'     : str         -- descripcion del resultado
    """

    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)

    m, n = A.shape  # m restricciones, n variables originales

    # ─────────────────────────────────────────
    #  FASE 1: Construir la tabla aumentada
    #  Añadir variables de holgura, exceso y artificiales
    # ─────────────────────────────────────────

    base = []             # índices de variables básicas iniciales
    artificiales = []     # índices de variables artificiales

    col = n               # siguiente columna disponible

    cols_holgura = []
    cols_artificial = []
    costos_extra = []

    for i, tipo in enumerate(tipos_restriccion):
        if tipo == '<=':
            # Variable de holgura s_i (+1)
            cols_holgura.append((i, col, +1))
            costos_extra.append(0)
            base.append(col)
            col += 1
            cols_artificial.append(None)

        elif tipo == '>=':
            # Variable de exceso e_i (-1) + artificial a_i (+1)
            cols_holgura.append((i, col, -1))
            costos_extra.append(0)
            col += 1

            cols_artificial.append((i, col))
            artificiales.append(col)
            costos_extra.append(M)
            base.append(col)
            col += 1

        elif tipo == '=':
            # Solo artificial a_i (+1)
            cols_holgura.append(None)
            cols_artificial.append((i, col))
            artificiales.append(col)
            costos_extra.append(M)
            base.append(col)
            col += 1

    total_vars = col

    # Armar vector de costos completo
    c_ext = np.concatenate([c, np.array(costos_extra, dtype=float)])

    # Construir tabla (m filas x total_vars+1 columnas, ultima = b)
    tabla = np.zeros((m, total_vars + 1))
    tabla[:, :n] = A
    tabla[:, -1] = b

    for info in cols_holgura:
        if info is not None:
            i_fila, j_col, signo = info
            tabla[i_fila, j_col] = signo

    for info in cols_artificial:
        if info is not None:
            i_fila, j_col = info
            tabla[i_fila, j_col] = 1

    # ─────────────────────────────────────────
    #  FASE 2: Iteraciones del Simplex
    # ─────────────────────────────────────────

    iteraciones = 0
    MAX_ITER = 1000

    while iteraciones < MAX_ITER:
        iteraciones += 1

        # Costos reducidos: z_j - c_j
        c_B = c_ext[base]
        z_row = c_B @ tabla[:, :-1]
        reducidos = z_row - c_ext

        # Optimalidad (minimizacion): todos reducidos <= 0
        if np.all(reducidos <= 1e-8):
            break

        # Variable entrante: mayor reducido positivo
        entrante = int(np.argmax(reducidos))

        # Cocientes minimos para variable saliente
        col_pivot = tabla[:, entrante]
        with np.errstate(divide='ignore', invalid='ignore'):
            cocientes = np.where(
                col_pivot > 1e-10,
                tabla[:, -1] / col_pivot,
                np.inf
            )

        if np.all(np.isinf(cocientes)):
            return {
                'estado': 'no_acotado',
                'x': [],
                'z': None,
                'iteraciones': iteraciones,
                'mensaje': 'El problema no esta acotado (solucion infinita).'
            }

        saliente = int(np.argmin(cocientes))

        # Pivoteo
        pivote = tabla[saliente, entrante]
        tabla[saliente] /= pivote
        for i in range(m):
            if i != saliente:
                tabla[i] -= tabla[i, entrante] * tabla[saliente]

        base[saliente] = entrante

    # ─────────────────────────────────────────
    #  FASE 3: Verificar factibilidad
    # ─────────────────────────────────────────

    for idx, var_base in enumerate(base):
        if var_base in artificiales:
            if tabla[idx, -1] > 1e-6:
                return {
                    'estado': 'no_factible',
                    'x': [],
                    'z': None,
                    'iteraciones': iteraciones,
                    'mensaje': 'El problema no tiene solucion factible.'
                }

    # ─────────────────────────────────────────
    #  FASE 4: Extraer solucion
    # ─────────────────────────────────────────

    x = np.zeros(total_vars)
    for idx, var_base in enumerate(base):
        x[var_base] = tabla[idx, -1]

    x_originales = x[:n]
    z = float(c @ x_originales)

    return {
        'estado': 'optimo',
        'x': list(x_originales),
        'z': z,
        'iteraciones': iteraciones,
        'mensaje': 'Solucion optima encontrada.'
    }


# ─────────────────────────────────────────
#  PROBLEMA PRECONFIGURADO: Vacas Lecheras
# ─────────────────────────────────────────

PROBLEMA_VACAS = {
    'nombre': 'Raciones Alimenticias para Vacas Lecheras',
    'variables': ['Maiz', 'Sorgo', 'Torta Soya', 'Afrechillo', 'Alfalfa', 'Hna. Hueso'],
    'unidad': 'ton',
    'c': [2300, 2000, 3200, 1350, 1650, 4000],
    'A': [
        [1,    1,    1,    1,    1,    1   ],
        [90,   100,  440,  150,  180,  0   ],
        [3300, 3150, 3200, 2450, 2100, 0   ],
        [25,   28,   60,   110,  250,  0   ],
        [0.2,  0.4,  2.5,  1.2,  14,   300 ],
    ],
    'b': [1, 160, 2600, 180, 6],
    'tipos': ['=', '>=', '>=', '>=', '>='],
    'restricciones': [
        'Balance de masa = 1 tonelada',
        'Proteina Bruta >= 160 kg/ton',
        'Energia Metabolizable >= 2600 Mcal/ton',
        'Fibra >= 180 kg/ton',
        'Calcio >= 6 kg/ton',
    ]
}


def resolver_vacas():
    """Atajo para resolver el problema de vacas con datos precargados."""
    p = PROBLEMA_VACAS
    return simplex_gran_m(p['c'], p['A'], p['b'], p['tipos'])


# ─────────────────────────────────────────
#  TEST RAPIDO: python minimizacion.py
# ─────────────────────────────────────────

if __name__ == '__main__':
    p = PROBLEMA_VACAS
    print(f"\n{'='*50}")
    print(f"  {p['nombre']}")
    print(f"{'='*50}")

    resultado = resolver_vacas()

    print(f"\nEstado     : {resultado['estado']}")
    print(f"Mensaje    : {resultado['mensaje']}")
    print(f"Iteraciones: {resultado['iteraciones']}")

    if resultado['estado'] == 'optimo':
        print(f"\nSolucion optima:")
        for nombre, valor in zip(p['variables'], resultado['x']):
            print(f"  {nombre:<18}: {valor:.6f} {p['unidad']}")
        print(f"\n  Costo minimo: Bs {resultado['z']:,.2f} / tonelada")
