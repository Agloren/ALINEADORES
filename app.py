import os
import re
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuración general de la página
st.set_page_config(
    page_title="Asistente Clínico Angel Aligner - iOrtho",
    page_icon="🦷",
    layout="wide"
)

# 2. Configurar la API de Google Gemini desde Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Función para mostrar automáticamente las láminas/fotos de referencia mencionadas por la IA
CARPETA_FOTOS = "fotos_angel"

def mostrar_fotos_referencia(texto_respuesta):
    if not os.path.isdir(CARPETA_FOTOS):
        return
    patron = r"(?:0[1-9]|1[0-4])_[A-Za-z0-9_]+\.(?:jpg|png|jpeg)"
    encontradas = list(dict.fromkeys(re.findall(patron, texto_respuesta)))
    if encontradas:
        cols = st.columns(min(len(encontradas), 2))
        for idx, nombre_foto in enumerate(encontradas):
            ruta = os.path.join(CARPETA_FOTOS, nombre_foto)
            if os.path.isfile(ruta):
                with cols[idx % 2]:
                    st.image(ruta, caption=f"📌 Referencia: {nombre_foto}", use_container_width=True)

# 4. Barra lateral: Visor de Documentos Gráficos y Controles
st.sidebar.title("🦷 Biblioteca Gráfica Angel")
if os.path.isdir(CARPETA_FOTOS):
    archivos_graficos = sorted([
        f for f in os.listdir(CARPETA_FOTOS)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])
    if archivos_graficos:
        foto_sel = st.sidebar.selectbox(
            "Consultar lámina clínica / tabla:",
            ["Selecciona una lámina..."] + archivos_graficos
        )
        if foto_sel != "Selecciona una lámina...":
            st.sidebar.image(
                os.path.join(CARPETA_FOTOS, foto_sel),
                caption=foto_sel,
                use_container_width=True
            )
else:
    st.sidebar.info(
        "💡 Crea una carpeta llamada `fotos_angel` en tu repositorio de GitHub "
        "y sube ahí las láminas de los PDFs y capturas de iOrtho para activar el visor gráfico."
    )

if st.sidebar.button("🗑️ Limpiar memoria de consultas"):
    st.session_state.chat_angel = []
    st.session_state.ultima_prescripcion = ""
    st.session_state.ultima_auditoria = ""
    st.rerun()

# 5. EL "LADRILLO" / FRAMEWORK BIOMECÁNICO COMPLETO DE ANGEL ALIGNER (ROMINA VIGNOLO Y DAVID GONZÁLEZ ZAMORA)
FRAMEWORK_ANGEL_ALIGNER = """
Actúa como un Ortodoncista Senior y Director Clínico experto en el sistema Angel Aligner (plataforma iOrtho), entrenado estrictamente con los protocolos clínicos y biomecánicos de los Dres. David González Zamora y Romina Vignolo Lobato (Angel Academy).

REGLA SOBRE DOCUMENTOS GRÁFICOS Y FOTOS DE REFERENCIA:
Tienes a tu disposición este catálogo de láminas clínicas en la carpeta `fotos_angel/`. Siempre que expliques un protocolo, atache, línea de corte o tabla de iOrtho, incluye entre paréntesis el nombre exacto del archivo `.jpg` correspondiente para que la aplicación lo incruste automáticamente en pantalla:
- `01_iOrtho_Analisis_Bolton.jpg`: Ejemplo de tabla de Análisis de Bolton (3-3 y 6-6) y anchuras mesiodistales en iOrtho.
- `02_iOrtho_Staging_MovE.jpg`: Ejemplo de gráfico de secuenciación MovE (etapas, puntos rojos de ataches y rombos azules de IPR).
- `03_iOrtho_Tabla_TM_Inferior.jpg`: Ejemplo de Tabla de Movimientos (Tabla TM) arcada inferior con alertas amarillas.
- `04_iOrtho_Tabla_TM_Superior.jpg`: Ejemplo de Tabla de Movimientos (Tabla TM) arcada superior con alertas amarillas.
- `05_iOrtho_Anchura_Arcada.jpg`: Ejemplo de tabla de Anchura de la Arcada (3-3, 4-4, 5-5, 6-6).
- `06_iOrtho_OB_OJ_Sobremordida.jpg`: Ejemplo de tabla OB/OJ (mm) de sobremordida vertical y resalte horizontal.
- `07_Gama_Angel_Select_Pro_Kid_A6.jpg`: Comparativa de sistemas Angel Aligner Select, Pro, KiD y A6 Mandibular Solution.
- `08_Material_MasterControl_MasterForce.jpg`: Biomecánica del sistema dual Angel Aligner Pro (7 días masterControl S flexible 1.31N + 3 días masterForce rígido 2.86N).
- `09_Linea_Corte_Variable.jpg`: Tipos de línea de corte (Festoneada, Recta a 0.5 mm, Recta Alta a 2.5 mm y Mixta).
- `10_Catalogo_Ataches_Y_DGZ.jpg`: Catálogo de ataches Angel Aligner y diseño del Atache DGZ (DGZ Attachment: M en gingival + S en incisal).
- `11_Herramientas_AngelButton_Tongueoko_Levantes.jpg`: Herramientas exclusivas iOrtho (AngelButton, Tongueoko, Levantes de mordida curvos/rectangulares/inclinados y Barras de refuerzo).
- `12_Secuenciacion_Distalizacion_V_Pattern_Ninos.jpg`: Protocolos de secuenciación de distalización en V (adultos) vs. distalización simultánea y centrífuga en niños.
- `13_Protocolo_Clase_II_A6_Bloques_Tipo_I.jpg`: Tratamiento de Clase II con Bloques de Avance Mandibular A6 Tipo I (nunca Tipo II) y elásticos de posicionamiento.
- `14_Protocolo_Expansion_Simetrica_Y_Asimetrica.jpg`: Protocolos de expansión transversal simétrica vs. mordida cruzada unilateral (expandir primero lado comprimido).

====================================================================
1. SELECCIÓN DE PRODUCTO Y MATERIALES (ANGEL ALIGNER)
====================================================================
- ANGEL ALIGNER SELECT: Material monocapa `masterControl`. Opciones de 20 etapas (1 ref.), 30 etapas (1 ref.) o 30+ ilimitado (3 años).
- ANGEL ALIGNER PRO (`07_Gama_Angel_Select_Pro_Kid_A6.jpg`, `08_Material_MasterControl_MasterForce.jpg`):
  * Combina DOS materiales por cada etapa de tratamiento:
    1) Etapa impar / 1ª semana (7 días): `masterControl S` (multicapa flexible, fuerza suave de ~1.31 N, alta elasticidad y fácil inserción).
    2) Etapa par / últimos 3 días (3 días): `masterForce` (material rígido de ~2.86 N para expresar al 100% el movimiento programado, especialmente expansión, torque radicular, rotaciones y control de tip en extracciones).
- ANGEL ALIGNER KiD (K1 hasta 2 años / K2 hasta 4 años con fase 1 y fase 2) y A6 MANDIBULAR SOLUTION: Diseñados para pacientes en crecimiento, dentición temporal/mixta, compensación de erupción y avance mandibular.
- RITMO DE CITAS EN CLÍNICA: Revisiones cada 2 meses entregando ~6 alineadores por tanda; programar el IPR y cementado de elementos para que coincidan con las citas de control (por ejemplo, en etapa 1, 7, 13, 19...).

====================================================================
2. LÍNEA DE CORTE VARIABLE (TRIMMING LINE) (`09_Linea_Corte_Variable.jpg`)
====================================================================
- FESTONEADA (0 mm): Mayor estética o pacientes periodontales con recesiones gingivales. Menor fuerza biomecánica.
- RECTA ESTÁNDAR (0.5 mm): Equilibrio entre retención y confort.
- RECTA ALTA (2.5 mm): Cubre 2.5 mm por encima del margen gingival. Aumenta drásticamente la superficie de plástico, la retención y el brazo de palanca para EXPANSIÓN, DISTALIZACIÓN, uso de MÁSCARA FACIAL y AVANCE MANDIBULAR A6.
  * Precaución clínica: Si se pide línea de corte alta, hay que REDUCIR o suavizar la retención de los ataches (si se dejan los mismos ataches retentivos que con línea festoneada, el paciente no podrá sacarse el alineador). En adultos no mantenerla más de 20 alineadores seguidos si molesta en la mucosa lingual inferior (torus).
- MIXTA (Recta Alta 2.5 mm en posterior + Festoneada en anterior):
  * Imprescindible en NIÑOS en recambio del sector anterior (la encía anterior cambia de volumen al erupcionar los incisivos y rozaría con corte alto, mientras atrás aprovechamos toda la fuerza expansiva del corte alto).
  * Muy útil en ADULTOS durante la primera fase de expansión cuando no se requiere un control crítico de torque incisivo.

====================================================================
3. BIOMECÁNICA DE ATACHES Y REGLAS DEL "DGZ ATTACHMENT" (`10_Catalogo_Ataches_Y_DGZ.jpg`)
====================================================================
- REGLA DE ORO EN MOVIMIENTOS DIFÍCILES: Todo diente con movimiento complejo (o adyacente a un AngelButton) necesita atache para garantizar que el alineador no pierda anclaje ni desajuste. En niños pequeños con coronas clínicas cortas (caninos temporales y primeros molares temporales), colocar ATACHES GRANDES ("ladrillos") porque muerden el alineador al insertarlo y sin atache el diente temporal no se mueve ni expande.
- EXTRUSIÓN vs. TORQUE EN INCISIVOS (Atache HBO / Biselado Horizontal):
  * Colocado en el BORDE INCISAL (con bisel activo hacia gingival) = EXTRUSIÓN.
  * Colocado en el CENTRO DEL DIENTE = TORQUE.
  * Truco para extruir los 4 incisivos superiores: colocar atache biselado en los 4 incisivos y pedir al técnico dejar **0.1 mm de espacio interproximal** entre los 4 incisivos para eliminar la fricción interdentaria durante la extrusión.
  * En incisivos inferiores estrechos mesiodistalmente, el atache convencional rectangular biselado funciona muy bien para extrusión o intrusión si el paciente colabora.
- ATACHE DGZ ("DGZ Attachment" - Dr. David González Zamora & Dra. Romina Vignolo):
  * Siempre preferible frente al atache clásico de doble tip / doble biselado cuando necesitamos control radicular mesiodistal (tip radicular en caninos tras extracciones, cierre de diastemas, enderezamiento radicular de incisivos laterales o premolares).
  * Por qué falla el doble atache clásico: el atache más cercano a incisal desajusta el alineador en una zona donde el plástico es más rígido y estrecho, generando una fuerza intrusiva parásita que hunde el diente (hasta 0.99 mm de pérdida de altura vertical).
  * Diseño exacto del Atache DGZ: Dos cilindros semicónicos horizontales unidos por una barra vertical (3 mm de altura total, 1 mm de espesor). La clave biomecánica es que tiene **TALLA M (Mediana) en GINGIVAL y TALLA S (Pequeña) en INCISAL**. Al ser más pequeño en incisal, el alineador encaja perfectamente sin perder tracking, logra el 100% del tip radicular programado y reduce a la mitad el efecto secundario vertical.
  * Cómo pedirlo al técnico en iOrtho: Solicitar "Atache de doble retención tipo DGZ (tamaño M en gingival y S en incisal)" orientado según la dirección del movimiento radicular.
- ATACHES DE ROTACIÓN Y RETENCIÓN:
  * Los dientes cilíndricos (caninos y premolares) con rotaciones >15° requieren obligatoriamente atache de rotación (o el nuevo atache combinado de rotación + retención) y espacio mesiodistal libre (abrir espacio antes o hacer IPR suave).
- INTRUSIÓN ANTERIOR Y CONTROL DE SOBRECORRECCIÓN VERTICAL:
  * Para intruir incisivos sin que se proinclinen: pedir **lingualizar coronas aplicando torque radicular palatino** (evita que los incisivos se vestibularicen al intruir) y colocar **ataches de retención en premolares** como anclaje para que el alineador no se levante de atrás.
  * Evitar intruir caninos e incisivos exactamente en los mismos pasos si supera el anclaje disponible: secuenciar o apoyar con levantes de mordida.

====================================================================
4. HERRAMIENTAS EXCLUSIVAS DE iORTHO (`11_Herramientas_AngelButton_Tongueoko_Levantes.jpg`)
====================================================================
- ANGELBUTTON™ (Botón integrado en el alineador):
  * Fabricado en el mismo TPU rígido del Pro; soporta hasta **500 g de tracción elástica**.
  * DIFERENCIA BIOMECÁNICA CLAVE frente al Recorte para Botón (Cutout):
    1) Con **AngelButton**, la fuerza del elástico se transmite al plástico y se reparte en bloque por toda la arcada (ideal para corregir Clase II, Clase III o líneas medias en masa sin extruir ni volcar el diente individual).
    2) Con **Recorte en ventana para botón cementado al diente**, la fuerza va directa al diente (ideal cuando SÍ buscamos extruir ese molar o canino, o desrotarlo con cupla).
    3) Se pueden combinar ambos: por ejemplo, en un paciente braquifacial con Clase II, poner **AngelButton en canino superior** (frena y distaliza toda la arcada superior en bloque) y **Recorte para botón cementado en el molar inferior** (para que el elástico extruya el molar inferior y abra el plano oclusal).
  * REGLA OBLIGATORIA EN MORDIDAS CRUZADAS CON ANGELBUTTON: Si colocas un AngelButton en vestibular superior o lingual inferior para elásticos cruzados, **SIEMPRE hay que colocar un atache en la cara opuesta (palatino/vestibular) para retención**, evitando que el tiro del elástico desinserte el alineador.
- LEVANTES DE MORDIDA (BITE TURBOS):
  * **Anteriores (en palatino de incisivos superiores):** Imprescindibles desde el Día 1 en pacientes **braquifaciales con sobremordida aumentada**, en Clase II/III y en mordidas cruzadas (al desocluir los sectores posteriores eliminan las interferencias cuspídeas y dejan vía libre para expandir rápido).
    - *Diseño Curvo (Adaptativo):* Cambia su angulación etapa a etapa según se corrige el torque incisivo. **NUNCA se rellena de composite**.
    - *Diseño Rectangular/Cuadrado:* No adaptativo, pensado solo si el doctor desea cementarlo con composite.
    - *Levante Anterior Inclinado (exclusivo Angel):* Rampa inclinada palatina para mantener el avance mandibular en Clase II tras retirar los bloques A6 o en casos de salto mandibular leve.
  * **Posteriores (en caras oclusales de molares):** Para pacientes **dolicofaciales**, mordidas abiertas anteriores o mordidas cruzadas anteriores. **No se rellenan de composite**. Vigilar no mantenerlos más tiempo del necesario (especialmente con material Pro rígido) para no intruir en exceso los molares y generar mordida abierta posterior.
- TONGUEOKO™ (Topes / Recordatorios Linguales):
  * Aletas integradas en el plástico para reeducar la lengua en mordida abierta anterior o empuje lingual lateral. Pueden pedirse con apertura hacia mesial o hacia distal. **Nunca se rellenan de composite**.
- BARRAS DE REFUERZO (REINFORCEMENT BARS):
  * El software las añade por defecto cuando la brecha edéntula o distancia interarcada supera los **8 mm**, pero deben solicitarse al técnico siempre que hagamos expansiones amplias o distalizaciones largas para evitar que el plástico sufra deformación parabólica.

====================================================================
5. PROTOCOLOS DE PLANIFICACIÓN POR MALOCLUSIÓN
====================================================================
A) PROBLEMAS TRANSVERSALES Y MORDIDAS CRUZADAS (`14_Protocolo_Expansion_Simetrica_Y_Asimetrica.jpg`):
- Diagnóstico diferencial funcional y postural (Leyes de Planas):
  * En condiciones normales sin mordida cruzada, el maxilar se expande hacia el lado de trabajo. En cambio, en una **mordida cruzada**, la 1ª Ley de Planas se invierte: el maxilar superior queda atrapado por dentro y se comprime en el lado cruzado, mientras la mandíbula se desvía hacia ese lado (que suele coincidir con el lado preferente de dormir del paciente, donde la musculatura es más corta).
  * Rehabilitar siempre la **volumetría torsional de la lengua** (en el lado de trabajo es ancha y baja; en el lado de balanceo es estrecha y alargada) y cambiar hábitos posturales al dormir (no dormir boca abajo ni metiendo la mano/hombro bajo la cara).
- EXPANSIÓN ASIMÉTRICA (Mordida Cruzada Unilateral):
  * **ERROR CLÁSICO A EVITAR:** Nunca sobreexpandir primero el lado sano para hacer anclaje recíproco, porque dejas al paciente sin oclusión en ambos lados durante meses y no puede masticar.
  * **PROTOCOLO CORRECTO (Zamora & Vignolo):**
    1) Fase 1: Pedir al técnico **expansión unilateral exclusiva del lado comprimido** hasta igualarlo en anchura y simetría con el lado sano (apoyando con ataches en palatino si se usan elásticos cruzados en AngelButton). Indicar al paciente que mastique por el lado contrario al que masticaba habitualmente.
    2) Fase 2: Una vez lograda la simetría entre ambas hemiarcadas, continuar con **expansión bilateral simétrica** hasta lograr una arcada cuadrada/redondeada que permita frote oclusal bilateral.
- TASAS Y LÍMITES DE EXPANSIÓN:
  * **En Niños (Dentición temporal / mixta):** Programar expansión a **0.25 mm por etapa**. Pedir **sobrecorrección** y **ataches grandes** en caninos temporales y primeros molares temporales (tienen poca corona clínica y el plástico resbala si no llevan atache potente). En casos con compresión + falta de espacio + retrognatia/Clase II dentaria, aplicar **"Expansión Centrífuga"** (expandir + distalar + protruir simultáneamente en los 3 planos del espacio). Dejar siempre **0.5 mm de espacio en mesial y distal de los caninos de leche** (espacio de primate).
  * **En Adultos:** Programar expansión lenta a **0.10 – 0.15 mm por etapa**. Si los molares iniciales ya están inclinados a vestibular, pedir **torque radicular vestibular y sobrecorrección con torque palatino de la corona** durante la expansión para lograr movimiento en masa y no volcamiento coronal (evitando recesiones y contactos prematuros en cúspides palatinas).

B) PROBLEMAS SAGITALES: CLASE II, DISTALIZACIÓN Y AVANCE MANDIBULAR A6 (`12_Secuenciacion_Distalizacion_V_Pattern_Ninos.jpg`, `13_Protocolo_Clase_II_A6_Bloques_Tipo_I.jpg`):
- DISTALIZACIÓN SECUENCIAL vs. SIMULTÁNEA:
  * **En Adultos:** Usar **Secuenciación en V (patrón 1/2)**: distalar el 2º molar (7); cuando lleva el 50% de su recorrido empieza a distalar el 1er molar (6); cuando el 7 llega a su sitio empieza el 5, de modo que **nunca haya más de 2 dientes distalando simultáneamente por cuadrante** (para no superar el anclaje anterior y evitar que los incisivos se proinclinen por acción-reacción). Si los molares están muy rotados a mesial, usar primero *Frog pattern* (desrotar y abrir ligero espacio entre 7 y 6 / 6 y 5 para que el plástico entre en interproximal) y luego distalar. Acompañar con elásticos de Clase II desde que inicia el movimiento del 6 o el 5.
  * **En Niños en Crecimiento:** Sí es predecible hacer **distalización simultánea** de molares combinada con expansión transversal.
    - Si un lado es Clase II y el otro es Clase I: en el lado de Clase I distalar arriba y abajo a la par para no perder la Clase I mientras se gana espacio; en el lado de Clase II distalar más la arcada superior.
- AVANCE MANDIBULAR CON BLOQUES A6 (Pacientes en Crecimiento con Clase II mandibular):
  * **REGLA CRÍTICA DE DISEÑO DEL BLOQUE:** Elegir **SIEMPRE BLOQUES TIPO I** (con escalón y superficie horizontal plana de apoyo oclusal). **PROHIBIDO ELEGIR BLOQUES TIPO II** (los inclinados sin plano horizontal), porque el plano inclinado concentra toda la fuerza masticatoria en los molares, los intruye y genera una mordida abierta posterior severa.
  * **Posición del bloque A6:** Escalonar siempre al técnico que **el bloque superior DEBE cubrir como mínimo el primer molar inferior definitivo (6)** para evitar que la mandíbula se descuelgue por detrás del bloque.
  * **Magnitud del salto mandibular:**
    - Salto mínimo: **4 mm** (altura/avance mínimo para desalojar el cóndilo de la cavidad glenoidea y estimular crecimiento real de la rama mandibular).
    - Salto máximo por fase: **7 mm**. Si el paciente tiene >7-8 mm de resalte, dividir el avance en **2 saltos** (ej. primer salto de 4-5 mm y segundo salto hasta Clase I; nunca hacer micro-saltitos de 1-2 mm porque no separan el cóndilo).
  * **Nivelación vertical y Salto Virtual:** Nivelar el plano oclusal superior y el plano oclusal inferior de forma independiente (intruyendo incisivos inferiores con levantes/plano plano, sin extruir molares artificialmente) y pedir un **salto virtual vertical** para que el técnico permita la anterorrotación natural de la mandíbula.
  * **Elástico de posicionamiento con A6 (Truco Dra. Romina Vignolo):** Poner siempre **AngelButton en caninos superiores (13 y 23)** y **recorte para botón en primeros molares inferiores (36 y 46)** para usar un **elástico muy suave (ej. 1/4" 2 oz)** por la noche (y por la tarde en el lado más corto si la Clase II es asimétrica). Esto guía muscularmente al niño para cerrar encajando los bloques A6 sin aplastarlos.
  * **Tiempo de consolidación:** Mantener el avance un mínimo de **9 meses** para pasar de adaptación muscular a remodelado esquelético. Si la fase de bloques dura 20 alineadores (~5 meses), en la segunda fase colocar **levantes anteriores inclinados** + elásticos nocturnos para completar los 9 meses de retención activa del salto.

C) PROBLEMAS SAGITALES: CLASE III:
- En pacientes en crecimiento: combinar **línea de corte alta (2.5 mm)** + expansión maxilar + **AngelButtons o recortes posteriores superiores** para tracción con máscara facial o elásticos de Clase III.
- En camuflaje dentoalveolar: aprovechar los **AngelButtons** (de canino inferior a molar superior) para repartir la fuerza de Clase III en toda la arcada inferior sin extruir ni lingualizar en exceso los incisivos inferiores, o distalizar secuencialmente en V la arcada inferior vigilando el límite óseo retromolar y el torque incisivo inferior.

====================================================================
6. AUDITORÍA DE LA TABLA DE MOVIMIENTOS (TABLA TM), BOLTON Y OB/OJ EN iORTHO
====================================================================
Cuando analices una captura o datos del primer Setup de iOrtho (`01_iOrtho_Analisis_Bolton.jpg` a `06_iOrtho_OB_OJ_Sobremordida.jpg`), audita sistemáticamente estos 6 puntos:
1) **Lectura de la Tabla TM (Corona / Centro de resistencia / Ápice radicular):**
   - **Extrusión / Intrusión (`E` / `I`):** Movimientos >1.0 - 1.5 mm requieren ataches específicos (HBO incisal para extrusión con 0.1 mm de espacio interproximal; ataches de retención en premolares + torque radicular palatino para intrusión). Vigilar intrusiones recíprocas falsas: si ves intrusión de un canino junto a extrusión de un lateral (>1.5 mm), exigir escalonar movimientos o colocar atache de retención potente en el diente de anclaje.
   - **Traslación V-L (`B` / `La` / `L`):** Alertas amarillas (>1.0 - 1.5 mm) en caninos o incisivos al cerrar espacios o expandir. Verificar en la pestaña `Ápice radicular` que el ápice no salga de la cortical alveolar.
   - **Traslación M-D (`M` / `D`):** Si hay distalización >2 mm en adultos, comprobar en el gráfico `MovE` que NO se muevan todos los dientes a la vez (exigir secuenciación en V 1/2).
   - **Rotación (`M` / `D` en grados):** Cualquier rotación **>15° en caninos o premolares** o **>20° en incisivos** (aunque iOrtho no la marque en amarillo, como rotaciones de 25° a 42°) es de ALTO RIESGO de pérdida de tracking. Exigir:
     a) Reducir la velocidad de rotación o dividir en fases.
     b) Colocar **atache de rotación + retención** (o biselado amplio).
     c) Abrir **0.1 - 0.2 mm de espacio M-D previo** antes de iniciar el giro (o reprogramar el IPR al inicio y no en la etapa 14-19).
   - **Angulación / Tip (`M` / `D` en grados):** Si supera 4-5° en caninos/incisivos o hay cierre de espacio de extracción/agenesia (ej. ausencia del 42), exigir el **Atache DGZ (M gingival + S incisal)** para mover la raíz sin inclinar la corona.
   - **Torque (`La` / `Li` / `B` en grados):** Alertas amarillas (>10°). Si al cerrar espacios inferiores o retruir incisivos el torque lingual se dispara (ej. >10-13° Li), el diente perderá torque y aumentará la sobremordida. Exigir **sobrecorrección de torque radicular lingual / coronal vestibular (+5° a +10°)** y levantes de mordida anteriores.
2) **Auditoría del Gráfico `MovE` (Secuenciación / Staging):**
   - Si ves todas las barras azules moviéndose simultáneamente desde la etapa 1 hasta la final en un caso complejo de adulto, alerta al doctor: pedir secuenciación lógica (primero expandir/abrir espacio y desrotar, o secuenciar en V) y **adelantar el IPR (rombos azules)** a las primeras etapas antes de desrotar o retruir.
3) **Auditoría del Análisis de Bolton (`Bolton`):**
   - Verificar siempre si una discrepancia grande de Bolton (ej. exceso superior de 9 mm en 3-3) se debe a una **ausencia o agenesia unilateral/bilateral** (ej. falta del 42) o a microdoncias de laterales superiores (12, 22). Definir si se abrirá espacio para implante/reconstrucción o si se cerrará espacio mesializando con Atache DGZ y ajustando el IPR superior.
4) **Auditoría de Anchura de Arcada (`Arcada`):**
   - Comprobar los cambios en `3-3`, `4-4`, `5-5` y `6-6`. **Alerta roja si el técnico comprime la distancia intercanina (`3-3`)** de forma excesiva (ej. -1.3 mm arriba o -4.3 mm abajo al cerrar una ausencia de incisivo) sin compensar el torque, ya que colapsará la arcada y atrapará la mandíbula.
5) **Auditoría de Sobremordida y Resalte (`OB/OJ`):**
   - Si el **Overbite (Sobremordida)** objetivo sube a ~3.0 mm o más al retruir incisivos, el paciente terminará en mordida profunda en boca real (efecto *bowing* de los alineadores). Exigir terminar el setup en **sobrecorrección vertical (OB objetivo de 0.5 a 1.0 mm)** con intrusión incisiva pura, curva de Spee inversa inferior y levantes de mordida anteriores.
   - Verificar que el **Overjet (Sobremordida horizontal)** final no quede demasiado ajustado (<1.5 mm) para evitar contacto prematuro anterior que provoque mordida abierta posterior.
"""

# 6. Inicializar modelo Gemini (compatible con texto e imágenes de iOrtho)
modelo = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    system_instruction=FRAMEWORK_ANGEL_ALIGNER
)

# 7. Cabecera de la Aplicación
st.title("🦷 Asistente Clínico de Ortodoncia — Angel Aligner (iOrtho)")
st.markdown(
    "Sistema inteligente de **Prescripción Inicial** y **Auditoría Biomecánica del Setup 3D** "
    "basado en los protocolos clínicos de los Dres. **David González Zamora y Romina Vignolo Lobato**."
)

# Memoria de sesión
if "chat_angel" not in st.session_state:
    st.session_state.chat_angel = []
if "ultima_prescripcion" not in st.session_state:
    st.session_state.ultima_prescripcion = ""
if "ultima_auditoria" not in st.session_state:
    st.session_state.ultima_auditoria = ""

# 8. Creación de las 3 Pestañas de Trabajo
tab_diag, tab_setup, tab_chat = st.tabs([
    "📋 Fase 1: Diagnóstico y Prescripción Inicial",
    "🔍 Fase 2: Auditoría del 1er Setup (Capturas iOrtho / Tabla TM)",
    "💬 Fase 3: Chat Clínico y Consultas del Ladrillo"
])

# ==============================================================================
# PESTAÑA 1: DIAGNÓSTICO Y PRESCRIPCIÓN INICIAL
# ==============================================================================
with tab_diag:
    st.subheader("📋 Formulario de Diagnóstico Clínico Inicial")
    st.caption("Rellena las características del paciente para generar la receta exacta de prescripción para el técnico CAD de Angel Aligner.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1. Paciente y Biotipo")
        tipo_paciente = st.selectbox(
            "Grupo de edad / Dentición",
            [
                "Adulto (Dentición permanente)",
                "Adolescente (Dentición permanente joven)",
                "Niño en Crecimiento - Dentición Mixta 1ª Fase",
                "Niño en Crecimiento - Dentición Mixta 2ª Fase",
                "Niño Pequeño - Dentición Temporal (<6 años)"
            ]
        )
        biotipo = st.selectbox(
            "Biotipo Facial",
            ["Mesofacial", "Braquifacial (Tendencia a sobremordida)", "Dolicofacial (Tendencia a mordida abierta)"]
        )
        colaboracion = st.selectbox(
            "Colaboración estimada / Higiene",
            ["Alta", "Media", "Baja /Riesgo de mal uso de elásticos", "Periodontal / Recesiones gingivales"]
        )
        habitos_atm = st.multiselect(
            "Hábitos, Postura y ATM",
            [
                "Sin alteraciones",
                "Respirador oral / Cornetes hipertróficos",
                "Deglución atípica / Empuje lingual anterior",
                "Lengua baja / asimétrica (torsión lingual)",
                "Duerme boca abajo / apoya mano-hombro en cara",
                "Masticación unilateral predominante",
                "Bruxismo / Apretamiento",
                "Clic / Disfunción ATM"
            ],
            default=["Sin alteraciones"]
        )

    with col2:
        st.markdown("#### 2. Plano Sagital y Líneas Medias")
        c_molar_d = st.selectbox("Clase Molar Derecha", ["Clase I", "Clase II incompleta (1/2 cúspide)", "Clase II completa", "Clase III incompleta", "Clase III completa"])
        c_molar_i = st.selectbox("Clase Molar Izquierda", ["Clase I", "Clase II incompleta (1/2 cúspide)", "Clase II completa", "Clase III incompleta", "Clase III completa"])
        c_canina_d = st.selectbox("Clase Canina Derecha", ["Clase I", "Clase II incompleta", "Clase II completa", "Clase III incompleta", "Clase III completa"])
        c_canina_i = st.selectbox("Clase Canina Izquierda", ["Clase I", "Clase II incompleta", "Clase II completa", "Clase III incompleta", "Clase III completa"])
        origen_sagital = st.selectbox(
            "Origen principal de la displasia sagital",
            ["Dentoalveolar", "Retrusión mandibular (susceptible de Avance A6 si crece)", "Protrusión maxilar", "Hipoplasia maxilar (Clase III)", "Mixto"]
        )
        resalte_oj = st.number_input("Resalte / Overjet inicial (mm)", min_value=-10.0, max_value=20.0, value=2.5, step=0.5)
        lm_sup = st.selectbox("Línea Media Superior respecto a Facial", ["Centrada", "Desviada a la Derecha (1-2 mm)", "Desviada a la Derecha (>2 mm)", "Desviada a la Izquierda (1-2 mm)", "Desviada a la Izquierda (>2 mm)"])
        lm_inf = st.selectbox("Línea Media Inferior respecto a Superior", ["Centrada", "Desviada a la Derecha (1-2 mm)", "Desviada a la Derecha (>2 mm)", "Desviada a la Izquierda (1-2 mm)", "Desviada a la Izquierda (>2 mm)"])

    with col3:
        st.markdown("#### 3. Plano Vertical, Transversal y Espacio")
        sobremordida_ob = st.number_input("Sobremordida / Overbite inicial (mm)", min_value=-10.0, max_value=12.0, value=2.5, step=0.5)
        problema_vertical = st.selectbox(
            "Situación Vertical y Curva de Spee",
            [
                "Normal (1.5 - 2.5 mm)",
                "Sobremordida aumentada / Mordida profunda por extrusión incisiva inferior (Curva de Spee marcada)",
                "Sobremordida aumentada por extrusión incisiva superior (Sonrisa gingival)",
                "Mordida borde a borde (0 mm)",
                "Mordida abierta anterior dentoalveolar (empuje lingual)",
                "Mordida abierta esquelética posterior/anterior"
            ]
        )
        problema_transversal = st.selectbox(
            "Situación Transversal",
            [
                "Arcadas simétricas y bien coordinadas",
                "Compresión bilateral simétrica (Necesita expansión simétrica)",
                "Mordida cruzada posterior UNILATERAL DERECHA (Lado derecho comprimido)",
                "Mordida cruzada posterior UNILATERAL IZQUIERDA (Lado izquierdo comprimido)",
                "Mordida cruzada posterior BILATERAL",
                "Mordida en tijera (Brodie)"
            ]
        )
        apinamiento_sup = st.selectbox("Espacio Arcada Superior", ["Sin apiñamiento", "Apiñamiento leve (1-3 mm)", "Apiñamiento moderado (4-6 mm)", "Apiñamiento severo (>6 mm)", "Diastemas / Espacios"])
        apinamiento_inf = st.selectbox("Espacio Arcada Inferior", ["Sin apiñamiento", "Apiñamiento leve (1-3 mm)", "Apiñamiento moderado (4-6 mm)", "Apiñamiento severo (>6 mm)", "Diastemas / Espacios"])
        incisivos_inclinacion = st.selectbox("Inclinación de Incisivos (Torque inicial)", ["Normoinclinados", "Proinclinados superior e inferior", "Retroinclinados (ej. Clase II div 2)", "Superior proinclinado / Inferior retroinclinado", "Superior retroinclinado / Inferior proinclinado (Compensación CIII)"])

    notas_clinicas_ini = st.text_area(
        "Notas adicionales del caso (ausencias dentarias, agenesias, caninos incluidos, terceros molares, objetivos estéticos):",
        placeholder="Ej: Ausencia del 42, caninos de leche presentes, el 23 está muy rotado a mesial..."
    )

    if st.button("🚀 Generar Estrategia y Prescripción Inicial para Angel Aligner", type="primary"):
        prompt_fase1 = f"""
Genera la PLANIFICACIÓN BIOMECÁNICA Y PRESCRIPCIÓN INICIAL COMPLETA para enviar este caso a Angel Aligner (iOrtho), aplicando estrictamente los protocolos de los Dres. David González Zamora y Romina Vignolo:

DATOS DIAGNÓSTICOS DEL PACIENTE:
- Edad / Dentición: {tipo_paciente}
- Biotipo facial: {biotipo} | Colaboración/Periodonto: {colaboracion}
- Hábitos, Postura y ATM: {', '.join(habitos_atm)}
- Clase Molar: Derecha = {c_molar_d} | Izquierda = {c_molar_i}
- Clase Canina: Derecha = {c_canina_d} | Izquierda = {c_canina_i}
- Origen sagital: {origen_sagital} | Resalte (Overjet) inicial: {resalte_oj} mm
- Línea Media Superior: {lm_sup} | Línea Media Inferior: {lm_inf}
- Sobremordida (Overbite) inicial: {sobremordida_ob} mm ({problema_vertical})
- Situación Transversal: {problema_transversal}
- Espacio Superior: {apinamiento_sup} | Espacio Inferior: {apinamiento_inf}
- Inclinación incisiva inicial: {incisivos_inclinacion}
- Notas clínicas adicionales: {notas_clinicas_ini if notas_clinicas_ini else 'Ninguna'}

Estructura tu respuesta en estos 6 bloques claros:
1. **Producto Angel Aligner y Línea de Corte recomendada:** (Elige entre Select, Pro 7+3 días, KiD o A6, y especifica la Línea de Corte: Festoneada, Recta 0.5 mm, Alta 2.5 mm o Mixta explicando el porqué).
2. **Estrategia Transversal:** (Simétrica vs. Unilateral del lado comprimido primero, tasa en mm por etapa según edad, control de torque molar y espacio de primate si aplica).
3. **Estrategia Sagital y Secuenciación (Staging):** (Distalización en V 1/2 vs simultánea, Bloques A6 Tipo I con salto mínimo de 4 mm y cobertura del 6 inferior si aplica, IPR o protrusión).
4. **Estrategia Vertical y Control de Torque:** (Levantes de mordida anteriores curvos/inclinados o posteriores, salto virtual vertical, Tongueoko si hay hábito lingual, sobrecorrección de OB).
5. **Diseño de Ataches, AngelButtons y Elásticos:** (Dónde pedir Ataches DGZ M-gingival/S-incisal, HBO de extrusión vs torque, ataches en palatino si hay AngelButton cruzado, y pauta exacta de elásticos).
6. **📝 TEXTO EXACTO LISTO PARA COPIAR Y PEGAR EN LAS INSTRUCCIONES AL TÉCNICO CAD DE iORTHO:** (Redactado en puntos claros y directos para enviar en la plataforma).
Recuerda citar entre paréntesis los nombres exactos de los archivos `.jpg` de referencia del catálogo para mostrar los esquemas gráficos.
"""
        with st.spinner("Analizando diagnóstico y redactando prescripción para iOrtho..."):
            try:
                respuesta_ini = modelo.generate_content(prompt_fase1)
                st.session_state.ultima_prescripcion = respuesta_ini.text
            except Exception as e:
                st.error(f"Detalle del error de conexión con Google Gemini: {e}")

    if st.session_state.ultima_prescripcion:
        st.markdown("---")
        st.markdown("### ✅ Prescripción Inicial y Plan Biomecánico")
        st.markdown(st.session_state.ultima_prescripcion)
        mostrar_fotos_referencia(st.session_state.ultima_prescripcion)

# ==============================================================================
# PESTAÑA 2: AUDITORÍA DEL 1er SETUP (CAPTURAS iORTHO / TABLA TM / BOLTON / OB-OJ)
# ==============================================================================
with tab_setup:
    st.subheader("🔍 Auditoría Inteligente de la 1ª Propuesta de iOrtho (Setup 3D)")
    st.markdown(
        "Sube directamente las **fotos o capturas de pantalla de tu monitor en iOrtho** "
        "(**Tabla TM** superior e inferior, **Análisis de Bolton**, **Anchura de la arcada**, **OB/OJ** y gráfico **MovE**). "
        "Gemini leerá todas las cifras y alertas amarillas/rojas automáticamente."
    )

    capturas_iortho = st.file_uploader(
        "📸 Arrastra aquí tus capturas o fotos de la pantalla de iOrtho (puedes subir varias a la vez):",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

    if capturas_iortho:
        cols_img = st.columns(min(len(capturas_iortho), 3))
        imagenes_pil = []
        for i, archivo in enumerate(capturas_iortho):
            img_pil = Image.open(archivo)
            imagenes_pil.append(img_pil)
            with cols_img[i % 3]:
                st.image(img_pil, caption=archivo.name, use_container_width=True)

    observaciones_setup = st.text_area(
        "Observaciones adicionales o dudas sobre este Setup (opcional, o pega valores si no subes fotos):",
        placeholder="Ej: Es el primer setup que me manda el técnico. Veo que falta el 42 y han cerrado el espacio comprimiendo el 3-3 inferior..."
    )

    incluir_diag_previo = st.checkbox(
        "Cruzar esta auditoría con los datos que he seleccionado en la Pestaña 1 (Diagnóstico Inicial)",
        value=True
    )

    if st.button("🔬 Auditar Setup de iOrtho y Generar Modificaciones para el CAD", type="primary"):
        contexto_diag = ""
        if incluir_diag_previo:
            contexto_diag = f"""
CONTEXTO DIAGNÓSTICO DEL PACIENTE (PESTAÑA 1):
- Edad/Dentición: {tipo_paciente} | Biotipo: {biotipo}
- Clase Molar D: {c_molar_d} | I: {c_molar_i} | Clase Canina D: {c_canina_d} | I: {c_canina_i}
- Resalte inicial: {resalte_oj} mm | Sobremordida inicial: {sobremordida_ob} mm ({problema_vertical})
- Transversal: {problema_transversal} | Notas: {notas_clinicas_ini}
"""
        prompt_fase2 = f"""
Actúa como auditor clínico experto en Angel Aligner (iOrtho). Analiza minuciosamente las capturas de pantalla adjuntas del software iOrtho (Tabla TM de movimientos dentales, Análisis de Bolton, Anchura de la arcada, OB/OJ y gráfico de secuenciación MovE) junto con las observaciones del doctor.

{contexto_diag}
OBSERVACIONES DEL DOCTOR:
{observaciones_setup if observaciones_setup else 'Analizar todas las tablas de las imágenes adjuntas.'}

Realiza una AUDITORÍA CLÍNICA COMPLETA dividida en estas 6 secciones:
1. **Lectura de Datos Clave Detectados en las Capturas:**
   - Resume qué has leído en el **Bolton** (identificando ausencias/agenesias o discrepancias en 3-3 y 6-6), en **OB/OJ** (Inicial vs Objetivo), en **Anchura de Arcada** (3-3, 4-4, 5-5, 6-6) y el número de etapas / secuencia en **MovE**.
2. **Alerta de Movimientos Críticos en la Tabla TM (Diente por Diente):**
   - Señala todos los dientes con **alertas amarillas/rojas** Y también los que están en blanco pero superan límites biomecánicos predecibles:
     * **Rotaciones >15° en caninos/premolares o >20° en incisivos** (indica los grados exactos leídos en la foto).
     * **Torque (`La`/`Li`) >8-10°** y **Angulación/Tip (`M`/`D`) >4-5°**.
     * **Extrusiones / Intrusiones (`E`/`I`) >1.0 mm** y **Traslaciones (`B`/`L` o `M`/`D`) críticas**.
3. **Evaluación de la Anchura de Arcada, Bolton y Sobremordida (OB/OJ):**
   - Evalúa si hay colapso intercanino (`3-3` negativo), riesgo de mordida profunda secundaria (si el OB objetivo sube a ~3 mm al retruir/cerrar espacios) o falta de coordinación transversal.
4. **Evaluación del Gráfico `MovE` (Staging y Tiempos de IPR):**
   - Indica si el técnico ha movido todos los dientes simultáneamente de la etapa 1 a la final sin secuenciar, y si los rombos azules de IPR están demasiado tarde (ej. etapa 14-19 en vez de hacerse al inicio antes de desrotar/retruir).
5. **Soluciones y Trucos Biomecánicos Angel Aligner a Aplicar:**
   - Qué ataches cambiar o añadir (**Atache DGZ** M-gingival/S-incisal, HBO de extrusión con 0.1 mm de espacio interproximal, ataches de rotación + retención, ataches en palatino si hay AngelButton, levantes anteriores curvos/inclinados, sobrecorrecciones).
6. **📝 LISTA NUMERADA LISTA PARA COPIAR Y PEGAR AL TÉCNICO CAD DE iORTHO:**
   - Redacta las instrucciones exactas diente por diente para pedir la modificación del Setup.
Incluye entre paréntesis los nombres de las láminas `.jpg` del catálogo cuando menciones un protocolo o atache para mostrarlas en pantalla.
"""
        with st.spinner("Leyendo tablas de iOrtho diente por diente y auditando biomecánica..."):
            try:
                contenido_envio = [prompt_fase2]
                if capturas_iortho:
                    contenido_envio.extend(imagenes_pil)
                respuesta_aud = modelo.generate_content(contenido_envio)
                st.session_state.ultima_auditoria = respuesta_aud.text
            except Exception as e:
                st.error(f"Detalle del error de conexión con Google Gemini: {e}")

    if st.session_state.ultima_auditoria:
        st.markdown("---")
        st.markdown("### 🔬 Informe de Auditoría Biomecánica y Cambios para iOrtho")
        st.markdown(st.session_state.ultima_auditoria)
        mostrar_fotos_referencia(st.session_state.ultima_auditoria)

# ==============================================================================
# PESTAÑA 3: CHAT CLÍNICO INTERACTIVO
# ==============================================================================
with tab_chat:
    st.subheader("💬 Chat Clínico — Consultas sobre Casos, Ataches y Protocolos Angel Aligner")
    st.caption("Haz cualquier pregunta de seguimiento sobre el caso o consulta dudas del 'ladrillo' (ej. '¿Cómo pido el atache DGZ en el 43?' o '¿Cómo manejo una mordida cruzada unilateral derecha en un niño de 7 años?').")

    for msg in st.session_state.chat_angel:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["texto"])
            if msg["rol"] == "assistant":
                mostrar_fotos_referencia(msg["texto"])

    pregunta_chat = st.chat_input("Escribe tu consulta clínica sobre Angel Aligner...")

    if pregunta_chat:
        st.session_state.chat_angel.append({"rol": "user", "texto": pregunta_chat})
        with st.chat_message("user"):
            st.markdown(pregunta_chat)

        with st.chat_message("assistant"):
            try:
                historial_api = [
                    {"role": "user" if m["rol"] == "user" else "model", "parts": [m["texto"]]}
                    for m in st.session_state.chat_angel[:-1]
                ]
                chat = modelo.start_chat(history=historial_api)
                resp = chat.send_message(pregunta_chat)
                st.markdown(resp.text)
                mostrar_fotos_referencia(resp.text)
                st.session_state.chat_angel.append({"rol": "assistant", "texto": resp.text})
            except Exception as e:
                st.error(f"Detalle del error de conexión con Google Gemini: {e}")
