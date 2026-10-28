import os
import re
import zipfile
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai
from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

# 1. Configuración general de la página
st.set_page_config(
    page_title="Asistente Clínico Angel Aligner - iOrtho",
    page_icon="🦷",
    layout="wide"
)

CARPETA_FOTOS = "fotos_angel"

# ==============================================================================
# 2. MOTOR AUTO-EXTRACTOR DE LA BASE DE DATOS VISUAL (PDFs + ZIP + HEIC)
# ==============================================================================
def buscar_pdf_en_repo(palabra_clave):
    for f in os.listdir("."):
        if f.lower().endswith(".pdf") and palabra_clave.lower() in f.lower():
            return f
    return None

def extraer_pagina_y_recortes(ruta_pdf, num_pagina_1based, nombre_salida, extraer_subimagenes=False, prefijo_sub=""):
    if not ruta_pdf or not os.path.isfile(ruta_pdf):
        return
    ruta_destino = os.path.join(CARPETA_FOTOS, nombre_salida)
    try:
        doc = fitz.open(ruta_pdf)
        if 1 <= num_pagina_1based <= len(doc):
            page = doc.load_page(num_pagina_1based - 1)
            if not os.path.isfile(ruta_destino):
                pix = page.get_pixmap(dpi=200)
                pix.save(ruta_destino)
            if extraer_subimagenes:
                img_list = page.get_images(full=True)
                for idx, img_info in enumerate(img_list, start=1):
                    xref = img_info[0]
                    base_img = doc.extract_image(xref)
                    if base_img and base_img.get("image"):
                        ext = base_img.get("ext", "jpg")
                        sub_name = f"{prefijo_sub}_Fig{idx}.{ext}"
                        sub_path = os.path.join(CARPETA_FOTOS, sub_name)
                        if not os.path.isfile(sub_path) and base_img.get("width", 0) > 120 and base_img.get("height", 0) > 120:
                            with open(sub_path, "wb") as out_f:
                                out_f.write(base_img["image"])
        doc.close()
    except Exception:
        pass

@st.cache_resource
def construir_base_datos_visual():
    os.makedirs(CARPETA_FOTOS, exist_ok=True)

    pdf_dgz = buscar_pdf_en_repo("pdf569")
    pdf_cuaderno = buscar_pdf_en_repo("CUADERNO")
    pdf_angel1 = buscar_pdf_en_repo("ANGEL1")
    pdf_sao = buscar_pdf_en_repo("ArticuloSAO")
    pdf_brochure = buscar_pdf_en_repo("Brochure")

    # 1. Artículo del Atache DGZ (pdf569.pdf) - Extrae láminas y recortes de las figuras
    extraer_pagina_y_recortes(pdf_dgz, 4, "01_Atache_DGZ_Geometria_Vectores.jpg", True, "01_Recorte_DGZ_P4")
    extraer_pagina_y_recortes(pdf_dgz, 8, "02_Atache_DGZ_Cierre_Diastema_MARPE.jpg", True, "02_Recorte_DGZ_P8")
    extraer_pagina_y_recortes(pdf_dgz, 9, "03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg", True, "03_Recorte_DGZ_P9")
    extraer_pagina_y_recortes(pdf_dgz, 10, "04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg", True, "04_Recorte_DGZ_P10")

    # 2. Cuaderno Angel Academy (ANGEL ACADEMY CUADERNO.pdf)
    extraer_pagina_y_recortes(pdf_cuaderno, 2, "05_Notas_Tips_Trucos_Zamora_Vignolo.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 17, "06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg", True, "06_Recorte_IRS")
    extraer_pagina_y_recortes(pdf_cuaderno, 21, "07_Material_Dual_MasterControl_S_Y_MC.jpg", True, "07_Recorte_Material")
    extraer_pagina_y_recortes(pdf_cuaderno, 24, "08_Caso_Intraoral_AngelButton_Y_TADs.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 27, "09_Lineas_De_Corte_Variable_3_Tipos.jpg", True, "09_Recorte_Corte")
    extraer_pagina_y_recortes(pdf_cuaderno, 28, "10_Esquema_3D_Ataches_Y_Areas_Presion.jpg", True, "10_Recorte_3D")
    extraer_pagina_y_recortes(pdf_cuaderno, 29, "11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 30, "12_Tabla_2_Ataches_De_Precision.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 31, "13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 32, "14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 33, "15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 34, "16_Detalle_Clinico_AngelButton_TAD.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 35, "17_Detalle_Perfil_AngelButton_TPU.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 36, "18_Figura_4_Aplicaciones_AngelButton_360.jpg", True, "18_Recorte_AngelButton")
    extraer_pagina_y_recortes(pdf_cuaderno, 37, "19_Figura_5_Angel_Hook_Protraccion_CIII.jpg", True, "19_Recorte_AngelHook")
    extraer_pagina_y_recortes(pdf_cuaderno, 38, "20_Protocolo_A6_Reglas_Avance_Mandibular.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 39, "21_Figura_6_Avance_Mandibular_A6_Bloques.jpg", True, "21_Recorte_A6")
    extraer_pagina_y_recortes(pdf_cuaderno, 43, "22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 44, "23_Porfolio_Angel_Pro_7_Mas_3.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 45, "24_Protocolo_Angel_Kid_Notas_Romina.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 46, "25_Esquema_Angel_Kid_Levantes_Y_A6.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 47, "26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg")
    extraer_pagina_y_recortes(pdf_cuaderno, 48, "27_Tabla_Aditamentos_Angel_Kid.jpg")

    # 3. Catálogo General Angel Aligner (ANGEL1.pdf)
    extraer_pagina_y_recortes(pdf_angel1, 6, "28_IRS_Control_Corona_Raiz_CBCT.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 8, "29_Esquema_Biomecanico_A6_Avance_Mandibular.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 9, "30_Protocolos_A7_Extracciones_Y_A8_Distalizacion.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 12, "31_Catalogo_Visual_AngelAttach.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 13, "32_Catalogo_Visual_Areas_Presion_Y_Auxiliares.jpg")

    # 4. Artículo SAO Clase II con A6 (ArticuloSAO_CII.pdf)
    extraer_pagina_y_recortes(pdf_sao, 3, "33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg", True, "33_Recorte_BloquesA6")
    extraer_pagina_y_recortes(pdf_sao, 4, "34_Curva_Crecimiento_Y_5_Pasos_Clase_II.jpg")
    extraer_pagina_y_recortes(pdf_sao, 5, "35_Opciones_Elasticos_Clase_II_Con_A6.jpg", True, "35_Recorte_ElasticosA6")

    # 5. Caso Clínico Clase III con Pro y A8 (Brochure Zamora)
    extraer_pagina_y_recortes(pdf_brochure, 6, "36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg", True, "36_Recorte_SetupCIII")
    extraer_pagina_y_recortes(pdf_brochure, 7, "37_Caso_Clase_III_Pro_Evolucion_Intraoral.jpg")

    # 6. Extraer fotos clínicas si el usuario sube un archivo .zip del curso
    for f in os.listdir("."):
        if f.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(f, "r") as z:
                    for member in z.namelist():
                        if "__MACOSX" in member or os.path.basename(member).startswith("._"):
                            continue
                        bname = os.path.basename(member)
                        if bname.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
                            nombre_limpio = os.path.splitext(bname)[0] + ".jpg"
                            out_img_path = os.path.join(CARPETA_FOTOS, f"Curso_{nombre_limpio}")
                            if not os.path.isfile(out_img_path):
                                with z.open(member) as img_file:
                                    im = Image.open(img_file).convert("RGB")
                                    im.save(out_img_path, "JPEG", quality=90)
            except Exception:
                pass

construir_base_datos_visual()

# 3. Configurar la API de Google Gemini desde Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 4. Función para mostrar automáticamente las láminas/fotos de referencia mencionadas por la IA
def mostrar_fotos_referencia(texto_respuesta):
    if not os.path.isdir(CARPETA_FOTOS):
        return
    patron = r"[A-Za-z0-9_]+\.(?:jpg|png|jpeg)"
    encontradas = list(dict.fromkeys(re.findall(patron, texto_respuesta)))
    archivos_validos = [f for f in encontradas if os.path.isfile(os.path.join(CARPETA_FOTOS, f))]
    if archivos_validos:
        st.markdown("#### 🖼️ Documentos Gráficos de Referencia:")
        cols = st.columns(min(len(archivos_validos), 2))
        for idx, nombre_foto in enumerate(archivos_validos):
            ruta = os.path.join(CARPETA_FOTOS, nombre_foto)
            with cols[idx % 2]:
                st.image(ruta, caption=f"📌 {nombre_foto}", use_container_width=True)

# 5. Barra lateral: Biblioteca Gráfica Interactiva
st.sidebar.title("🦷 Biblioteca Gráfica Angel")
archivos_graficos = []
if os.path.isdir(CARPETA_FOTOS):
    archivos_graficos = sorted([
        f for f in os.listdir(CARPETA_FOTOS)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])

if archivos_graficos:
    st.sidebar.success(f"✅ {len(archivos_graficos)} láminas cargadas en la base de datos visual")
    foto_sel = st.sidebar.selectbox(
        "Consultar lámina o esquema clínico:",
        ["Selecciona una imagen..."] + archivos_graficos
    )
    if foto_sel != "Selecciona una imagen...":
        st.sidebar.image(
            os.path.join(CARPETA_FOTOS, foto_sel),
            caption=foto_sel,
            use_container_width=True
        )
else:
    st.sidebar.info(
        "💡 Sube los PDFs (`pdf569.pdf`, `ANGEL ACADEMY CUADERNO.pdf`, `ANGEL1.pdf`, `ArticuloSAO_CII.pdf`) "
        "a tu repositorio de GitHub para que la aplicación extraiga todas las fotos automáticamente."
    )

if st.sidebar.button("🗑️ Limpiar memoria de consultas"):
    st.session_state.chat_angel = []
    st.session_state.ultima_prescripcion = ""
    st.session_state.ultima_auditoria = ""
    st.rerun()

# ==============================================================================
# 6. EL "LADRILLO" / FRAMEWORK BIOMECÁNICO COMPLETO DE ANGEL ALIGNER
# ==============================================================================
FRAMEWORK_ANGEL_ALIGNER = """
Actúa como un Ortodoncista Senior y Director Clínico experto en el sistema Angel Aligner (plataforma iOrtho), entrenado estrictamente con los protocolos clínicos, artículos científicos y anotaciones de los Dres. David González Zamora y Romina Vignolo Lobato (Angel Academy).

REGLA CRÍTICA SOBRE DOCUMENTOS GRÁFICOS Y FOTOS DE REFERENCIA:
Tienes conectada una base de datos visual en la carpeta `fotos_angel/`. SIEMPRE que expliques un atache (especialmente el Atache DGZ), una línea de corte, una herramienta de iOrtho o un protocolo clínico, DEBES escribir entre paréntesis el nombre exacto del archivo `.jpg` de esta lista para que la aplicación muestre automáticamente la imagen en pantalla:
- `01_Atache_DGZ_Geometria_Vectores.jpg` y `01_Recorte_DGZ_P4_Fig1.jpg`: Geometría del Atache DGZ (Double Gripping Zag) con lóbulo gingival (M) y lóbulo incisal (S) y vectores de fuerza F1 y F2 a ambos lados del centro de resistencia.
- `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`: Planificación en iOrtho y evolución clínica intraoral del cierre de diastema post-MARPE con Atache DGZ.
- `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`: Setup 3D del Atache DGZ para control de tip en caninos, premolares y enderezamiento molar.
- `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`: Comparativa biomecánica entre el atache de doble tip clásico de Invisalign (d=4mm, F=0.5N) y el Atache DGZ (d=10.7mm, F=0.19N).
- `05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`: Resumen de tips y trucos clínicos de David González Zamora y Romina Vignolo (citas, TADs, A8, curva de Spee).
- `06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg`: Cefalometría asistida por IA e integración radicular 3D con CBCT (IRS - Intelligent Root System).
- `07_Material_Dual_MasterControl_S_Y_MC.jpg`: Estructura del sistema dual Angel Aligner Pro (7 días MasterControl S multicapa + 3 días MasterControl TPU rígido).
- `08_Caso_Intraoral_AngelButton_Y_TADs.jpg`: Fotografía intraoral de tratamiento con AngelButtons, recortes y microtornillos.
- `09_Lineas_De_Corte_Variable_3_Tipos.jpg`: Comparativa 3D de Línea de corte festoneada gingival, recta alta a 2.5 mm y mixta (festoneada anterior + 2.5 mm posterior).
- `10_Esquema_3D_Ataches_Y_Areas_Presion.jpg`: Vista 3D de ataches y áreas de presión en iOrtho.
- `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`: Tabla 1 oficial de Ataches convencionales (Rectangular, Rotación con bisel invertido, HBO de extrusión/torque, Rotación+Extrusión, Retención y DGZ).
- `12_Tabla_2_Ataches_De_Precision.jpg`: Tabla 2 oficial de Ataches de precisión de control radicular y rotación.
- `13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`: Tabla 3 oficial de Áreas de presión de torque, de intrusión (>2.5 mm) y de rotación (12° a 25°).
- `14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg`: Tabla 4 oficial de Recortes para elástico, botón y bracket/tubo para arcos seccionales.
- `15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg`: Tabla 5 oficial de Levantes de mordida posteriores (bite bubbles), anteriores (bite turbos) e inclinados.
- `16_Detalle_Clinico_AngelButton_TAD.jpg` y `17_Detalle_Perfil_AngelButton_TPU.jpg`: Fotografías intraorales en detalle del AngelButton integrado.
- `18_Figura_4_Aplicaciones_AngelButton_360.jpg`: Esquema completo de todas las mecánicas de elásticos con AngelButton (Clase II, Clase III, cruzados, diagonales de línea media, extrusión e intrusión con TADs).
- `19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`: Detalle del Angel Hook para tracción anterior del maxilar con máscara facial en Clase III.
- `20_Protocolo_A6_Reglas_Avance_Mandibular.jpg` y `21_Figura_6_Avance_Mandibular_A6_Bloques.jpg`: Protocolo A6 y fotografías intraorales de los bloques de avance mandibular.
- `22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg` y `23_Porfolio_Angel_Pro_7_Mas_3.jpg`: Especificaciones de Angel Aligner Select y Pro.
- `24_Protocolo_Angel_Kid_Notas_Romina.jpg`, `25_Esquema_Angel_Kid_Levantes_Y_A6.jpg`, `26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg` y `27_Tabla_Aditamentos_Angel_Kid.jpg`: Protocolos y aditamentos de Angel Aligner KiD (K1 y K2).
- `28_IRS_Control_Corona_Raiz_CBCT.jpg`: Esquema de los 4 tipos de movimiento corona-raíz en el sistema IRS.
- `29_Esquema_Biomecanico_A6_Avance_Mandibular.jpg`: Esquema biomecánico de apertura y avance con bloques A6.
- `30_Protocolos_A7_Extracciones_Y_A8_Distalizacion.jpg`: Esquema biomecánico de las soluciones A7 (Extracción de premolares) y A8 (Distalización molar).
- `31_Catalogo_Visual_AngelAttach.jpg` y `32_Catalogo_Visual_Areas_Presion_Y_Auxiliares.jpg`: Catálogo visual de todos los ataches, áreas de presión, pónticos, power-arm y guías de erupción.
- `33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg`, `34_Curva_Crecimiento_Y_5_Pasos_Clase_II.jpg` y `35_Opciones_Elasticos_Clase_II_Con_A6.jpg`: Figuras del artículo científico de Clase II (bloques rectos vs inclinados, curva de crecimiento y elásticos).
- `36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg` y `37_Caso_Clase_III_Pro_Evolucion_Intraoral.jpg`: Caso clínico de Clase III tratado en 39 alineadores Pro con protocolo A8.

====================================================================
1. PORFOLIO DE PRODUCTOS, MATERIALES Y RITMO CLÍNICO
====================================================================
- ACTIVACIÓN POR ETAPA: Los alineadores Angel Aligner tienen una magnitud de activación lineal entre **0.27 mm y 0.33 mm** por etapa.
- ANGEL ALIGNER SELECT (`22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg`): Fabricado en `MasterControl S` (MCS, triple capa de PET-G modificado + TPU).
  * **Select 10:** Hasta 10 etapas, apiñamiento/espaciado <=2 mm, mejora de OB <=1 mm/arcada, rotaciones <=20°. No apto para extracciones ni A6. Incluye 1 refinamiento (10 etapas) y 1 juego de retenedores (validez 1 año).
  * **Select 20:** Hasta 20 etapas, apiñamiento/espaciado <=5 mm/arcada, corrección AP <=2.5 mm, rotaciones <=40°, OB <=2.5 mm/arcada. Incluye 2 refinamientos y 2 juegos de retenedores (2 años).
  * **Select 30:** Hasta 30 etapas, corrección sagital <=4.5 mm, apiñamiento/espaciado <=10 mm/arcada, rotaciones <=60°, mejora vertical <=4.5 mm/arcada. Incluye 3 refinamientos de 30 etapas y 1 juego de retenedores (3 años).
  * **Select Unlimited:** Sin límite de alineadores ni refinamientos durante 5 años, 1 juego de retenedores, opción de Avance Mandibular A6.
- ANGEL ALIGNER PRO (`07_Material_Dual_MasterControl_S_Y_MC.jpg`, `23_Porfolio_Angel_Pro_7_Mas_3.jpg`):
  * **REGLA CLÍNICA:** **NO USARLO EN PACIENTES PERIODONTALES**.
  * Sistema dual `7+3` en cada etapa: **7 días con `MasterControl S`** (multicapa flexible para iniciar el movimiento con fuerza suave y constante) + **3 días con `MasterControl`** (TPU más grueso y rígido para expresar el control radicular, el torque y los movimientos en masa).
  * Incluye alineadores y refinamientos ilimitados durante 6 años y 3 juegos de retenedores (de 0.76 mm en TPU MasterControl).
- ANGEL ALIGNER KiD (`24_Protocolo_Angel_Kid_Notas_Romina.jpg` a `27_Tabla_Aditamentos_Angel_Kid.jpg`):
  * **K1:** Dentición temporal y mixta (1ª y 2ª fase), alineadores y refinamientos ilimitados durante **2 años** (24 meses) + 1 juego de retenedores. **Truco clínico:** Si al paciente le queda aunque sea un diente de leche, escanear y empezar con un caso KiD (sale más económico).
  * **K2:** Fase 2 para dentición permanente (solo accesible si llevó K1 previamente, con ventana de hasta 10 años para activarlo), ilimitado durante **5 años** + 1 juego de retenedores.
- GESTIÓN DE CITAS DEL DR. DAVID GONZÁLEZ ZAMORA (`05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`):
  * Revisiones cada **2 meses**, entregando **6 alineadores por tanda**.
  * Programar el IPR y acciones clínicas para que coincidan con las citas en los alineadores **7, 13, 19...**
  * Tomar el escáner intraoral **con los ataches puestos** en refinamientos y luego evaluar en el software cuál se queda y cuál se quita (iOrtho marca con un punto rojo los ataches que cambian).

====================================================================
2. LÍNEA DE CORTE VARIABLE (TRIMMING LINE) (`09_Lineas_De_Corte_Variable_3_Tipos.jpg`)
====================================================================
1) **Línea de corte festoneada a nivel gingival (0 mm):** Más estética, indicada en pacientes periodontales o con recesiones.
2) **Línea de corte recta alta a 2.5 mm del margen gingival:** Mayor retención, estabilidad y control biomecánico para expansión, distalización, control de torque anterior (junto a HBO central + torque ridge), máscara facial y aparatos funcionales.
   * **Precauciones:** Si se pide línea de corte alta, regular/reducir la retención de los ataches para que el paciente pueda desinsertar el alineador. En adultos no mantenerla más de 20 etapas seguidas si molesta en la zona lingual inferior. En casos de sobremordida donde se busque levantar la mordida con rampas, expansión y torque ridge + atache de extrusión anterior, no poner la línea de corte alta al principio sino más adelante.
3) **Línea de corte mixta (Festoneada a nivel gingival en sector anterior + Recta a 2.5 mm en sector posterior):**
   * **En niños:** Pedir siempre línea de corte alta en niños SALVO si están erupcionando los incisivos permanentes; en ese caso pedir **línea de corte mixta** (evita interferencias gingivales en anterior mientras mantiene máximo agarre expansivo en los molares posteriores).
   * **En adultos:** Muy útil en fases largas de expansión cuando no se necesita un control crítico de torque incisivo anterior.

====================================================================
3. BIOMECÁNICA DE ATACHES, ATACHE DGZ, ÁREAS DE PRESIÓN Y AUXILIARES
====================================================================
A) ATACHE DGZ ("Double Gripping Zag Attachment" — Zamora & Vignolo, 2025) (`01_Atache_DGZ_Geometria_Vectores.jpg`, `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`, `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`, `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`, `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Qué es y cómo se diseña:** Dispositivo de doble lóbulo biselado diseñado para optimizar el control del **tip mesiodistal y el movimiento en masa**. Consta de dos lóbulos separados diagonalmente al máximo dentro de la corona clínica (respetando 1 mm de margen incisal, gingival, mesial y distal):
  * **Lóbulo gingival (Talla M):** Ubicado a 1 mm del margen gingival (ej. en mesial-gingival), con su superficie activa biselada aplicando una fuerza en dirección incisal ($F_1$). Además aporta retención cervical evitando que el alineador se desadapte.
  * **Lóbulo incisal (Talla S):** Ubicado en el extremo opuesto a 1 mm del borde incisal (ej. en distal-incisal), con su superficie activa biselada aplicando una fuerza paralela y opuesta en dirección gingival ($F_2$).
- **Justificación física exacta:** En un incisivo central estándar ($8.5\text{ mm}$ de ancho x $10.5\text{ mm}$ de alto), el atache doble clásico de Invisalign tiene una separación efectiva de solo $d = 4\text{ mm}$ y sus vectores pasan por el mismo lado (incisal) lejos del Centro de Resistencia (CR), exigiendo $0.50\text{ N}$ por lóbulo. El **Atache DGZ** alcanza una separación diagonal de **$d = \sqrt{6.5^2 + 8.5^2} \approx 10.7\text{ mm}$** y sus vectores pasan **a ambos lados (mesial y distal) del Centro de Resistencia**, generando el mismo momento rotacional puro ($2\text{ N}\cdot\text{mm}$ por grado de tip) con solo **$0.19\text{ N}$** de fuerza, sin traslación parásita y protegiendo el periodonto.
- **Indicaciones clínicas del Atache DGZ (preferirlo siempre frente al atache rectangular o al doble tip clásico):**
  1) Cierre de diastemas interincisivos (ej. tras disyunción con MARPE, evitando el uso de *power arms*).
  2) Corrección de tip radicular en caninos (especialmente caninos inferiores), premolares y molares.
  3) Enderezamiento de molares inclinados (*molar straightening*).
  4) Movimientos en masa de dientes posteriores y caninos en casos de extracción de premolares.
  * **Limitación:** No colocarlo en **incisivos inferiores** porque su pequeña dimensión mesiodistal y altura no permite alojar los dos lóbulos.

B) REGLAS DE LOS DEMÁS ATACHES CONVENCIONALES (`11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Bisel invertido respecto a Invisalign:** En Angel Aligner la superficie activa es el bisel más corto; tanto en el **atache de rotación** como en el **atache de extrusión (HBA/HBO)** el bisel va orientado **al revés que en Invisalign** (no darles la vuelta por error).
- **Atache HBA / HBO (Horizontal Biselado):**
  * Si se coloca en el **tercio/borde incisal** (con el bisel hacia incisal/gingival activo) = sirve para **EXTRUSIÓN** (menor contramomento).
  * Si se coloca en el **CENTRO de la corona clínica** = sirve para dar **TORQUE a los incisivos** (combinado con *torque ridge* / área de presión de torque y línea de corte alta en casos de sobremordida).
  * Puede convivir en la misma cara con puntos/áreas de presión dejando **1 mm de distancia**.
- **Atache de Rotación + Extrusión (Caninos y Premolares):** Secuenciar haciendo **primero la rotación y luego la extrusión**, colocando atache de rotación por vestibular y atache de retención por palatino.
- **Atache de Retención (Caninos, Premolares y Molars):**
  * Imprescindible en expansiones y en dientes de anclaje cuando queremos intruir dientes vecinos (ej. **para intruir 11 y 21, colocar ataches de retención en 12 y 13**).
  * En incisivos inferiores estrechos, el atache convencional de retención también funciona muy bien para extrusión si el paciente colabora.
  * En niños pequeños (dentición temporal/mixta), poner **ataches grandes ("ladrillos")** porque muerden el alineador al ponérselo y los dientes temporales son expulsivos.

C) ÁREAS DE PRESIÓN (`13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`):
- **Área de presión de torque (Torque Ridge):** En incisivos y caninos para torque radiculolingual. Con esto no hace falta PIR; lleva un atache HBO en el mismo diente y se puede combinar con rampas de mordida y línea de corte alta.
- **Área de presión de intrusión:** En incisivos, específica para **intrusiones mayores a 2.5 mm**.
- **Área de presión de rotación (Crestas de rotación):** En incisivos y caninos para **rotaciones entre 12° y 25°**. Facilita la desrotación sin alterar su velocidad máxima por etapa (**Pro = 2.2°/etapa**, **Select = 1.8°/etapa**). En incisivos se aplica en pares (bucal y palatino), o solo en palatino si ya lleva atache vestibular (aunque bajo solicitud manual al técnico se pueden poner ambos en la misma cara a >=1 mm de distancia).

D) RECORTES, POWER ARMS Y LEVANTES DE MORDIDA (`14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg`, `15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg`):
- **Recorte para bracket/tubo:** Solicitarlo cuando queramos usar **arcos seccionales para mesializar molares**.
- **Power Arms:** Pueden ir cementados directamente al diente mediante recorte para botón o **crimpables metidos dentro de un attachment**.
- **Levantes de mordida posteriores (*Bite bubbles* / *Occlusal pads*):** En premolares y molares para mordida abierta, mordida cruzada posterior o anterior y mordida en tijera. **Nunca cementarlos/rellenarlos**. Ponerlos solo en las etapas necesarias para evitar crear una mordida abierta posterior (en niños verticales/dolicofaciales se usan como estímulo masticatorio para que el paciente los apriete y active la musculatura maseterina).
- **Levantes de mordida anteriores (*Bite turbos*):** De 3 a 3 en incisivos y caninos para intrusión anterior y sobremordida aumentada. **Mejor sin cementar (redondeados adaptativos)**. Vigilar en el setup que con el resalte inicial los incisivos inferiores ocluyan realmente sobre el levante y no por detrás de él.
- **Levante de mordida anterior inclinado:** Exclusivo de Angel Aligner en incisivos para ayudar a la corrección de **Clase II con resalte menor a 3 mm** (o como retención activa en Fase II tras retirar bloques A6).

E) ANGELBUTTON™ Y ANGEL HOOK (`16_Detalle_Clinico_AngelButton_TAD.jpg` a `19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`):
- **AngelButton™:** Integrado en el alineador en TPU MasterControl (soporta hasta **500 g**). Reparte la fuerza elástica en toda la arcada, mientras que el botón cementado directo al diente concentra la fuerza en esa raíz (y tiende a extruirlo).
  * **Regla en mordida cruzada:** Si se usa AngelButton para elásticos cruzados, colocar siempre **atache en palatino** para retención y que no se desadapte el plástico.
  * **Regla en Clase II de pacientes braquifaciales:** Si queremos extruir el molar inferior, poner **AngelButton en canino superior** y **botón cementado directo en el 6 inferior**, añadiendo **ataches de retención en el 7 y en el 5 inferiores** para facilitar la extrusión posterior.
  * **Elásticos diagonales anteriores:** De AngelButton de canino superior a AngelButton de canino inferior contralateral para centrar la línea media cuando existe un resalte canino mayor en un lado que en otro.
  * **Cupla de rotación con elásticos:** Botón cementado directo al diente rotado + AngelButton.
- **Angel Hook:** Gancho integrado para tracción anterior con máscara facial en Clase III esquelética cuando **solo queremos traccionar del maxilar superior**. Si además queremos mover dientes simultáneamente, colocar **AngelButtons**.

====================================================================
4. PROTOCOLOS ESPECÍFICOS POR MALOCLUSIÓN Y EDAD
====================================================================
A) PROTOCOLO A8 (DISTALIZACIÓN MOLAR) Y CLASE II (`05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`, `30_Protocolos_A7_Extracciones_Y_A8_Distalizacion.jpg`, `34_Curva_Crecimiento_Y_5_Pasos_Clase_II.jpg`):
- **Los 5 pasos biomecánicos en Clase II con alineadores:**
  1) Corregir cualquier rotación mesial de los 1º y 2º molares superiores (abre hasta 2 mm por lado).
  2) Expandir la arcada maxilar para corregir la deficiencia transversal relativa y ganar espacio.
  3) Coordinar arcadas superior e inferior.
  4) Sobrecorregir el torque lingual de los incisivos maxilares (salvo en protocolo A6 con bloques).
  5) Utilizar elásticos de Clase II (**4/16" [1/4"] de 4.5 oz**).
- **Control vertical en Protocolo A8:** Distalización molar secuencial a lo largo de la curva de compensación + uso de elásticos en AngelButton para control vertical y de anclaje anterior + rampas de mordida anteriores para desocluir y compensar la curva de Spee.
- **En niños (Angel KiD):** Se puede hacer distalización arriba y abajo de forma simultánea (los seises tienen que ir juntos; en Clase I distalar ambos a la par; en Clase II empezar por el molar superior hasta alcanzar Clase I y luego juntos). Dejar siempre **0.5 mm de espacio en mesial y distal de los caninos de leche** (espacio de primate) y pedir **compensador de erupción en los 7s** (sobre todo en dolicofaciales).

B) PROTOCOLO A6 (AVANCE MANDIBULAR) (`20_Protocolo_A6_Reglas_Avance_Mandibular.jpg`, `21_Figura_6_Avance_Mandibular_A6_Bloques.jpg`, `33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg`, `35_Opciones_Elasticos_Clase_II_Con_A6.jpg`):
- **Momento óptimo:** Primer pico de crecimiento entre **5 y 7 años** (segunda infancia, al erupcionar los 1º molares permanentes, maduración vertebral fin de C1 a fin de C2) o en el pico prepuberal (CS3-CS4).
- **Diseño del bloque:** Pedir **SIEMPRE BLOQUES RECTOS (Tipo I)**; prohibido usar los bloques inclinados (Tipo II) porque intruyen los molares y el paciente muerde con el borde generando mordida abierta posterior.
- **Ubicación del bloque:** En dentición mixta colocar los bloques **lo más posterior posible cubriendo como mínimo el primer molar inferior definitivo** (para evitar el efecto intrusivo de combate sobre el molar y permitir intruir el incisivo); en dentición permanente colocarlos más a nivel anterior.
- **Magnitud del avance:** Nunca hacer micro-avances incrementales; el salto debe ser completo (mínimo **4 mm** para separar el cóndilo de la cavidad glenoidea y máximo **7 mm**; si requiere más en niños muy pequeños, dividir en solo 2 saltos). Criterio de mordida constructiva: apertura vertical de 4–6 mm en premolares, 1–2 mm en anterior y sobrecorrección de 2–3 mm.
-
