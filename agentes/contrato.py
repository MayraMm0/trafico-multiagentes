# Contrato compartido entre la lógica y la parte gráfica.
T_PASO = 0.5
DIST_SEG = 2

AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE = (
    'AVANZANDO', 'DETENIDO', 'ESPERANDO_PASO', 'CEDIENDO', 'EN_CRUCE'
)

# Maniobras (se conservan los nombres definidos por el mapa).
from graficas.ciudad.mapa import RECTO, IZQ, DER

SOLICITAR_PASO = 'SOLICITAR_PASO'
PASAR = 'PASAR'
INFORMAR_SALIDA = 'INFORMAR_SALIDA'
CAMBIAR_FASE = 'CAMBIAR_FASE'

# Performativas FIPA usadas en el reporte y en los mensajes.
REQUEST = 'REQUEST'
AGREE = 'AGREE'
INFORM = 'INFORM'

PERFORMATIVAS = {
    SOLICITAR_PASO: REQUEST,
    PASAR: AGREE,
    INFORMAR_SALIDA: INFORM,
    CAMBIAR_FASE: REQUEST,
}
