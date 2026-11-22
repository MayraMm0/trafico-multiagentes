# Contrato compartido entre lo lógico y lo gráfico: AgenteCoche <-> Coche

T_PASO = 0.5 # Segundos que dura un paso del modelo
DIST_SEG = 2 # celdas libres que necesita enfrente para avanzar

# Estádos lógicos del coche
AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE = (
    'AVANZANDO', 'DETENIDO', 'ESPERANDO_PASO', 'CEDIENDO', 'EN_CRUCE')

# Maniobras
RECTO, IZQ, DER = 'RECTO', 'IZQ', 'DER'
from graficas.ciudad.mapa import RECTO, IZQ, DER



# Tipos de mensaje (compartido con Coordinador)
SOLICITAR_PASO, PASAR, INFORMAR_SALIDA, CAMBIAR_FASE = (
    'SOLICITAR_PASO', 'PASAR', 'INFORMAR_SALIDA', 'CAMBIAR_FASE')
