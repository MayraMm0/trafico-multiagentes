# Contrato compartido entre lo lógico y lo gráfico: AgenteCoche <-> Coche
T_PASO = 0.5 # Segundos que dura un paso del modelo
DIST_SEG = 2 # celdas libres que necesita enfrente para avanzar

# Estádos lógicos del coche
AVANZANDO, DETENIDO, ESPERANDO_PASO, CEDIENDO, EN_CRUCE = (
    'AVANZANDO', 'DETENIDO', 'ESPERANDO_PASO', 'CEDIENDO', 'EN_CRUCE')

# Maniobras
RECTO, IZQ, DER = 'RECTO', 'IZQ', 'DER'