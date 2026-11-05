<script setup>
import { computed } from "vue"
import { useI18n } from "vue-i18n"

const { locale } = useI18n({ useScope: "global" })
const textos = {
  es: {
    titulo: "Política de privacidad",
    fecha: "Actualización: 4 de noviembre de 2026",
    introduccion: "Esta política describe cómo el Museo Histórico Cultural Juan Santamaría trata la información en SIAM y los derechos previstos en la Ley N.° 8968 de Costa Rica, Protección de la Persona frente al Tratamiento de sus Datos Personales.",
    secciones: [
      {
        titulo: "Responsable y contacto",
        parrafos: [
          "El Museo Histórico Cultural Juan Santamaría, en Alajuela, Costa Rica, es la institución responsable del tratamiento de la información en SIAM. Su administración atiende las consultas relacionadas con la privacidad y el uso de los datos.",
          "Correo de referencia: privacidad@siam.example.",
        ],
      },
      {
        titulo: "Registro de visitantes del museo",
        parrafos: [
          "Para elaborar estadísticas de afluencia, el registro de ingreso guarda el grupo de edad (mayor o menor), la categoría de nacionalidad (nacional o extranjera), el sexo registrado y la fecha y hora del ingreso. También identifica al funcionario que realizó el registro, no al visitante.",
          "El registro no solicita nombre, cédula, correo, teléfono ni dirección del visitante. Los reportes presentan cantidades agrupadas para planificar actividades y evaluar la asistencia. Se trabaja sin identificadores directos del visitante; la combinación de categorías y hora de ingreso no permite prometer una anonimización irreversible en todos los contextos.",
        ],
      },
      {
        titulo: "Navegación sin seguimiento publicitario",
        parrafos: [
          "SIAM no incorpora herramientas de analítica de navegación, rastreadores publicitarios, perfiles de comportamiento ni seguimiento entre sitios. Consultar las páginas públicas no exige crear una cuenta ni suministrar datos de identidad.",
          "El navegador conserva las preferencias de idioma y tema en almacenamiento local. La autenticación del personal utiliza cookies de sesión y protección CSRF. Estas funciones técnicas no se usan para publicidad. El proveedor de alojamiento podría conservar registros técnicos de conexión, distintos del seguimiento publicitario.",
        ],
      },
      {
        titulo: "Cuentas internas y acceso a la información",
        parrafos: [
          "SIAM también trata nombres, correos, roles, contraseñas protegidas y registros de actividad del personal para gestionar el acceso y la trazabilidad. Por ello, no toda la información del sistema es anónima ni corresponde a visitantes.",
          "La aplicación restringe los registros y reportes internos mediante sesiones y permisos por rol. No incorpora funciones para vender datos personales ni compartirlos con redes publicitarias. Toda cesión de datos personales debe contar con la autorización o habilitación legal correspondiente y respetar la confidencialidad.",
        ],
      },
      {
        titulo: "Conservación y consentimiento",
        parrafos: [
          "La conservación de los datos debe limitarse al tiempo necesario para su finalidad y las obligaciones legales aplicables. La administración del museo debe revisar su pertinencia y determinar su eliminación o desasociación cuando corresponda.",
          "Cuando se recojan datos personales, se debe informar previamente la finalidad, los destinatarios, si responder es obligatorio o voluntario y las consecuencias de no hacerlo. Cuando corresponda, se debe obtener consentimiento expreso y documentado. Navegar por el sitio o leer esta política no equivale a consentir otros tratamientos.",
        ],
      },
      {
        titulo: "Sus derechos",
        parrafos: [
          "Puede solicitar confirmación y acceso a sus datos personales, conocer su origen, finalidad, uso y destinatarios, y pedir su rectificación, actualización o supresión cuando corresponda. Puede exigir confidencialidad y decidir sobre la cesión de sus datos.",
          "Si el tratamiento se basa en su consentimiento, puede revocarlo sin efectos retroactivos. El ejercicio de derechos es gratuito; el artículo 7 establece un plazo de cinco días hábiles desde la recepción de la solicitud para resolver lo que corresponda.",
          "Para ejercer estos derechos, dirija su solicitud a la administración del museo e indique el derecho que desea ejercer y los datos necesarios para localizar su registro. El responsable deberá verificar su identidad de forma proporcional. Si un registro estadístico no permite identificarle, no se le atribuirá una entrada mediante suposiciones.",
        ],
      },
    ],
    recursos: "Normativa y protección de derechos",
    ley: "Consultar la Ley N.° 8968",
    prodhab: "Trámites y denuncias ante PRODHAB",
    reclamos: "Si considera vulnerados sus derechos, puede acudir a la Agencia de Protección de Datos de los Habitantes (PRODHAB). Las modificaciones de esta política se publicarán en esta página con su fecha de actualización.",
  },
  en: {
    titulo: "Privacy policy",
    fecha: "Updated: November 4, 2026",
    introduccion: "This policy describes how the Museo Histórico Cultural Juan Santamaría handles information in SIAM and the rights established by Costa Rica's Law No. 8968 on the protection of individuals regarding the processing of personal data.",
    secciones: [
      {
        titulo: "Controller and contact",
        parrafos: [
          "The Museo Histórico Cultural Juan Santamaría, in Alajuela, Costa Rica, is the institution responsible for processing information in SIAM. Its administration handles questions about privacy and the use of data.",
          "Reference email: privacidad@siam.example.",
        ],
      },
      {
        titulo: "Museum visitor records",
        parrafos: [
          "To compile attendance statistics, entry records store age group (adult or minor), nationality category (national or foreign), recorded sex, and the date and time of entry. They also identify the staff member who entered the record, not the visitor.",
          "The register does not request visitors' names, identity numbers, emails, phone numbers or addresses. Reports present grouped counts to plan activities and evaluate attendance. Records have no direct visitor identifiers; the combination of categories and entry time means irreversible anonymization cannot be guaranteed in every context.",
        ],
      },
      {
        titulo: "Browsing without advertising tracking",
        parrafos: [
          "SIAM does not include browsing analytics, advertising trackers, behavioral profiles or cross-site tracking. Reading public pages does not require an account or identity details.",
          "Your browser saves language and theme preferences in local storage. Staff authentication uses session cookies and CSRF protection. These technical features are not used for advertising. The hosting provider may retain technical connection logs, which are separate from advertising tracking.",
        ],
      },
      {
        titulo: "Internal accounts and information access",
        parrafos: [
          "SIAM also processes staff names, emails, roles, protected passwords and activity records for access management and accountability. Therefore, not all system information is anonymous or relates to visitors.",
          "The application restricts internal records and reports through sessions and role permissions. It has no features for selling personal data or sharing it with advertising networks. Any transfer of personal data must have the required authorization or legal basis and respect confidentiality.",
        ],
      },
      {
        titulo: "Retention and consent",
        parrafos: [
          "Data retention must be limited to the time necessary for its purpose and applicable legal obligations. Museum management must review whether records remain necessary and determine their deletion or disassociation where appropriate.",
          "When collecting personal data, the controller must first explain the purpose, recipients, whether answers are mandatory or optional, and the consequences of declining. Express, documented consent must be obtained where required. Browsing the website or reading this policy does not constitute consent to other processing.",
        ],
      },
      {
        titulo: "Your rights",
        parrafos: [
          "You may request confirmation and access to your personal data, learn its source, purpose, use and recipients, and request correction, updates or deletion where applicable. You may require confidentiality and decide whether to authorize transfers of your data.",
          "When processing relies on your consent, you may withdraw it without retroactive effect. Exercising these rights is free; article 7 provides five working days from receipt of a request to resolve it as appropriate.",
          "To exercise these rights, submit your request to museum administration, stating the right you wish to exercise and the information needed to locate your record. The controller must verify your identity proportionately. If a statistical record cannot identify you, an entry will not be attributed to you through guesswork.",
        ],
      },
    ],
    recursos: "Law and protection of rights",
    ley: "Read Law No. 8968 (Spanish)",
    prodhab: "PRODHAB procedures and complaints (Spanish)",
    reclamos: "If you believe your rights have been infringed, you may contact Costa Rica's Data Protection Agency (PRODHAB). Changes to this policy will be published on this page with an updated date.",
  },
}
const texto = computed(() => textos[locale.value] ?? textos.es)
</script>

<template>
  <article class="politica-privacidad" aria-labelledby="titulo-privacidad">
    <h1 id="titulo-privacidad">{{ texto.titulo }}</h1>
    <p>{{ texto.fecha }}</p>
    <p>{{ texto.introduccion }}</p>

    <section v-for="seccion in texto.secciones" :key="seccion.titulo">
      <h2>{{ seccion.titulo }}</h2>
      <p v-for="parrafo in seccion.parrafos" :key="parrafo">{{ parrafo }}</p>
    </section>

    <section>
      <h2>{{ texto.recursos }}</h2>
      <p>{{ texto.reclamos }}</p>
      <ul>
        <li><a href="https://formatos.inamu.go.cr/SIDOC/DOCS/ley_8968.pdf">{{ texto.ley }}</a></li>
        <li><a href="https://www.prodhab.go.cr/tramites%20y%20servicios/index.aspx">{{ texto.prodhab }}</a></li>
      </ul>
    </section>
  </article>
</template>

<style scoped>
.politica-privacidad {
  max-width: 72ch;
  margin-inline: auto;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

h1 { line-height: 1.2; }
h2 { margin-top: 2rem; line-height: 1.3; }
a { color: var(--color-enlace); }
li + li { margin-top: 0.75rem; }
</style>
