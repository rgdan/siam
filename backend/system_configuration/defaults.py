from copy import deepcopy

DEFAULTS = {
    "museum_name": "Museo Histórico Cultural Juan Santamaría",
    "address": "Frente al costado norte del Parque Central, Alajuela, Costa Rica.",
    "location": "Alajuela, Costa Rica",
    "opening_hours": {
        str(day): {
            "opens": None if day == 1 else "09:00",
            "closes": None if day == 1 else "17:00",
        }
        for day in range(7)
    },
    "default_language": "es",
}


def default_for(key):
    return deepcopy(DEFAULTS[key])
