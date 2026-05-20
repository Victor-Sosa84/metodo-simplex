"""
maximizacion.py
---------------
Implementacion del Metodo Simplex para problemas de MAXIMIZACION.
Usa Dos Fases para manejar restricciones >= correctamente.
Soporta restricciones de tipo >= y <=.

Logica pura — sin GUI. Disenado para ser llamado desde gui.py.

Proyecto: Metodo Simplex — IO1, UAGRM 2026
"""

import numpy as np

M = 1_000_000


def _construir_tabla(A, b, tipos_restriccion):
    """
    Construye la tabla aumentada con holguras/excesos/artificiales.
    Orden: variables originales | excesos/holguras | artificiales
    Retorna: tabla, base, artificiales, total_vars, cols_info
    """
    m, n = A.shape
    base = []
    artificiales = []

    # Paso 1: holguras y excesos
    col = n
    cols_holgura = []
    costos_holgura = []
    for i, tipo in enumerate(tipos_restriccion):
        if tipo == '<=':
            cols_holgura.append((i, col, +1))
            costos_holgura.append(0)
            col += 1
        elif tipo == '>=':
            cols_holgura.append((i, col, -1))
            costos_holgura.append(0)
            col += 1
        else:
            cols_holgura.append(None)

    # Paso 2: artificiales
    cols_artificial = []
    costos_artificiales = []
    for i, tipo in enumerate(tipos_restriccion):
        if tipo in ('>=', '='):
            cols_artificial.append((i, col))
            artificiales.append(col)
            costos_artificiales.append(0)
            col += 1
        else:
            cols_artificial.append(None)

    total_vars = col

    # Base inicial
    for i, tipo in enumerate(tipos_restriccion):
        if tipo == '<=':
            for h in cols_holgura:
                if h and h[0] == i:
                    base.append(h[1])
                    break
        else:
            for art in cols_artificial:
                if art and art[0] == i:
                    base.append(art[1])
                    break

    # Construir tabla
    tabla = np.zeros((m, total_vars + 1))
    tabla[:, :n] = A
    tabla[:, -1] = b
    for h in cols_holgura:
        if h:
            i_fila, j_col, signo = h
            tabla[i_fila, j_col] = signo
    for art in cols_artificial:
        if art:
            i_fila, j_col = art
            tabla[i_fila, j_col] = 1

    return tabla, base, artificiales, total_vars


def _pivotear(tabla, base, entrante, m):
    col_pivot = tabla[:, entrante]
    with np.errstate(divide='ignore', invalid='ignore'):
        cocientes = np.where(col_pivot > 1e-10, tabla[:, -1] / col_pivot, np.inf)
    if np.all(np.isinf(cocientes)):
        return False, cocientes
    saliente = int(np.argmin(cocientes))
    pivote = tabla[saliente, entrante]
    tabla[saliente] /= pivote
    for i in range(m):
        if i != saliente:
            tabla[i] -= tabla[i, entrante] * tabla[saliente]
    base[saliente] = entrante
    return True, cocientes


def _fase1(tabla, base, artificiales, m, total_vars):
    """
    Fase 1: minimizar suma de artificiales.
    Retorna True si factible (todas artificiales = 0).
    """
    # Funcion objetivo fase 1: minimizar suma de artificiales
    c_f1 = np.zeros(total_vars)
    for idx in artificiales:
        c_f1[idx] = 1.0

    iteraciones = 0
    MAX_ITER = 1000
    while iteraciones < MAX_ITER:
        iteraciones += 1
        c_B = c_f1[base]
        z_row = c_B @ tabla[:, :-1]
        reducidos = z_row - c_f1
        if np.all(reducidos <= 1e-8):
            break
        entrante = int(np.argmax(reducidos))
        ok, _ = _pivotear(tabla, base, entrante, m)
        if not ok:
            break

    # Verificar factibilidad
    for idx, var_base in enumerate(base):
        if var_base in artificiales and tabla[idx, -1] > 1e-6:
            return False
    return True


def _fase2(tabla, base, c, artificiales, m, total_vars, n):
    """
    Fase 2: maximizar c·x con tabla factible.
    """
    # Sacar artificiales de base si siguen ahi con valor 0
    # (reemplazar con variable no basica que tenga coef != 0)
    for idx, var_base in enumerate(base):
        if var_base in artificiales:
            for j in range(n):
                if abs(tabla[idx, j]) > 1e-8:
                    base[idx] = j
                    pivote = tabla[idx, j]
                    tabla[idx] /= pivote
                    for i in range(m):
                        if i != idx:
                            tabla[i] -= tabla[i, j] * tabla[idx]
                    break

    # Funcion objetivo fase 2 (maximizacion = minimizar -c)
    c_ext = np.zeros(total_vars)
    c_ext[:n] = -c  # negado porque usamos criterio de minimizacion

    iteraciones = 0
    MAX_ITER = 1000
    while iteraciones < MAX_ITER:
        iteraciones += 1
        c_B = c_ext[base]
        z_row = c_B @ tabla[:, :-1]
        reducidos = z_row - c_ext
        if np.all(reducidos <= 1e-8):
            break
        entrante = int(np.argmax(reducidos))
        ok, cocientes = _pivotear(tabla, base, entrante, m)
        if not ok:
            return 'no_acotado', iteraciones
    return 'optimo', iteraciones


def simplex_maximizacion(c, A, b, tipos_restriccion):
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    m, n = A.shape

    tabla, base, artificiales, total_vars = _construir_tabla(A, b, tipos_restriccion)

    if artificiales:
        if not _fase1(tabla, base, artificiales, m, total_vars):
            return {
                'estado': 'no_factible', 'x': [], 'z': None,
                'iteraciones': 0,
                'mensaje': 'El problema no tiene solucion factible.'
            }

    estado, iteraciones = _fase2(tabla, base, c, artificiales, m, total_vars, n)

    if estado == 'no_acotado':
        return {
            'estado': 'no_acotado', 'x': [], 'z': None,
            'iteraciones': iteraciones,
            'mensaje': 'El problema no esta acotado (solucion infinita).'
        }

    x = np.zeros(total_vars)
    for idx, var_base in enumerate(base):
        x[var_base] = tabla[idx, -1]
    x_orig = x[:n]
    z = float(c @ x_orig)

    return {
        'estado': 'optimo',
        'x': list(x_orig),
        'z': z,
        'iteraciones': iteraciones,
        'mensaje': 'Solucion optima encontrada.'
    }


# ─────────────────────────────────────────
#  FUNCION CON PASOS
# ─────────────────────────────────────────

def simplex_maximizacion_pasos(c, A, b, tipos_restriccion):
    c = np.array(c, dtype=float)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    m, n = A.shape

    tabla, base, artificiales, total_vars = _construir_tabla(A, b, tipos_restriccion)

    headers = [f"x{j+1}" for j in range(total_vars)]
    headers.append("b")

    tiene_artificiales = len(artificiales) > 0

    # Separar costos para Z y M
    c_ext_max = np.zeros(total_vars)
    c_ext_max[:n] = -c
    c_normal = c_ext_max.copy()
    c_m = np.zeros(total_vars)
    for idx in artificiales:
        c_m[idx] = 1.0

    def snapshot(titulo, c_obj):
        c_B_n = c_normal[base]
        z_row_n = c_B_n @ tabla[:, :-1]
        fila_z = z_row_n - c_normal
        z_rhs = -float(c_B_n @ tabla[:, -1])

        if tiene_artificiales:
            c_B_m = c_m[base]
            z_row_m = c_B_m @ tabla[:, :-1]
            fila_m = z_row_m - c_m
            m_rhs = -float(c_B_m @ tabla[:, -1])
            mat = np.vstack([tabla,
                             np.append(fila_z, z_rhs),
                             np.append(fila_m, m_rhs)])
            base_labels = [f"x{b+1}" for b in base] + ['Z', 'M']
        else:
            mat = np.vstack([tabla, np.append(fila_z, z_rhs)])
            base_labels = [f"x{b+1}" for b in base] + ['Z']

        return {
            'titulo': titulo,
            'headers': headers,
            'base': base_labels,
            'matriz': mat.copy()
        }

    pasos = [snapshot("Tabla Inicial", c_ext_max)]

    # Fase 1 con pasos si hay artificiales
    if artificiales:
        c_f1 = np.zeros(total_vars)
        for idx in artificiales:
            c_f1[idx] = 1.0

        iter_f1 = 0
        MAX_ITER = 1000
        while iter_f1 < MAX_ITER:
            iter_f1 += 1
            c_B = c_f1[base]
            z_row = c_B @ tabla[:, :-1]
            reducidos = z_row - c_f1
            if np.all(reducidos <= 1e-8):
                break
            entrante = int(np.argmax(reducidos))
            ok, _ = _pivotear(tabla, base, entrante, m)
            if not ok:
                break
            pasos.append(snapshot(f"Iteracion {iter_f1}", c_ext_max))

        # Verificar factibilidad
        for idx, var_base in enumerate(base):
            if var_base in artificiales and tabla[idx, -1] > 1e-6:
                return {
                    'estado': 'no_factible', 'x': [], 'z': None,
                    'iteraciones': iter_f1,
                    'mensaje': 'El problema no tiene solucion factible.',
                    'pasos': pasos
                }

        # Sacar artificiales de base
        for idx, var_base in enumerate(base):
            if var_base in artificiales:
                for j in range(n):
                    if abs(tabla[idx, j]) > 1e-8:
                        base[idx] = j
                        pivote = tabla[idx, j]
                        tabla[idx] /= pivote
                        for i in range(m):
                            if i != idx:
                                tabla[i] -= tabla[i, j] * tabla[idx]
                        break

    # Fase 2
    iter_f2 = 0
    MAX_ITER = 1000
    while iter_f2 < MAX_ITER:
        iter_f2 += 1
        c_B = c_ext_max[base]
        z_row = c_B @ tabla[:, :-1]
        reducidos = z_row - c_ext_max
        if np.all(reducidos <= 1e-8):
            break
        entrante = int(np.argmax(reducidos))
        ok, _ = _pivotear(tabla, base, entrante, m)
        if not ok:
            return {
                'estado': 'no_acotado', 'x': [], 'z': None,
                'iteraciones': iter_f2,
                'mensaje': 'El problema no esta acotado.',
                'pasos': pasos
            }
        pasos.append(snapshot(f"Iteracion {(len(pasos))}", c_ext_max))

    x = np.zeros(total_vars)
    for idx, var_base in enumerate(base):
        x[var_base] = tabla[idx, -1]
    x_orig = x[:n]
    z = float(c @ x_orig)

    return {
        'estado': 'optimo',
        'x': list(x_orig),
        'z': z,
        'iteraciones': iter_f2,
        'mensaje': 'Solucion optima encontrada.',
        'pasos': pasos
    }


if __name__ == '__main__':
    print("=== Test 1: Optimo normal ===")
    res = simplex_maximizacion_pasos([5,4],[[6,4],[1,2]],[24,6],['<=','<='])
    print(f"Estado: {res['estado']}, Z: {res['z']}, x: {res['x']}")

    print("\n=== Test 2: No acotado ===")
    res = simplex_maximizacion_pasos([3,2],[[0,2],[1,1]],[6,2],['<=','>='])
    print(f"Estado: {res['estado']}")

    print("\n=== Test 3: No factible ===")
    res = simplex_maximizacion_pasos([2,3],[[1,1],[1,1]],[2,6],['<=','>='])
    print(f"Estado: {res['estado']}")

    print("\n=== Test 4: Con restriccion >= ===")
    res = simplex_maximizacion_pasos([4,5],[[1,2],[1,1]],[20,15],['<=','<='])
    print(f"Estado: {res['estado']}, Z: {res['z']}, x: {res['x']}")