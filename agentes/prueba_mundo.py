# Prueba automática del MundoModelo.  Correr desde la raíz del repo:
#     python -m agentes.prueba_mundo
# Cada línea dice OK o FALLA y por qué.  No abre ventana (no usa OpenGL).
from agentes.mundoModelo import MundoModelo
from graficas.ciudad.mapa import MAPA, FLECHAS, SEMAFOROS

N_COCHES, PASOS = 20, 400
fallas = 0


def revisar(cond, texto):
    global fallas
    print(('  OK    ' if cond else '  FALLA ') + texto)
    fallas += 0 if cond else 1


print(f'MundoModelo con {N_COCHES} coches, {PASOS} pasos')
modelo = MundoModelo({'n_coches': N_COCHES, 'steps': 10**9, 'seed': 1})
s0 = modelo.estado_inicial()

print('\n1) Snapshot inicial')
revisar(isinstance(s0, dict) and {'t', 'coches', 'semaforos'} <= set(s0),
        "estado_inicial() regresa un dict con 't', 'coches' y 'semaforos'")
revisar(len(s0['coches']) == N_COCHES, f"hay {N_COCHES} coches (hay {len(s0['coches'])})")
ids_mapa = sorted(s['id'] for s in SEMAFOROS)
revisar(sorted(s0['semaforos']) == ids_mapa,
        f"los semáforos usan los ids del mapa {ids_mapa[0]}-{ids_mapa[-1]} (sid, no el id de AgentPy)")
revisar(all(v == 'ROJO' for v in s0['semaforos'].values()), "todos los semáforos arrancan en ROJO")
pos0 = [(c['f'], c['c']) for c in s0['coches']]
revisar(len(set(pos0)) == len(pos0), "ningún par de coches arranca en la misma celda")
revisar(all(MAPA[f][c] in FLECHAS for f, c in pos0), "todos arrancan sobre una celda con flecha (fuera de cruces)")

print(f'\n2) {PASOS} pasos')
choques, t_ok, fuera = 0, True, 0
for i in range(1, PASOS + 1):
    s = modelo.paso()
    t_ok &= (s['t'] == i)
    pos = [(c['f'], c['c']) for c in s['coches']]
    choques += len(pos) - len(set(pos))
    fuera += sum(1 for f, c in pos if not (0 <= f < len(MAPA) and 0 <= c < len(MAPA[0])))
revisar(t_ok, "paso() avanza t de 1 en 1")
revisar(choques == 0, f"nunca hay dos coches en la misma celda (hubo {choques})")
revisar(fuera == 0, f"ningún coche queda fuera del mapa (hubo {fuera})")
revisar(len(s['coches']) == N_COCHES, "el número de coches se mantiene (n constante)")
rep = getattr(modelo, 'reapariciones', None)
revisar(rep is not None and rep > 0, f"los coches salen y reaparecen (reapariciones = {rep})")
revisar(len({c['id'] for c in s['coches']}) == N_COCHES, "los ids de los coches no se repiten")

print('\n' + ('TODO BIEN' if fallas == 0 else f'{fallas} prueba(s) fallaron'))