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
# 2. MOTOR AUTO-EXTRACTOR DE LA BASE DE DATOS VISUAL (PDF 40 PÁGS + CARPETA FOTOS)
# ==============================================================================
def buscar_pdf_en_repo(palabra_clave):
    for raiz, _, archivos in os.walk("."):
        if CARPETA_FOTOS in raiz or ".git" in raiz:
            continue
        for f in archivos:
            if f.lower().endswith(".pdf") and palabra_clave.lower() in f.lower():
                return os.path.join(raiz, f)
    return None

def limpiar_nombre_archivo(nombre_base):
    limpio = re.sub(r"[^A-Za-z0-9_]", "_", nombre_base)
    limpio = re.sub(r"_+", "_", limpio).strip("_")
    return limpio

def extraer_pagina_y_recortes(ruta_pdf, num_pagina_1based, nombre_salida, extraer_subimagenes=False, prefijo_sub=""):
    if not ruta_pdf or not os.path.isfile(ruta_pdf):
        return
    ruta_destino = os.path.join(CARPETA_FOTOS, nombre_salida)
    try:
        doc = fitz.open(ruta_pdf)
        if 1 <= num_pagina_1based <= len(doc):
            page = doc.load_page(num_pagina_1based - 1)
            if not os.path.isfile(ruta_destino):
                pix = page.get_pixmap(dpi=180)
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

    # 1. Artículo del Atache DGZ (pdf569.pdf - 11 páginas)
    extraer_pagina_y_recortes(pdf_dgz, 4, "01_Atache_DGZ_Geometria_Vectores.jpg", True, "01_Recorte_DGZ_P4")
    extraer_pagina_y_recortes(pdf_dgz, 8, "02_Atache_DGZ_Cierre_Diastema_MARPE.jpg", True, "02_Recorte_DGZ_P8")
    extraer_pagina_y_recortes(pdf_dgz, 9, "03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg", True, "03_Recorte_DGZ_P9")
    extraer_pagina_y_recortes(pdf_dgz, 10, "04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg", True, "04_Recorte_DGZ_P10")

    # 2. Cuaderno Angel Academy (Detecta automáticamente tu versión de 40 páginas con páginas eliminadas)
    if pdf_cuaderno and os.path.isfile(pdf_cuaderno):
        try:
            doc_c = fitz.open(pdf_cuaderno)
            total_pags = len(doc_c)
            doc_c.close()
        except Exception:
            total_pags = 40

        if total_pags <= 42:
            # Mapeo exacto para tu PDF de 40 páginas (con páginas eliminadas)
            extraer_pagina_y_recortes(pdf_cuaderno, 2, "05_Notas_Tips_Trucos_Zamora_Vignolo.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 3, "05b_Indice_Ortodoncia_Interceptiva_Y_Protocolos.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 8, "06a_Esquema_3D_Vias_Aereas_Senos_Raices.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 11, "06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg", True, "06_Recorte_IRS")
            extraer_pagina_y_recortes(pdf_cuaderno, 14, "07_Material_Dual_MasterControl_S_Y_MC.jpg", True, "07_Recorte_Material")
            extraer_pagina_y_recortes(pdf_cuaderno, 15, "07b_Propiedades_MasterControl_S_Triple_Capa.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 16, "07c_Propiedades_MasterControl_Rigido_Pro.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 17, "08_Caso_Intraoral_AngelButton_Y_TADs.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 20, "09_Lineas_De_Corte_Variable_3_Tipos.jpg", True, "09_Recorte_Corte")
            extraer_pagina_y_recortes(pdf_cuaderno, 21, "10_Esquema_3D_Ataches_Y_Areas_Presion.jpg", True, "10_Recorte_3D")
            extraer_pagina_y_recortes(pdf_cuaderno, 22, "11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 23, "12_Tabla_2_Ataches_De_Precision.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 24, "13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 25, "14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 26, "15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 27, "16_Detalle_Clinico_AngelButton_TAD.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 28, "17_Detalle_Perfil_AngelButton_TPU.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 29, "18_Figura_4_Aplicaciones_AngelButton_360.jpg", True, "18_Recorte_AngelButton")
            extraer_pagina_y_recortes(pdf_cuaderno, 30, "19_Figura_5_Angel_Hook_Protraccion_CIII.jpg", True, "19_Recorte_AngelHook")
            extraer_pagina_y_recortes(pdf_cuaderno, 31, "20_Protocolo_A6_Reglas_Avance_Mandibular.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 32, "21_Figura_6_Avance_Mandibular_A6_Bloques.jpg", True, "21_Recorte_A6")
            extraer_pagina_y_recortes(pdf_cuaderno, 34, "22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 35, "23_Porfolio_Angel_Pro_7_Mas_3.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 36, "24_Protocolo_Angel_Kid_Notas_Romina.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 37, "25_Esquema_Angel_Kid_Levantes_Y_A6.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 38, "26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 39, "27_Tabla_Aditamentos_Angel_Kid.jpg")
            extraer_pagina_y_recortes(pdf_cuaderno, 40, "27b_Retenedores_MasterControl_076mm.jpg")
        else:
            # Mapeo por si en algún momento se usa el PDF de 49 páginas
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

    # 6. Procesar todas las fotos sueltas (.JPG, .jpeg, .HEIC) de la carpeta del curso en GitHub
    for raiz, _, archivos in os.walk("."):
        if CARPETA_FOTOS in raiz or ".git" in raiz:
            continue
        for f in sorted(archivos):
            if f.startswith("._"):
                continue
            ruta_completa = os.path.join(raiz, f)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
                try:
                    base_sin_ext = os.path.splitext(f)[0]
                    nombre_limpio = limpiar_nombre_archivo(base_sin_ext)
                    if not nombre_limpio.startswith("Curso_"):
                        nombre_limpio = f"Curso_{nombre_limpio}"
                    out_img_path = os.path.join(CARPETA_FOTOS, f"{nombre_limpio}.jpg")
                    if not os.path.isfile(out_img_path):
                        im = Image.open(ruta_completa).convert("RGB")
                        im.thumbnail((1500, 1500))
                        im.save(out_img_path, "JPEG", quality=85)
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

# 5. Barra lateral: Biblioteca Gráfica Interactiva dividida por categorías
st.sidebar.title("🦷 Biblioteca Gráfica Angel")
archivos_graficos = []
if os.path.isdir(CARPETA_FOTOS):
    archivos_graficos = sorted([
        f for f in os.listdir(CARPETA_FOTOS)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])

if archivos_graficos:
    laminas_manuales = [f for f in archivos_graficos if not f.startswith("Curso_")]
    fotos_curso = [f for f in archivos_graficos if f.startswith("Curso_")]

    st.sidebar.success(f"✅ {len(laminas_manuales)} láminas de manuales + {len(fotos_curso)} fotos del curso cargadas")

    categoria_visor = st.sidebar.radio(
        "Tipo de documento gráfico:",
        ["📘 Láminas y Tablas Oficiales (PDFs)", "📸 Fotos del Curso (IMG_...)"]
    )

    lista_mostrar = laminas_manuales if "Láminas" in categoria_visor else fotos_curso
    foto_sel = st.sidebar.selectbox(
        "Selecciona una imagen para visualizar:",
        ["Selecciona una imagen..."] + lista_mostrar
    )
    if foto_sel != "Selecciona una imagen...":
        st.sidebar.image(
            os.path.join(CARPETA_FOTOS, foto_sel),
            caption=foto_sel,
            use_container_width=True
        )
else:
    st.sidebar.info(
        "💡 Sube los PDFs y las fotos sueltas a tu repositorio de GitHub "
        "para que la aplicación extraiga todas las láminas automáticamente."
    )

if st.sidebar.button("🗑️ Limpiar memoria de consultas"):
    st.session_state.chat_angel = []
    st.session_state.ultima_prescripcion = ""
    st.session_state.ultima_auditoria = ""
    st.rerun()

lista_archivos_disponibles = ", ".join(archivos_graficos) if archivos_graficos else "Ninguna cargada aún"

# ==============================================================================
# 6. EL "LADRILLO" / FRAMEWORK BIOMECÁNICO COMPLETO DE ANGEL ALIGNER
# (Texto puro sin f-string para evitar conflictos con fórmulas)
# ==============================================================================
FRAMEWORK_BASE = """
Actúa como un Ortodoncista Senior y Director Clínico experto en el sistema Angel Aligner (plataforma iOrtho), entrenado estrictamente con los protocolos clínicos, artículos científicos y anotaciones de los Dres. David González Zamora y Romina Vignolo Lobato (Angel Academy).

REGLA CRÍTICA SOBRE DOCUMENTOS GRÁFICOS Y FOTOS DE REFERENCIA:
Tienes conectada una base de datos visual en la carpeta `fotos_angel/`. Archivos disponibles actualmente: [__LISTA_ARCHIVOS__].
SIEMPRE que expliques un atache (especialmente el Atache DGZ), una línea de corte, una herramienta de iOrtho o un protocolo clínico, DEBES escribir entre paréntesis el nombre exacto del archivo `.jpg` de esta lista para que la aplicación muestre automáticamente la imagen en pantalla:
- `01_Atache_DGZ_Geometria_Vectores.jpg` y `01_Recorte_DGZ_P4_Fig1.jpg`: Geometría del Atache DGZ (Double Gripping Zag) con lóbulo gingival (M) y lóbulo incisal (S) y vectores de fuerza F1 y F2 a ambos lados del centro de resistencia.
- `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`: Planificación en iOrtho y evolución clínica intraoral del cierre de diastema post-MARPE con Atache DGZ.
- `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`: Setup 3D del Atache DGZ para control de tip en caninos, premolares y enderezamiento molar.
- `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`: Comparativa biomecánica entre el atache de doble tip clásico de Invisalign (d=4mm, F=0.5N) y el Atache DGZ (d=10.7mm, F=0.19N).
- `05_Notas_Tips_Trucos_Zamora_Vignolo.jpg` y `05b_Indice_Ortodoncia_Interceptiva_Y_Protocolos.jpg`: Resumen de tips y trucos clínicos de David González Zamora y Romina Vignolo (citas, TADs, A8, curva de Spee, guía para la lengua, bloques rectos).
- `06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg` y `06a_Esquema_3D_Vias_Aereas_Senos_Raices.jpg`: Cefalometría asistida por IA, vías aéreas e integración radicular 3D con CBCT (IRS - Intelligent Root System).
- `07_Material_Dual_MasterControl_S_Y_MC.jpg`, `07b_Propiedades_MasterControl_S_Triple_Capa.jpg` y `07c_Propiedades_MasterControl_Rigido_Pro.jpg`: Estructura y tablas de propiedades del sistema dual Angel Aligner Pro (7 días MasterControl S multicapa + 3 días MasterControl TPU rígido).
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
- `24_Protocolo_Angel_Kid_Notas_Romina.jpg`, `25_Esquema_Angel_Kid_Levantes_Y_A6.jpg`, `26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg`, `27_Tabla_Aditamentos_Angel_Kid.jpg` y `27b_Retenedores_MasterControl_076mm.jpg`: Protocolos y aditamentos de Angel Aligner KiD (K1 y K2) y retenedores.
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
  * **Lóbulo gingival (Talla M):** Ubicado a 1 mm del margen gingival (ej. en mesial-gingival), con su superficie activa biselada aplicando una fuerza en dirección incisal (F1). Además aporta retención cervical evitando que el alineador se desadapte.
  * **Lóbulo incisal (Talla S):** Ubicado en el extremo opuesto a 1 mm del borde incisal (ej. en distal-incisal), con su superficie activa biselada aplicando una fuerza paralela y opuesta en dirección gingival (F2).
- **Justificación física exacta:** En un incisivo central estándar (8.5 mm de ancho x 10.5 mm de alto), el atache doble clásico de Invisalign tiene una separación efectiva de solo d = 4 mm y sus vectores pasan por el mismo lado (incisal) lejos del Centro de Resistencia (CR), exigiendo 0.50 N por lóbulo. El **Atache DGZ** alcanza una separación diagonal de **d = raiz_cuadrada(6.5^2 + 8.5^2) = 10.7 mm** y sus vectores pasan **a ambos lados (mesial y distal) del Centro de Resistencia**, generando el mismo momento rotacional puro (2 N·mm por grado de tip) con solo **0.19 N** de fuerza, sin traslación parásita y protegiendo el periodonto.
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
- **Atache de Retención (Caninos, Premolares y Molares):**
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
- **Material y cambio:** El avance mandibular A6 utiliza siempre material flexible con dos juegos por etapa (**5 días + 5 días**).
- **Ataches y Elásticos en A6:** Colocar ataches de retención en todos los dientes posteriores para aplanar la curva de Spee y biselados en incisivos. Acompañar siempre los bloques con **AngelButtons y elásticos de Clase II** (1/4" 4.5 oz para estabilización general, o elástico suave nocturno/tarde para guiar muscularmente la mandíbula hacia adelante).
- **Fase II de consolidación (mínimo 9 meses totales):** Tras la Fase I con bloques A6, pasar a Fase II con **levante anterior inclinado** y elásticos nocturnos para consolidar el cambio muscular en remodelado esquelético.

C) TRANSVERSAL, MORDIDAS CRUZADAS Y ASIMETRÍAS (`24_Protocolo_Angel_Kid_Notas_Romina.jpg`):
- **Mordida cruzada unilateral:** Hacer primero **expansión unilateral del lado de la mordida cruzada** hasta simetrizar con el lado sano (indicando al paciente que mastique por el lado contrario al que masticaba, necesitando ~2 años para remodelar la trayectoria condílea), y en una segunda etapa hacer la **expansión bilateral simétrica** buscando una **arcada cuadrada** en niños que permita frote bilateral.
- **Salto virtual vertical:** Nivelar el plano oclusal superior y el plano inferior de forma independiente y pedir al técnico un **salto virtual vertical** para que la mandíbula anterorrote sola sin extruir dientes artificialmente.

D) CLASE III CON ANGEL ALIGNER PRO Y PROTOCOLO A8 (`36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg`, `37_Caso_Clase_III_Pro_Evolucion_Intraoral.jpg`):
- En adultos jóvenes con Clase III dentoalveolar/esquelética compensable: usar **Angel Aligner Pro (7+3)** con **Protocolo A8 de distalización inferior** en cuadrantes 3 y 4, intrusión anteroinferior para nivelar curva de Spee, control radicular/torque de caninos inferiores (33 y 43) dentro de la cortical con IRS (CBCT), IPR anterior según Bolton y **elásticos de Clase III (3/16", 4.5 oz) conectados a AngelButtons**.

====================================================================
5. REGLAS DE AUDITORÍA DE CAPTURAS DE iORTHO (TABLA TM, BOLTON, OB/OJ, ARCADA, MovE)
====================================================================
Al auditar las capturas de pantalla de iOrtho subidas por el doctor:
1) **Bolton:** Identificar si el exceso (ej. 3-3 o 6-6) se debe a ausencias dentarias (`—` en la tabla M-D, como falta del 42, 17, 37) o desproporción anatómica, y proponer cómo compensarlo (IPR, reconstrucción o cierre con Atache DGZ).
2) **Gráfico MovE (Secuenciación):** Verificar número de etapas activas, ausencias (`X`), cementado de ataches (puntos rojos) y etapas de IPR (rombos azules). Si todos los dientes se mueven en bloque de la etapa 1 a la final en un adulto, exigir secuenciación (ej. patrón en V en distalizaciones o desrotar/expandir antes de retruir) y **adelantar el IPR a las primeras etapas (etapa 1 o 7)**.
3) **Tabla TM (Corona, Centro de resistencia y Ápice radicular):**
   - Detectar todas las celdas marcadas en amarillo/rojo Y las celdas en blanco que superen límites predecibles:
     * **Rotaciones >15° en caninos/premolares o >20° en incisivos:** exigir atache de rotación (o rotación + retención vestibular y retención palatina), área de presión de rotación (en incisivos/caninos entre 12° y 25° respetando velocidad máx 2.2°/etapa en Pro o 1.8°/etapa en Select) y abrir espacio previo.
     * **Tip / Angulación >4-5° o cierre de espacios de extracción/agenesia:** exigir **Atache DGZ (talla M en gingival y S en incisal)**.
     * **Torque >8-10° (`La`/`Li`):** exigir área de presión de torque (*torque ridge*) + atache HBO en el centro de la corona + línea de corte alta a 2.5 mm.
     * **Intrusión >1.0 - 2.5 mm:** exigir ataches de retención en dientes vecinos (ej. en 12 y 13 para intruir 11 y 21) y área de presión de intrusión si supera 2.5 mm.
4) **Anchura de la Arcada (`3-3`, `4-4`, `5-5`, `6-6`):** Alertar si hay estrechamiento/colapso severo de la distancia intercanina (`3-3` muy negativo, ej. `-4.3 mm`) o compresión posterior.
5) **OB/OJ (Sobremordida y Resalte):** Si la sobremordida (OB) objetivo sube cerca de `3.0 mm` al retruir o cerrar espacios, alertar del riesgo de mordida profunda secundaria y pedir **levantes de mordida anteriores adaptativos de 3 a 3** y sobrecorrección vertical.
"""

FRAMEWORK_ANGEL_ALIGNER = FRAMEWORK_BASE.replace("__LISTA_ARCHIVOS__", lista_archivos_disponibles)

# 7. Inicializar el modelo Gemini
modelo = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    system_instruction=FRAMEWORK_ANGEL_ALIGNER
)

# 8. Interfaz Principal
st.title("🦷 Asistente Clínico de Ortodoncia — Angel Aligner (iOrtho)")
st.markdown(
    "Sistema de **Prescripción Inicial**, **Auditoría del Setup 3D (Tabla TM / Bolton / OB-OJ)** y **Base de Datos Gráfica** "
    "basado en los protocolos de los Dres. **David González Zamora y Romina Vignolo Lobato**."
)

if "chat_angel" not in st.session_state:
    st.session_state.chat_angel = []
if "ultima_prescripcion" not in st.session_state:
    st.session_state.ultima_prescripcion = ""
if "ultima_auditoria" not in st.session_state:
    st.session_state.ultima_auditoria = ""

tab_diag, tab_setup, tab_chat = st.tabs([
    "📋 Fase 1: Diagnóstico y Prescripción Inicial",
    "🔍 Fase 2: Auditoría del 1er Setup (Capturas iOrtho / Tabla TM)",
    "💬 Fase 3: Chat Clínico y Buscador Visual (Atache DGZ, Tablas, Protocolos)"
])

# ==============================================================================
# PESTAÑA 1: DIAGNÓSTICO Y PRESCRIPCIÓN INICIAL
# ==============================================================================
with tab_diag:
    st.subheader("📋 Formulario de Diagnóstico Clínico Inicial")
    st.caption("Introduce los datos clínicos del paciente para generar la prescripción inicial exacta para iOrtho.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 1. Paciente y Biotipo")
        tipo_paciente = st.selectbox(
            "Grupo de edad / Dentición",
            [
                "Adulto (Dentición permanente)",
                "Adolescente (Dentición permanente joven)",
                "Niño con algún diente de leche - Candidato a Angel KiD (K1)",
                "Niño en Crecimiento - Dentición Mixta (Pico 5-7 años / C1-C2)",
                "Niño Pequeño - Dentición Temporal (<6 años)"
            ]
        )
        biotipo = st.selectbox(
            "Biotipo Facial",
            ["Mesofacial", "Braquifacial (Tendencia a sobremordida)", "Dolicofacial (Tendencia a mordida abierta)"]
        )
        estado_periodontal = st.selectbox(
            "Estado Periodontal y Colaboración",
            [
                "Periodonto sano / Buena colaboración (Apto para Pro 7+3)",
                "Paciente Periodontal / Recesiones (NO usar Pro, usar Select)",
                "Colaboración dudosa con elásticos",
                "Niño pequeño (requiere ataches grandes por inserción)"
            ]
        )
        habitos_atm = st.multiselect(
            "Hábitos, Lengua, Postura y ATM",
            [
                "Sin alteraciones",
                "Respirador oral / Cornetes hipertróficos",
                "Lengua baja (Candidato a Posicionador Lingual)",
                "Interposición lingual / Succión digital (Candidato a Corrector de hábitos / Tongue Crib)",
                "Duerme boca abajo / apoya mano-hombro en cara",
                "Masticación unilateral predominante",
                "Disfunción ATM / Canteo oclusal"
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
            "Etiología Sagital Principal",
            [
                "Dentoalveolar (candidato a Protocolo A8 de distalización)",
                "Retrusión mandibular en crecimiento (candidato a Protocolo A6 bloques rectos)",
                "Clase II con resalte < 3 mm (candidato a Levantes anteriores inclinados)",
                "Hipoplasia maxilar Clase III en crecimiento (candidato a Angel Hook / AngelButtons + Máscara)",
                "Casos de Extracción de Premolares (Protocolo A7)"
            ]
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
                "Sobremordida aumentada / Curva de Spee marcada (Levantes anteriores de 3 a 3)",
                "Intrusión incisiva > 2.5 mm necesaria (Área de presión de intrusión)",
                "Mordida borde a borde (0 mm)",
                "Mordida abierta anterior (Levantes posteriores / Bite bubbles)",
                "Canteo del plano oclusal (Valorar TADs con cabeza de botón)"
            ]
        )
        problema_transversal = st.selectbox(
            "Situación Transversal",
            [
                "Arcadas simétricas y bien coordinadas",
                "Compresión bilateral simétrica (Expansión simétrica / Arcada cuadrada en niños)",
                "Mordida cruzada posterior UNILATERAL DERECHA (Expandir lado derecho primero)",
                "Mordida cruzada posterior UNILATERAL IZQUIERDA (Expandir lado izquierdo primero)",
                "Mordida cruzada posterior BILATERAL",
                "Mordida en tijera (Brodie)"
            ]
        )
        apinamiento_sup = st.selectbox("Espacio Arcada Superior", ["Sin apiñamiento", "Apiñamiento leve (<=2 mm)", "Apiñamiento moderado (3-5 mm)", "Apiñamiento severo (6-10 mm)", "Diastemas / Cierre post-MARPE (Atache DGZ)"])
        apinamiento_inf = st.selectbox("Espacio Arcada Inferior", ["Sin apiñamiento", "Apiñamiento leve (<=2 mm)", "Apiñamiento moderado (3-5 mm)", "Apiñamiento severo (6-10 mm)", "Diastemas / Espacios"])
        incisivos_inclinacion = st.selectbox("Inclinación de Incisivos (Torque inicial)", ["Normoinclinados", "Proinclinados superior e inferior", "Retroinclinados (requiere HBO central + Torque Ridge + Corte alto)", "Superior proinclinado / Inferior retroinclinado", "Superior retroinclinado / Inferior proinclinado (Compensación CIII)"])

    notas_clinicas_ini = st.text_area(
        "Notas adicionales del caso (ausencias, caninos incluidos, erupción de incisivos/7s, asimetrías):",
        placeholder="Ej: Ausencia del 42, caninos inferiores con tip mesial, o niño con incisivos en erupción..."
    )

    if st.button("🚀 Generar Prescripción Inicial y Esquemas Visuales", type="primary"):
        prompt_fase1 = f"""
Genera la PLANIFICACIÓN BIOMECÁNICA Y PRESCRIPCIÓN INICIAL COMPLETA para enviar este caso a Angel Aligner (iOrtho), aplicando los protocolos de los Dres. David González Zamora y Romina Vignolo:

DATOS DIAGNÓSTICOS DEL PACIENTE:
- Edad / Dentición: {tipo_paciente}
- Biotipo facial: {biotipo} | Estado Periodontal/Colaboración: {estado_periodontal}
- Hábitos, Lengua y ATM: {', '.join(habitos_atm)}
- Clase Molar: Derecha = {c_molar_d} | Izquierda = {c_molar_i}
- Clase Canina: Derecha = {c_canina_d} | Izquierda = {c_canina_i}
- Etiología sagital: {origen_sagital} | Resalte (Overjet) inicial: {resalte_oj} mm
- Línea Media Superior: {lm_sup} | Línea Media Inferior: {lm_inf}
- Sobremordida (Overbite) inicial: {sobremordida_ob} mm ({problema_vertical})
- Situación Transversal: {problema_transversal}
- Espacio Superior: {apinamiento_sup} | Espacio Inferior: {apinamiento_inf}
- Inclinación incisiva inicial: {incisivos_inclinacion}
- Notas clínicas adicionales: {notas_clinicas_ini if notas_clinicas_ini else 'Ninguna'}

Estructura tu respuesta en estos 6 apartados:
1. **Producto Angel Aligner y Línea de Corte exacta:** (Elige entre Select 10/20/30/Unlimited, Pro 7+3 [recuerda no usar Pro en periodontales], o KiD K1/K2, y define la Línea de Corte: Festoneada, Recta alta a 2.5 mm o Mixta si están erupcionando incisivos).
2. **Estrategia Transversal y Forma de Arcada:** (Expansión unilateral del lado cruzado primero vs bilateral, arcada cuadrada en niños, espacio de primate de 0.5 mm en caninos temporales).
3. **Estrategia Sagital (Protocolos A6, A7 o A8):** (Los 5 pasos de Clase II, distalización secuencial A8 vs simultánea en niños, o Bloques A6 rectos 5+5 días cubriendo el 6 inferior con elásticos 1/4" 4.5 oz, o Angel Hook / AngelButtons en Clase III).
4. **Estrategia Vertical y Funcional:** (Levantes de mordida anteriores adaptativos de 3 a 3, inclinados si OJ<3mm, o posteriores sin cementar; aditamentos linguales en KiD; compensador de erupción en 7s o barras en caninos incluidos).
5. **Diseño de Ataches (incluyendo Atache DGZ), Áreas de Presión y Elásticos:** (Dónde colocar Atache DGZ M-gingival/S-incisal, HBO incisal para extrusión vs HBO en el centro + Torque Ridge para torque, ataches de retención en vecinos para intrusión o en 7 y 5 si hay botón directo en el 6, y elásticos diagonales/clase II/III).
6. **📝 TEXTO EXACTO PARA COPIAR Y PEGAR EN LA PRESCRIPCIÓN AL TÉCNICO DE iORTHO.**
Cita siempre entre paréntesis los nombres exactos de los archivos `.jpg` de la biblioteca gráfica para que se muestren debajo de tu respuesta.
"""
        with st.spinner("Generando prescripción clínica y cargando esquemas gráficos..."):
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
        "Sube las **capturas de pantalla o fotos de tu monitor en iOrtho** "
        "(**Tabla TM**, **Bolton**, **Anchura de la arcada**, **OB/OJ** y **MovE**). "
        "La IA leerá cada celda y la cruzará con el 'ladrillo' de Angel Aligner."
    )

    capturas_iortho = st.file_uploader(
        "📸 Arrastra aquí tus capturas de iOrtho (puedes seleccionar las 6 imágenes a la vez):",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

    imagenes_pil = []
    if capturas_iortho:
        cols_img = st.columns(min(len(capturas_iortho), 3))
        for i, archivo in enumerate(capturas_iortho):
            img_pil = Image.open(archivo)
            imagenes_pil.append(img_pil)
            with cols_img[i % 3]:
                st.image(img_pil, caption=archivo.name, use_container_width=True)

    observaciones_setup = st.text_area(
        "Observaciones adicionales sobre el Setup (opcional):",
        placeholder="Ej: Paciente adulto con ausencia del 42. Revisar rotaciones de caninos, colapso del 3-3 inferior y tiempos de IPR..."
    )

    incluir_diag_previo = st.checkbox(
        "Cruzar esta auditoría con el diagnóstico seleccionado en la Pestaña 1",
        value=True
    )

    if st.button("🔬 Auditar Capturas de iOrtho y Generar Modificaciones para el Técnico", type="primary"):
        contexto_diag = ""
        if incluir_diag_previo:
            contexto_diag = f"""
CONTEXTO DIAGNÓSTICO DEL PACIENTE (PESTAÑA 1):
- Edad/Dentición: {tipo_paciente} | Biotipo: {biotipo} | Periodonto: {estado_periodontal}
- Clase Molar D: {c_molar_d} | I: {c_molar_i} | Clase Canina D: {c_canina_d} | I: {c_canina_i}
- Resalte inicial: {resalte_oj} mm | Sobremordida inicial: {sobremordida_ob} mm ({problema_vertical})
- Transversal: {problema_transversal} | Notas: {notas_clinicas_ini}
"""
        prompt_fase2 = f"""
Actúa como auditor clínico experto en Angel Aligner (iOrtho). Analiza todas las cifras de las capturas adjuntas de iOrtho (Tabla TM de movimientos dentales, Análisis de Bolton, Anchura de la arcada, OB/OJ y gráfico MovE) junto con las notas del doctor.

{contexto_diag}
OBSERVACIONES DEL DOCTOR:
{observaciones_setup if observaciones_setup else 'Auditar todas las imágenes de iOrtho adjuntas.'}

Estructura tu auditoría en estos 6 bloques:
1. **Resumen de Datos Leídos en las Capturas de iOrtho:** (Bolton 3-3 y 6-6, ausencias dentarias detectadas con `—` o `X`, número de alineadores en MovE, etapas donde han puesto los rombos de IPR, Anchura 3-3/4-4/5-5/6-6 y OB/OJ inicial vs objetivo).
2. **Auditoría Diente por Diente de la Tabla TM (Alertas Amarillas y Riesgos Ocultos en Blanco):**
   - Lista con sus valores exactos los dientes que superen límites biomecánicos en Rotación (>12-15°), Torque (>8-10°), Tip/Angulación (>4°), Traslación V-L o M-D, y Extrusión/Intrusión.
3. **Análisis del Gráfico `MovE` (Secuenciación y Citas cada 6 alineadores):**
   - Evalúa si todos los dientes se mueven a la vez sin secuenciar y si los rombos de IPR están mal ubicados (recuerda la regla de David de programar el IPR al inicio o en las citas de los alineadores 7, 13, 19...).
4. **Análisis de Anchura de Arcada, Bolton y Sobremordida (OB/OJ):**
   - Alerta si hay colapso intercanino (`3-3` negativo) o aumento excesivo del Overbite final (~3 mm).
5. **Soluciones Biomecánicas Angel Aligner (Atache DGZ, HBO, Áreas de Presión, Levantes):**
   - Indica exactamente dónde colocar el **Atache DGZ** (talla M gingival y S incisal, recordando no ponerlo en incisivos inferiores sino en caninos/premolares/incisivos superiores), dónde poner **áreas de presión de rotación** (12-25°), **áreas de presión de torque + HBO en el centro de la corona**, o **ataches de rotación por vestibular + retención por palatino**.
6. **📝 TEXTO NUMERADO LISTO PARA COPIAR Y PEGAR AL TÉCNICO CAD DE iORTHO.**
Cita siempre entre paréntesis los nombres exactos de los archivos `.jpg` de la biblioteca gráfica (como `01_Atache_DGZ_Geometria_Vectores.jpg`, `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`, `13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`, etc.) para mostrar las referencias visuales.
"""
        with st.spinner("Leyendo capturas de iOrtho y auditando biomecánica diente por diente..."):
            try:
                contenido_envio = [prompt_fase2]
                if imagenes_pil:
                    contenido_envio.extend(imagenes_pil)
                respuesta_aud = modelo.generate_content(contenido_envio)
                st.session_state.ultima_auditoria = respuesta_aud.text
            except Exception as e:
                st.error(f"Detalle del error de conexión con Google Gemini: {e}")

    if st.session_state.ultima_auditoria:
        st.markdown("---")
        st.markdown("### 🔬 Informe de Auditoría Biomecánica y Modificaciones para iOrtho")
        st.markdown(st.session_state.ultima_auditoria)
        mostrar_fotos_referencia(st.session_state.ultima_auditoria)

# ==============================================================================
# PESTAÑA 3: CHAT CLÍNICO Y BUSCADOR DE REFERENCIAS VISUALES
# ==============================================================================
with tab_chat:
    st.subheader("💬 Chat Clínico y Buscador Visual del 'Ladrillo' Angel Aligner")
    st.caption(
        "Pregúntale por cualquier protocolo o pídele ver una referencia gráfica "
        "(ej. 'Enséñame la imagen de la forma y vectores del atache DGZ', 'Muéstrame la tabla de áreas de presión' o '¿Cómo configuro un avance mandibular A6?')."
    )

    for msg in st.session_state.chat_angel:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["texto"])
            if msg["rol"] == "assistant":
                mostrar_fotos_referencia(msg["texto"])

    pregunta_chat = st.chat_input("Ej: Muéstrame la imagen del atache DGZ y explícame cómo pedirlo...")

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
