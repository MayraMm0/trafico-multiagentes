T_VERDE, T_AMARILLO = 6.0, 1.5

class ControlSemaforos:
    def __init__(self, semaforos):
        # TODO: agrupar por cruce: {cruce: [s1, s2]}
        #       en cada cruce: el PRIMER semáforo es grupo A, el SEGUNDO grupo B
        # TODO: por cruce guardar: fase ('A' o 'B'), color del grupo activo, tiempo acumulado
        # TODO: desfasar cada cruce (ej. tiempo inicial = id_cruce * 1.3) para que no cambien
        #       todos al mismo tiempo
        # TODO: aplicar estado inicial: activo VERDE, el otro ROJO

    def update(self, dt):
        # TODO: por cada cruce sumar dt
        #       si activo VERDE y pasó T_VERDE      → activo AMARILLO, reiniciar tiempo
        #       si activo AMARILLO y pasó T_AMARILLO → activo ROJO, el otro VERDE, cambiar fase
        # TODO: llamar set_estado en los semáforos según la fase