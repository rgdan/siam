
/*
 * SIAM-8: Información pública del museo.
 * Datos provisionales mientras se desarrolla SIAM-32.
 * Cuando Jorge tenga lista la API, estos datos
 * serán reemplazados por la configuración del sistema.
 */

export const museoProvisional = {
  nombre: "Museo Histórico Cultural Juan Santamaría",

  historia: {
    es: "El Museo Histórico Cultural Juan Santamaría abrió sus puertas el 9 de abril de 1980. Está dedicado a preservar y divulgar la historia de la Campaña Nacional de 1856-1857 y el patrimonio cultural de Alajuela.",
    en: "The Juan Santamaría Historical Cultural Museum opened on April 9, 1980. It is dedicated to preserving and sharing the history of the National Campaign of 1856–1857 and Alajuela's cultural heritage.",
  },

  ubicacion: {
    es: "Frente al costado norte del Parque Central, Alajuela, Costa Rica.",
    en: "Across from the north side of Central Park, Alajuela, Costa Rica.",
  },

  entradaGratuita: true,

  // 0 = domingo, 1 = lunes, ... 6 = sábado.
  horarios: [
    { dia: 1, apertura: null, cierre: null },
    { dia: 2, apertura: "09:00", cierre: "17:00" },
    { dia: 3, apertura: "09:00", cierre: "17:00" },
    { dia: 4, apertura: "09:00", cierre: "17:00" },
    { dia: 5, apertura: "09:00", cierre: "17:00" },
    { dia: 6, apertura: "09:00", cierre: "17:00" },
    { dia: 0, apertura: "09:00", cierre: "17:00" },
  ],
}
