"""
dualidad.py
-----------
Conversion Primal -> Dual para problemas de Programacion Lineal.

Reglas de transformacion (sin restricciones de igualdad):

  PRIMAL (MAX)              DUAL (MIN)
  ─────────────────────     ─────────────────────
  Maximizar c·x             Minimizar b·w
  Restricciones Ax <= b     Restricciones A^T·w >= c
  x >= 0                    w >= 0

  PRIMAL (MIN)              DUAL (MAX)
  ─────────────────────     ─────────────────────
  Minimizar c·x             Maximizar b·w
  Restricciones Ax >= b     Restricciones A^T·w <= c
  x >= 0                    w >= 0

Logica pura — sin GUI. Disenado para ser llamado desde gui.py.

Proyecto: Metodo Simplex — IO1, UAGRM 2026
"""

import numpy as np


def convertir_dual(tipo_primal, c, A, b, tipos_restriccion,
                   nombres_variables=None, nombres_restricciones=None):
    """
    Convierte un problema primal a su dual.

    Parametros
    ----------
    tipo_primal : str
        'max' o 'min' — tipo del problema primal.

    c : list[float]
        Coeficientes de la funcion objetivo del primal.

    A : list[list[float]]
        Matriz de coeficientes de restricciones (m x n).

    b : list[float]
        Lados derechos de las restricciones.

    tipos_restriccion : list[str]
        Tipo de cada restriccion del primal: '>=' o '<='
        Para MAX se esperan '<=', para MIN se esperan '>='.

    nombres_variables : list[str], opcional
        Nombres de las variables del primal (x1, x2, ...).
        Si no se pasan, se generan automaticamente.

    nombres_restricciones : list[str], opcional
        Nombres de las restricciones del primal.
        Si no se pasan, se generan automaticamente.

    Retorna
    -------
    dict con claves:
        'tipo_dual'              : str         — 'max' o 'min'
        'c_dual'                 : list[float] — coeficientes f.obj. dual
        'A_dual'                 : list[list]  — matriz dual
        'b_dual'                 : list[float] — lados derechos dual
        'tipos_dual'             : list[str]   — tipos de restriccion dual
        'nombres_vars_dual'      : list[str]   — nombres variables duales (w1, w2...)
        'nombres_rest_dual'      : list[str]   — nombres restricciones duales
        'n_vars_dual'            : int         — numero de variables duales
        'n_rest_dual'            : int         — numero de restricciones duales
        'error'                  : str | None  — mensaje si hay problema
    """

    tipo_primal = tipo_primal.lower().strip()

    # ── Validaciones basicas ──────────────────────────────────────────────
    if tipo_primal not in ('max', 'min'):
        return _error("tipo_primal debe ser 'max' o 'min'.")

    A = np.array(A, dtype=float)
    c = np.array(c, dtype=float)
    b = np.array(b, dtype=float)
    m, n = A.shape  # m restricciones, n variables

    if len(c) != n:
        return _error(f"c tiene {len(c)} elementos pero A tiene {n} columnas.")
    if len(b) != m:
        return _error(f"b tiene {len(b)} elementos pero A tiene {m} filas.")
    if len(tipos_restriccion) != m:
        return _error(f"tipos_restriccion tiene {len(tipos_restriccion)} elementos pero hay {m} restricciones.")

    for t in tipos_restriccion:
        if t not in ('<=', '>='):
            return _error(f"Tipo de restriccion '{t}' no valido. Solo se aceptan '<=' y '>='.")

    # ── Nombres por defecto ───────────────────────────────────────────────
    if nombres_variables is None:
        nombres_variables = [f"x{i+1}" for i in range(n)]
    if nombres_restricciones is None:
        nombres_restricciones = [f"Restriccion {i+1}" for i in range(m)]

    # ── Transformacion ────────────────────────────────────────────────────
    # Las variables duales corresponden a las restricciones del primal.
    # Las restricciones duales corresponden a las variables del primal.
    #
    # Dual de MAX (Ax <= b, max cx):  min b·w,  A^T·w >= c,  w >= 0
    # Dual de MIN (Ax >= b, min cx):  max b·w,  A^T·w <= c,  w >= 0

    A_dual = A.T.tolist()     # (n x m) — traspuesta
    c_dual = b.tolist()       # coeficientes f.obj. dual = b primal
    b_dual = c.tolist()       # lados derechos dual = c primal

    if tipo_primal == 'max':
        tipo_dual = 'min'
        tipos_dual = ['>='] * n      # n restricciones duales, todas >=

    else:  # min
        tipo_dual = 'max'
        tipos_dual = ['<='] * n      # n restricciones duales, todas <=

    # Nombres de variables duales: w1, w2, ... (una por restriccion primal)
    nombres_vars_dual = [f"w{i+1}" for i in range(m)]

    # Nombres de restricciones duales: una por variable primal
    nombres_rest_dual = [f"Dual de {nombres_variables[j]}" for j in range(n)]

    return {
        'tipo_dual'          : tipo_dual,
        'c_dual'             : c_dual,
        'A_dual'             : A_dual,
        'b_dual'             : b_dual,
        'tipos_dual'         : tipos_dual,
        'nombres_vars_dual'  : nombres_vars_dual,
        'nombres_rest_dual'  : nombres_rest_dual,
        'n_vars_dual'        : m,    # vars duales = restricciones primal
        'n_rest_dual'        : n,    # restricciones duales = vars primal
        'error'              : None,
    }


def formatear_dual(resultado_dual, decimales=4):
    """
    Genera un texto legible del problema dual para mostrar en la GUI.

    Parametros
    ----------
    resultado_dual : dict
        Salida de convertir_dual().
    decimales : int
        Cifras decimales para los coeficientes.

    Retorna
    -------
    str con la formulacion del dual lista para mostrar.
    """
    if resultado_dual.get('error'):
        return f"Error: {resultado_dual['error']}"

    d = resultado_dual
    tipo = d['tipo_dual'].upper()
    c    = d['c_dual']
    A    = d['A_dual']
    b    = d['b_dual']
    tipos = d['tipos_dual']
    wvars = d['nombres_vars_dual']

    lineas = []

    # Funcion objetivo
    fo = " + ".join(
        f"{round(c[i], decimales)}{wvars[i]}" for i in range(len(c))
    )
    lineas.append(f"{tipo}  Z = {fo}")
    lineas.append("")
    lineas.append("Sujeto a:")

    # Restricciones
    for j, fila in enumerate(A):
        terminos = " + ".join(
            f"{round(fila[k], decimales)}{wvars[k]}" for k in range(len(fila))
        )
        lineas.append(f"  {terminos}  {tipos[j]}  {round(b[j], decimales)}")

    # No negatividad
    lineas.append("")
    no_neg = ", ".join(wvars) + "  >=  0"
    lineas.append(f"  {no_neg}")

    return "\n".join(lineas)


# ── Utilidad interna ──────────────────────────────────────────────────────

def _error(mensaje):
    return {
        'tipo_dual'          : None,
        'c_dual'             : [],
        'A_dual'             : [],
        'b_dual'             : [],
        'tipos_dual'         : [],
        'nombres_vars_dual'  : [],
        'nombres_rest_dual'  : [],
        'n_vars_dual'        : 0,
        'n_rest_dual'        : 0,
        'error'              : mensaje,
    }


# ── TEST RAPIDO: python dualidad.py ──────────────────────────────────────

if __name__ == '__main__':

    # Ejemplo: Primal de MINIMIZACION (problema de vacas, simplificado a 2 vars)
    # MIN  2300x1 + 1650x5
    # s.a. x1  + x5  >= 1      (balance masa)
    #      90x1 + 180x5 >= 160  (proteina)
    #      x1, x5 >= 0

    print("=" * 55)
    print("  EJEMPLO: Primal MIN -> Dual MAX")
    print("=" * 55)

    tipo_p = 'min'
    c_p    = [2300, 1650]
    A_p    = [[1,   1  ],
              [90,  180 ]]
    b_p    = [1, 160]
    tipos_p = ['>=', '>=']
    vars_p  = ['x1 (Maiz)', 'x5 (Alfalfa)']
    rest_p  = ['Balance masa', 'Proteina']

    print("\nPRIMAL:")
    print(f"  MIN  {c_p[0]}x1 + {c_p[1]}x5")
    print(f"  s.a. x1 + x5 >= {b_p[0]}")
    print(f"       {A_p[1][0]}x1 + {A_p[1][1]}x5 >= {b_p[1]}")
    print(f"       x1, x5 >= 0")

    dual = convertir_dual(tipo_p, c_p, A_p, b_p, tipos_p, vars_p, rest_p)

    print("\nDUAL:")
    print(formatear_dual(dual))

    print("\n--- Datos raw del dual ---")
    print(f"tipo_dual : {dual['tipo_dual']}")
    print(f"c_dual    : {dual['c_dual']}")
    print(f"A_dual    : {dual['A_dual']}")
    print(f"b_dual    : {dual['b_dual']}")
    print(f"tipos_dual: {dual['tipos_dual']}")
