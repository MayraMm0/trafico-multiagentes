def bbox(ruta, swapyz=True):
    xs, ys, zs = [], [], []
    for linea in open(ruta):
        if linea.startswith('v '):
            x, y, z = map(float, linea.split()[1:4])
            if swapyz:
                y, z = z, y
            xs.append(x); ys.append(y); zs.append(z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

for nombre in ["carroceria", "llanta_FL", "llanta_FR", "llantas_traseras"]:
    bx, by, bz = bbox(nombre + ".obj")
    print(nombre, "X", bx, "Y", by, "Z", bz)