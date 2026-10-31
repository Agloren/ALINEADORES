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

    # 2. Cuaderno Angel Academy (Detecta automáticamente la versión de 40 páginas o 49 páginas)
    if pdf_cuaderno and os.path.isfile(pdf_cuaderno):
        try:
            doc_c = fitz.open(pdf_cuaderno)
            total_pags = len(doc_c)
            doc_c.close()
        except Exception:
            total_pags = 40

        if total_pags <= 42:
            # Mapeo exacto para el PDF de 40 páginas
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
# (Integra Manuales, Artículos y Transcripciones de Crecimiento y Transversal)
# ==============================================================================
FRAMEWORK_BASE = """
Actúa como un Ortodoncista Senior y Director Clínico experto en el sistema Angel Aligner (plataforma iOrtho), entrenado estrictamente con los protocolos clínicos, artículos científicos, cuadernos y cursos monográficos (Pacientes en Crecimiento y Problemas Transversales) de los Dres. David González Zamora y Romina Vignolo Lobato (Angel Academy).

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
1. PORFOLIO DE PRODUCTOS, MATERIALES Y GESTIÓN DE CLÍNICA
====================================================================
- ACTIVACIÓN POR ETAPA: Los alineadores Angel Aligner tienen una magnitud de activación lineal entre **0.27 mm y 0.33 mm** por etapa.
- ANGEL ALIGNER SELECT (`22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg`): Fabricado con un solo material flexible multicapa `MasterControl S` (MCS: PET-G modificado + TPU). Fuerza constante (~1.31 N).
  * **Select 10:** Hasta 10 etapas, apiñamiento/espaciado <=2 mm, mejora de OB <=1 mm/arcada, rotaciones <=20°. No apto para extracciones ni A6. Incluye 1 refinamiento (10 etapas) y 1 juego de retenedores (1 año).
  * **Select 20:** Hasta 20 etapas, apiñamiento/espaciado <=5 mm/arcada, corrección AP <=2.5 mm, rotaciones <=40°, OB <=2.5 mm/arcada. Incluye 2 refinamientos y 2 juegos de retenedores (2 años).
  * **Select 30:** Hasta 30 etapas, corrección sagital <=4.5 mm, apiñamiento/espaciado <=10 mm/arcada, rotaciones <=60°, mejora vertical <=4.5 mm/arcada. Incluye 3 refinamientos de 30 etapas y 1 juego de retenedores (3 años).
  * **Select Unlimited:** Sin límite de alineadores ni refinamientos durante 5 años, 1 juego de retenedores, opción de Avance Mandibular A6.
- ANGEL ALIGNER PRO (`07_Material_Dual_MasterControl_S_Y_MC.jpg`, `23_Porfolio_Angel_Pro_7_Mas_3.jpg`):
  * **REGLA CLÍNICA:** **NO USARLO NUNCA EN PACIENTES PERIODONTALES**.
  * Sistema dual `7+3` en cada fase/etapa (2 alineadores por etapa):
    1) **7 días con `MasterControl S`** (multicapa flexible, inicia el movimiento con fuerza suave y continua sin deformarse tras las primeras 8 horas).
    2) **3 días con `MasterControl`** (TPU más grueso y rígido, actúa como el arco de acero en brackets para expresar al 100% el torque radicular, movimientos en masa, expansiones y rotaciones difíciles).
  * Incluye alineadores y refinamientos ilimitados durante 6 años y 3 juegos de retenedores (de 0.76 mm en TPU MasterControl).
- ANGEL ALIGNER KiD (K1 y K2) (`24_Protocolo_Angel_Kid_Notas_Romina.jpg` a `27_Tabla_Aditamentos_Angel_Kid.jpg`):
  * **Filosofía de tratamiento temprano (RNO) en 2 Fases:** A una persona que no ve bien a ningún médico se le ocurriría esperar a los 18-20 años para ponerle gafas. El tratamiento precoz decayó por artículos de *Evidence-Based Practice* centrados solo en el pico prepuberal, pero tratar desde la dentición temporal/mixta temprana (idealmente entre los 5 y 7 años cuando empiezan a erupcionar los 1º molares permanentes) equilibra el crecimiento tridimensional (músculo, hueso y diente, incluyendo la profundidad de arcada que un disyuntor clásico no trata).
  * **Diferencia entre el "K0" chino y el K1 europeo:** En China existía un "0" pasivo miofuncional sin movimiento dental porque a los técnicos les daba miedo expandir y distalar simultáneamente; gracias a los protocolos enviados por David y Romina a Vicky (ortodoncista jefa en Wuxi/Shanghái, donde trabajan con estructura jerárquica de Ortodoncista -> Técnico Senior -> Técnico Junior), en Europa el **K1** integra tanto la ortopedia miofuncional como el movimiento dental complejo en 3D.
  * **Ventaja única:** Permite tratar en **dentición de leche pura**, sin exigir que estén erupcionados ni el primer molar definitivo (6) ni ningún incisivo permanente.
  * **Truco económico y clínico:** Si al paciente le queda aunque sea **un solo diente de leche**, escanear y empezar como caso **KiD (K1)**.
  * **K1:** Dura **2 años (24 meses)** con alineadores y refinamientos ilimitados (ampliaron 6 meses la garantía porque con 1 año en pleno recambio dentario te quedabas corto al escanear cada caída de diente). Desde el 1 de abril de 2025 el avance mandibular A6 y todos los aditamentos miofuncionales vienen incluidos de serie en el precio del K1. Conviene "estirar el chicle" y resolver todo lo posible dentro de los 2 años del K1.
  * **K2:** Segunda fase para dentición definitiva (exclusiva para pacientes que hicieron un K1 previo; dan una **ventana de 10 años** para pasar de K1 a K2). Funcionalmente **el K2 es un Select Unlimited tal cual** (5 años de tratamientos/refinamientos ilimitados + 1 juego de retenedores) a precio muy reducido. En adolescentes en crecimiento que no vienen de un K1, elegir directamente Select o Pro según la complejidad.
- GESTIÓN DE CITAS Y ESCANEADO EN REFINAMIENTOS (`05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`):
  * David ve a los pacientes cada **2 meses**, entregando **6 alineadores por tanda**; por tanto, pide al técnico programar el IPR y acciones clínicas en los alineadores **7, 13, 19...**
  * **Escaneado con ataches puestos:** Para los refinamientos, tomar el escáner intraoral con los ataches puestos y evaluar después cuáles se quedan y cuáles se quitan.
  * **El "Punto Rojo" en iOrtho:** Cuando en el software ves un **punto rojo** sobre un diente en un refinamiento, significa que tienes que quitar ese atache antiguo y cementar uno nuevo (evita tener que buscar las 7 diferencias etapa por etapa). **Ojo clínico:** si ves un punto rojo y por vestibular no ves atache, **mira siempre por palatino/lingual**, para que la higienista no meta el alineador nuevo encima de un atache o botón palatino antiguo sin quitarlo.
  * **Vigilancia al caer un molar temporal y salir el premolar:** Cuando se cae el molar de leche y erupciona el premolar en el hueco bajo el alineador, vigilar estrechamente que el premolar no se sobreextruya o invada el hueco desajustando la férula.

====================================================================
2. LÍNEA DE CORTE VARIABLE Y EL "KIT DE SUPERVIVENCIA" (`09_Lineas_De_Corte_Variable_3_Tipos.jpg`)
====================================================================
1) **Línea de corte festoneada a nivel gingival (0 mm):** Más estética, indicada en pacientes periodontales o con recesiones.
2) **Línea de corte recta alta (+2.5 mm por encima del margen gingival):**
   * Da muchísimo más plástico haciendo empuje y retención. **Imprescindible en expansiones, distalizaciones, uso de máscara facial y aparatos funcionales (A6 / Clase II / Clase III)** (en niños con máscara o A6, Romina pide 100% línea de corte alta completa).
   * **Regulación de ataches con línea alta:** Si pides línea de corte alta, debes **reducir/regular la retención de los ataches**; si dejas los mismos ataches ultrarretentivos con línea alta, el alineador entra pero el paciente no puede sacárselo.
   * **En adultos:** A David no le gusta mantener la línea de corte alta más de **20 alineadores seguidos** en adultos. En sobremordidas donde se combine rampa anterior + expansión + *torque ridge* + atache de extrusión anterior, no poner la línea de corte alta al principio sino más adelante.
   * **Dónde molesta realmente y el "Kit de Supervivencia" (Dra. Romina Vignolo):** Donde más molesta la línea de corte alta no es arriba, sino **abajo por lingual** (en la zona de prominencia alveolar o torus mandibular). Romina entrega a los pacientes un *"kit de supervivencia"* (tijerita de cortar uñas de punta fina, lima y ganchos extractores extra) para que recorten un filete mínimo del borde superior donde roce. Además, a muchas pacientes adultas les gusta más la línea alta porque al sonreír no se ve la raya del plástico sobre el diente.
3) **Línea de corte mixta (Festoneada en sector anterior + Recta alta a 2.5 mm en sector posterior):**
   * **En niños en recambio incisivo:** Cuando están erupcionando los incisivos centrales o laterales, el volumen de la encía anterior engorda y cambia constantemente (algo imposible de calcular por el software). Pedir **línea mixta** evita roces e interferencias gingivales en el sector anterior mientras mantiene toda la fuerza expansiva y retentiva de la línea alta en los molares de leche posteriores.
   * **En adultos:** Ideal en fases largas de expansión cuando no se necesita un control crítico de torque en los incisivos anteriores.

====================================================================
3. BIOMECÁNICA PROFUNDA DE ATACHES, ATACHE DGZ, ÁREAS DE PRESIÓN Y AUXILIARES
====================================================================
A) FÍSICA DE LOS ATACHES ANGEL ALIGNER Y POR QUÉ VAN "AL REVÉS" QUE INVISALIGN/SPARK (`11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Regla de oro en movimientos difíciles y en Expansiones:** Una expansión sin control provoca proinclinación de las coronas y pérdida de torque -> genera interferencias cuspídeas -> abre la mordida y crea un problema vertical y sagital. Por tanto, en toda expansión y movimiento difícil hacen falta buenos ataches (rectangulares o de retención) para dar **control radículo-vestibular** y evitar que el diente se escape del plástico.
- **Pop-up 3D y Tallas en iOrtho:** Pulsando doble clic sobre un atache en iOrtho aparece el *pop-up* (con controles circunferenciales para rotación y lineales para extrusión) para modificar posición y perfil. En el atache de retención hay tallas S y M; en los rectangulares hay XS, S, M, L, M+, L+ (uno indica el ancho y otro el alto). En *Preferencias Clínicas* se puede pedir que pongan por defecto el atache más grande posible.
- **Ataches en Niños ("Ladrillos" y Ataches de Colores):** Los niños se ponen los alineadores **mordiéndolos** en vez de insertarlos con los dedos; si pones un atache pequeño en un molar o canino de leche (que son cortos y expulsivos), el plástico entra mal y se desadapta. Romina pide **ataches enormes ("ladrillos") en niños** y utiliza **composites fluidos de colores con carga** (ej. *Voco Twinky Star*: morado, verde, amarillo, rosa, azul, naranja) en los dientes posteriores (acordándolo antes con los padres y dejando blancos los anteriores). Así los niños se motivan y se ve fácilmente si se desgasta algún fragmento del atache.
- **¡ATENCIÓN! Por qué los ataches de Rotación y de Extrusión (HBO) tienen el bisel "al revés" que Invisalign/Spark (NO darles la vuelta):**
  * Cuando David y Romina empezaron con Angel Aligner les daban la vuelta a todos los ataches pensando que venían mal puestos, hasta que estudiaron su física: en Invisalign y Spark la cara activa es la superficie larga; **en Angel Aligner la cara activa es el bisel más corto/estrecho** (el más perpendicular).
  * **Física del Atache de Rotación:** En un diente redondo (canino/premolar) necesitamos una superficie plana lejos del centro de resistencia para crear una **cupla** (momento de rotación pura sin desplazamiento, donde Momento = Fuerza x Distancia). En el diseño de Angel Aligner, la inclinación del bisel corto hace que la línea de acción genere un brazo de palanca mucho mayor y un contramomento menor que el de Invisalign/Spark. Además, tiene **dos superficies activas en un solo atache**: una corrige la rotación y la otra sirve para retención (si está hacia gingival) o intrusión (si está hacia incisal).
  * **Física del Atache de Extrusión (HBA / HBO):** Un incisivo no es retentivo (tiene forma de cuña convergente hacia incisal). Con el bisel largo clásico, por la 3ª Ley de Newton (acción-reacción), al empujar sobre la pendiente vestibular se produce un contramomento ("efecto cáliz/cuña") que **intruye** el incisivo en lugar de extruirlo. El bisel corto activo de Angel Aligner abraza el atache y descompone el vector de fuerzas logrando un **componente vertical muchísimo mayor que el horizontal**.
  * **Doble posición del Atache HBO en la corona clínica:**
    1) Si quieres **EXTRUSIÓN**: tiene que estar colocado muy **en el tercio incisal** (como sale por defecto) para que el contramomento sea mínimo.
    2) Si quieres **CONTROL DE TORQUE**: tienes que **subirlo al CENTRO de la corona clínica** (combinado con *torque ridge* y línea de corte alta).
  * **Truco de David para extruir incisivos inferiores:** Como la anchura mesiodistal del incisivo inferior es diminuta, el **atache convencional de retención** funciona fenomenal para extruirlos (o intruirlos) porque la inclinación de su superficie activa gingival es casi perpendicular.
  * **La doble cara de la moneda (Colaboración):** Como la superficie activa de los ataches de Angel es más perpendicular y efectiva, si el paciente **no es colaborador** y el alineador desajusta un poco, pierde el enganche enseguida y toca parar, reescanear y pedir otro caso. Vigilar el ajuste en cada visita.
  * **Manejo de interferencias oclusales con ataches:** Si un atache choca al morder, poner un levante de mordida sin cementar solo protege mientras lleva el alineador puesto, pero cuando el paciente se lo quita para comer chocará igual y despegará el atache; por tanto, si hay interferencia, bajar/empequeñecer el atache o reubicarlo en la corona para que libre la oclusión.
- **Atache de Rotación + Extrusión / Retención en Premolares y Caninos:** Hacer primero la rotación y luego la extrusión; colocar atache de rotación por vestibular y atache de retención por palatino. Asegura que el alineador esté encajado y no pierda el control durante el giro.

B) ATACHE DGZ ("Double Gripping Zag Attachment" — Zamora & Vignolo, 2025) (`01_Atache_DGZ_Geometria_Vectores.jpg`, `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`, `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`, `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`, `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Origen y problema que resuelve (MARPE y Canino Inferior en Extracciones/Clase III):**
  * En disyunciones de adultos con **MARPE**, no solo resiste la sutura palatina media sino sobre todo la **articulación pterigomaxilar**, haciendo que la disyunción se abra en abanico (arco en V con un gran diastema anterior). Al cerrar ese diastema con alineadores convencionales, las coronas se inclinan dejando las raíces en "tienda de campaña". Igualmente, en extracciones de premolares o Clases III, mover la raíz del **canino inferior** (la raíz más larga en la cortical más dura) es una pesadilla.
  * El atache clásico de doble tip de Invisalign falla porque sus dos lóbulos están muy juntos (d = 4 mm), no tienen retención, solo juega con la anchura del diente y **ambos vectores de fuerza pasan por el mismo lado (incisal) del Centro de Resistencia (CR)**, exigiendo fuerzas altas (0.50 N) que desadaptan el plástico.
- **Diseño biomecánico del Atache DGZ:** David rotó 90° cada lóbulo y aprovechó tanto la anchura mesiodistal como la altura incisogingival de la corona (dejando 1 mm de margen en los 4 bordes):
  * **Lóbulo Gingival (Talla M):** Colocado en mesial-gingival (a 1 mm de la encía), aplica una fuerza vertical hacia incisal (F1) y además asegura una **gran retención cervical**.
  * **Lóbulo Incisal (Talla S):** Colocado en el extremo opuesto distal-incisal (a 1 mm del borde incisal), aplica una fuerza vertical opuesta hacia gingival (F2).
  * **Ventaja física exacta:** La distancia diagonal entre ambos lóbulos sube a **d = 10.7 mm** y los dos vectores de fuerza pasan **a un lado y a otro (mesial y distal) del Centro de Resistencia**, exactamente igual que cuando un bracket endereza una raíz con un arco 0.012. Para lograr el momento de 2 N·mm (1° de tip) solo necesita **0.19 N** de fuerza (menos de la mitad que el doble tip clásico), logrando movimiento radicular puro sin traslación indeseada.
- **Indicaciones del Atache DGZ (pedirlo siempre en lugar del doble tip o rectangular):**
  1) Cierre de diastemas interincisivos post-MARPE (evita poner *power arms*).
  2) Control de tip radicular en caninos (especialmente el canino inferior en Clase III o extracciones), premolares y molares.
  3) Enderezamiento de molares inclinados (*molar straightening*).
  * **Limitación anatómica:** No cabe en **incisivos inferiores** por su reducido ancho y alto coronal (en molares grandes en casos de extracción A7 también se pueden usar dos ataches rectangulares verticales).

C) ÁREAS DE PRESIÓN, RECORTES Y COMPENSADORES DE ERUPCIÓN (`13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`, `14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg`):
- **Área de presión de torque (Torque Ridge):** En incisivos y caninos para torque radiculolingual; lleva HBO en el centro del diente y línea de corte alta.
- **Área de presión de intrusión:** En incisivos para intrusiones **> 2.5 mm** (acompañar siempre de ataches de retención en dientes vecinos, ej. en 12 y 13 para intruir 11 y 21).
- **Área de presión de rotación (Crestas de rotación):** En incisivos y caninos para rotaciones entre **12° y 25°** (velocidad máxima: **Pro = 2.2°/etapa**, **Select = 1.8°/etapa**). En incisivos van en par (bucal y palatino) o solo en palatino si hay atache vestibular (bajo solicitud manual pueden ir en la misma cara dejando >=1 mm de separación).
- **Recorte para bracket/tubo:** Para usar arcos seccionales cuando queremos mesializar molares.
- **Compensadores de erupción Activos vs. Pasivos (con CBCT):**
  * En otras marcas el compensador siempre se coloca de forma pasiva en la línea de la arcada. En Angel Aligner, si envías el **CBCT**, puedes pedir al técnico que coloque el compensador **donde esté realmente el diente ectópico/palatinizado** y hacerlo **ACTIVO**: el compensador va empujando y acompañando poco a poco al diente hacia la arcada conforme erupciona, e incluso permite hacerle un recorte para botón en el propio compensador.
  * **Momento de colocar el Tongue Crib ("el pinchito") en recambio incisivo:** Si los incisivos definitivos apenas han asomado en un niño con mordida abierta por interposición lingual, Romina prefiere esperar un par de meses a que erupcionen un poco más antes de escanear (en lugar de llenarlo de compensadores), porque así ya se pueden cementar buenos ataches de retención en los incisivos y el software ya deja colocar el *Tongue Crib* ("pinchito" lingual).
  * En casos de **caninos incluidos quirúrgicos**: suturar el cemento quirúrgico tras la exposición para dejar abierto el acceso al diente, pedir muchos alineadores pasivos y colocar **barras de refuerzo** en lugar de compensadores grandes para evitar interferencias.

D) LEVANTES DE MORDIDA: ANTERIORES, INCLINADOS, CLASE III Y "BITE BUBBLES" POSTERIORES (`15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg`):
- **Diseños de levantes anteriores:**
  * *Rectangulares/Cuadrados:* No son adaptativos; solo se piden si el doctor quiere rellenarlos/cementarlos con composite en boca.
  * *Curvos/Redondeados (Adaptativos):* Cambian automáticamente su angulación con el diente según se corrige la maloclusión. **David y Romina NUNCA rellenan los levantes de composite**. En pacientes con sobremordida, su estándar es poner **levantes anteriores adaptativos de 3 a 3 desde el primer día**.
  * *Levante anterior inclinado (exclusivo Angel):* Tiene rampa con pendiente (como una pista anterior de Planas) que obliga a la mandíbula a ir hacia adelante en Clases II con resalte < 3 mm o en la Fase II de estabilización tras retirar los bloques A6.
  * **¡REGLA DE ORO ANTES DE APROBAR UN LEVANTE ANTERIOR EN EL SETUP!:** Comprobar que el paciente tiene un resalte suficientemente corto para ocluir sobre el levante y que **en relación céntrica NO sea capaz de quedarse atrapado por detrás del levante** (David lo vivió con una paciente y es un desastre clínico porque le empotra la mandíbula hacia atrás). Si tiene demasiado resalte inicial, pedir al técnico que coloque el levante anterior **a partir de la etapa X**, cuando ya se haya reducido parte del resalte con elásticos.
  * *Levantes anteriores adaptativos en Clase III (salto de mordida cruzada anterior):* En Clases III compensables donde hay que saltar la mordida anterior con elásticos, Angel dispone de levantes anteriores adaptativos que van subiendo hacia el borde incisal hasta que salta la mordida. **Nunca poner levantes posteriores en una Clase III donde quieras aplanar la curva de Spee**, porque intruirán los molares posteriores (y más aún con el material rígido del Pro) dejando una mordida abierta posterior que cuesta meses revertir.
- **Levantes Posteriores ("Bite Bubbles" / Cabezas de champiñón) y la Filosofía Postural de Romina en Pacientes Verticales/Dolicofaciales:**
  * Se piden siempre al técnico (no tienen pop-up manual) y **jamás se rellenan de composite**.
  * *En adultos / mordidas cruzadas:* Ponerlos solo durante las etapas estrictamente necesarias para desocluir y descruzar, retirándolos enseguida para no intruir molares ni abrir la mordida posterior (especialmente en Pro).
  * *En niños verticales / mordida abierta anterior (Protocolo Dra. Romina Vignolo):* Posturológicamente, en un paciente vertical es un sacrilegio aumentar pasivamente la dimensión vertical con un bloque rígido porque aumenta el tono muscular posterior y lo hace aún más inestable. Lo que hay que cambiar es el **engrama muscular** activando los maseteros: Romina coloca los *bite bubbles* huecos y **le pide al niño que los apriete todos los días hasta chafarlos**; a la semana siguiente cambia de alineador, tiene una burbuja nueva y vuelve a apretarla, entrenando la musculatura masticatoria.
  * **El "Salto Virtual Vertical" en el Setup de Mordida Abierta:** Para que el técnico no cierre la mordida abierta extruyendo incisivos artificialmente, Romina pide **nivelar el plano oclusal superior y nivelar el plano oclusal inferior de forma independiente, solicitando un "salto virtual vertical"** que simule la anterorrotación natural en bisagra de la mandíbula al corregir los planos.

E) ANGELBUTTON™ Y ANGEL HOOK: BIOMECÁNICA Y PELIGRO DE SOBRECORRECCIÓN (`16_Detalle_Clinico_AngelButton_TAD.jpg` a `19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`):
- **Diferencia física entre AngelButton y Botón Cementado al Diente:**
  * El **AngelButton** es del mismo TPU rígido del Pro y soporta **500 g**. Al tirar de un AngelButton, **toda la fuerza se reparte en bloque por toda la arcada** a través del plástico. En cambio, al tirar de un botón cementado directo al diente, la fuerza se disipa en la raíz de ese diente (tiende a extruirlo/inclinarse) y apenas se transmite a los vecinos por los puntos de contacto.
  * En un paciente braquifacial de Clase II donde queremos abrir la mordida extruyendo el molar inferior: combinamos **AngelButton en el canino superior** (frena y distaliza toda la arcada superior en bloque) con **recorte para botón cementado directo en el 6 inferior** (para que el elástico extruya el molar inferior), poniendo siempre **ataches de retención en el 7 y en el 5 inferiores**.
- **¡ALERTA CLÍNICA CON LOS ELÁSTICOS EN ANGELBUTTONS!:** Como el AngelButton transmite la fuerza a toda la arcada de forma tan eficiente y vemos al paciente cada 2 meses, si el paciente usa los elásticos todo el día **los casos de Clase II se pasan a Clase III quirúrgicas y las Clases III se pasan a Clase II** con suma facilidad. Es obligatorio sacar fotos y supervisar la oclusión en cada cita (y no delegarlo sin control) para parar o invertir la goma a tiempo.
- **Truco si salta el elástico en vectores hacia adelante (Máscara Facial / Clase III):** El AngelButton tiene algo menos de retención si tiras con un vector muy horizontal hacia adelante entre lateral y canino; para que no salte la goma, **cruzar el elástico de un punto a otro** o pedir el **Angel Hook**.
- **Mecánicas combinadas (Distalización + Tracción de canino alto con AngelButton):** El alineador abre el espacio mientras el elástico extruye el canino y asienta el plástico; pero **no pidas el AngelButton en las primeras etapas si aún no vas a enganchar el elástico** hasta que se abra hueco, porque los "cuernitos" vacíos sin elástico rozan y molestan al paciente.
- **Regla obligatoria en Mordida Cruzada con AngelButton:** Siempre que se usen AngelButtons para elásticos cruzados (o en la arcada inferior por lingual), colocar **atache en palatino/vestibular opuesto para retención**, evitando que el elástico desinserte el alineador.

====================================================================
4. PROTOCOLOS ESPECÍFICOS DE CRECIMIENTO, TRANSVERSAL, CLASE II Y CLASE III
====================================================================
A) ETIOLOGÍA POSTURAL, PODAL, FUNCIONAL Y TRATAMIENTO DE LAS MORDIDAS CRUZADAS (RNO / LEYES DE PLANAS) (`24_Protocolo_Angel_Kid_Notas_Romina.jpg`, `26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg`):
- **Factores etiológicos y posturales desde el nacimiento:**
  1) *Tortícolis congénita o plagiocefalia:* Partos instrumentales con fórceps o ventosa que contracturan el esternocleidomastoideo (ECM) de un lado, inclinando la cabeza y desviando la mandíbula hacia ese lado.
  2) *Falta de gateo y cadenas musculares:* Al no dormir boca abajo, muchos bebés no activan el reflejo de extensión cervical ni hacen gateo cruzado ("gatean con el culete" o pasan directo a ponerse de pie). El gateo cruzado es el que activa las cadenas cruzadas anteriores (*core*); sin él, quedan con hipertono de la cadena posterior.
     - *Correlaciones posturales y podales:* Hiperextensión de rodillas + pies planos + cabeza adelantada tiende a **Clase II**; hiperlordosis + rodillas flexionadas + pies cavos tiende a **Clase III**. Un pie plano aumentado se correlaciona con dimensión vertical bucal aumentada; el **retropié valgo** (hacia adentro, cadena de cierre) disminuye la dimensión vertical bucal y simula una **falsa pierna corta** de ese lado, mientras que el **retropié varo** (cadena de apertura) la aumenta.
     - *Test de los rollitos de algodón (Meersseman):* Permite comprobar cómo al desprogramar la oclusión se centra el tono postural y se rectifica la lordosis/escoliosis cervical cuando la boca es el captor descendente.
  3) *Dormir boca abajo o sobre la mano/hombro (90% de la población):* Meter el hombro o la mano debajo de la cara al dormir comprime el maxilar de ese lado y acorta la musculatura homolateral, atrayendo la mandíbula y el hueso hioides hacia ese lado. El verdadero lado preferente de dormir de un niño es **el lado en el que lo encuentras durmiendo por la mañana al ir a despertarlo**.
     - *Truco clínico de Romina para cambiar el lado de dormir en niños:* Los niños duermen mirando hacia lo que les da seguridad (los padres, la puerta, la ventana o su hermano). **Pon la almohada a los pies de la cama** (o gira la cuna en bebés; si son dos hermanos que duermen mirándose, pon las dos almohadas a los pies de ambas camas) para que sigan mirando hacia su zona de confort pero apoyando el lado contrario de la cara.
  4) *Respiración oral y alerta sobre los "Tapes" (esparadrapos bucales):* Antes de mandar esparadrapo bucal nocturno, verifica con el ORL que el paciente tiene **paso de aire nasal real** (cuidado con los cornetes hipertróficos aunque en la telerradiografía se vea buena vía aérea faríngea posterior); tapar la boca sin paso nasal real provoca apneas infantiles y de adulto.
- **Por qué no se cumple la 1ª Ley de Planas en las Mordidas Cruzadas y la Lengua Torsional:**
  * En un niño muy pequeño la mordida cruzada empieza por una prematuridad dental (si aún muerde indistintamente a derecha e izquierda, basta un **tallado selectivo**). Una vez instaurada, a diferencia de una boca normal donde el maxilar se expande hacia el lado de trabajo, en la **mordida cruzada** el maxilar superior queda atrapado por dentro del inferior y trabaja al revés: **el lado de mínima dimensión vertical (lado cruzado/de trabajo) se queda comprimido en el maxilar** (signo patognomónico en la panorámica), con un cóndilo más redondeado, rama más corta y movimiento puramente de rotación con trayectoria condílea muy vertical (tendencia a Clase II); mientras que el lado de balanceo tiene el cóndilo más alargado, rama más larga y movimiento de rotación+traslación (tendencia a Clase I/III). (Un diente incluido unilateral actúa posturalmente casi como una agenesia comprimiendo ese lado).
  * **Volumetría torsional de la lengua:** En una mordida cruzada unilateral la lengua es asimétrica en 3D: en el lado de masticación es **ancha y baja**, y en el lado de balanceo es **estrecha y alargada**. Si no se rehabilita posicional y tridimensionalmente con logopeda y posicionador lingual (quitándose el alineador en el logopeda para ejercitar y poniéndoselo después como estímulo), la lengua provocará recidiva.
- **Protocolo de Expansión Asimétrica en Mordida Cruzada Unilateral (Zamora & Vignolo):**
  * **ERROR A EVITAR:** Nunca sobreexpandir primero el lado sano para hacer anclaje recíproco, porque dejas al niño durante meses sin contacto oclusal ni por la derecha ni por la izquierda y no puede comer.
  * **SECUENCIA CORRECTA EN 2 ETAPAS:**
    1) **Etapa 1 (Simetrizar):** Pedir al técnico **expansión unilateral exclusiva del lado comprimido** hasta dejarlo totalmente simétrico con el lado contralateral sano (podemos ayudarnos poniendo 1 AngelButton por palatino y 2 por vestibular con ataches de retención).
    2) **Etapa 2 (Expansión bilateral, Arcada Cuadrada y Líneas Medias 100% Centradas):** Una vez que ambas hemiarcadas son simétricas, continuar con **expansión bilateral simétrica** dándole una **forma de arcada cuadrada** para permitir el frote oclusal bilateral. En niños es innegociable terminar con **molares y caninos a la misma altura y las líneas medias superior e inferior centradas respecto a su base ósea y entre sí** (una línea media desviada en un niño significa que mantiene dos trayectorias condíleas distintas y recidivará).
    3) **Rehabilitación masticatoria de 2 años:** Pedir activamente al paciente que **coma por el lado contrario al que comía (el lado no cruzado) durante aproximadamente 2 años**, que es el tiempo biológico que tarda en remodelarse por completo la trayectoria condílea (controlando FMA y ángulos goniacos), antes de pasar a una masticación bilateral alternante.

B) DISCREPANCIA ÓSEO-DENTARIA EN DENTICIÓN MIXTA: "EXPANSIÓN CENTRÍFUGA" (SUSTITUTO DEL 2x4 / D-GAINER) (`24_Protocolo_Angel_Kid_Notas_Romina.jpg`):
- **Ventaja frente al clásico 2x4 / D-Gainer / Utilitario:** El 2x4 solo expandía y distalaba el primer molar y proinclinaba los incisivos (perdiendo el control de torque), dejando los 3 dientes intermedios de cada cuadrante (canino y molares de leche) sin desarrollar transversalmente. Con alineadores logramos un desarrollo tridimensional completo ("expansión centrífuga": **distalar + expandir + protruir simultáneamente** con control de torque y levante anterior) en unos 26 alineadores (~6.5 meses).
- **Secuencia biomecánica exacta en dentición mixta:**
  1) **Expandir y distalar los primeros molares (6s) a la vez** (combinado con levante de mordida anterior si hay sobremordida).
     - *Regla de oro de coordinación sagital al distalar arriba y abajo:* Si el lado está en **Clase I**, la distalización del molar superior e inferior tiene que ir **acompasada a la par** (el molar inferior nunca puede ganarle la posición al superior para no crear una interferencia y perder el anclaje). Si el lado está en **Clase II**, empezar distalando primero el molar superior y, cuando ya alcance relación de Clase I con el inferior, distalar los dos juntos en Clase I.
  2) **Una vez distalado el 6, distalar y expandir los molares de leche.**
     - *Seguridad radicular:* Distalar molares de leche NO daña ni deforma los gérmenes de los premolares definitivos (las raíces temporales acompañan y reconducen favorablemente la erupción del premolar) ni impacta los segundos molares (los 7s están en un plano más hacia vestibular y erupcionan sin problema, a diferencia de las antiguas bandas molares que sí los atascaban).
  3) **Ordenar el apiñamiento incisivo anterior dejando SIEMPRE 0.5 mm de espacio en mesial y 0.5 mm en distal de los caninos de leche (Espacio de Primate):** Incluir siempre esta instrucción en la prescripción inicial para dejar la arcada preparada para el recambio.

C) AVANCE MANDIBULAR CON PROTOCOLO A6 EN CLASE II (`20_Protocolo_A6_Reglas_Avance_Mandibular.jpg`, `21_Figura_6_Avance_Mandibular_A6_Bloques.jpg`, `33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg`, `35_Opciones_Elasticos_Clase_II_Con_A6.jpg`):
- **Ventana ideal:** Primer pico de crecimiento entre los **5 y 7 años** (segunda infancia, cuando empiezan a salir los 6s, maduración vertebral fin de C1 a fin de C2) o en el estirón prepuberal (CS3-CS4). Permite expandir de forma simétrica ("efecto Planas"), nivelar e impulsar el crecimiento de la rama mandibular todo a la vez.
- **Por qué el avance debe ser de al menos 4 mm y NO a micro-saltitos:** En las aletas clásicas de otras marcas se hacía avance incremental en micro-saltitos porque las aletas eran bajas; pero si no aumentas lo suficiente la separación vertical entre arcadas, **no permites que el cóndilo se separe de la cavidad glenoidea** y la rama mandibular no crece (solo haces una reposición funcional).
  * **Regla de magnitud del salto en A6:** Máximo **7 mm**. Si en un niño muy pequeño (5-6 años) con casi 10 mm de resalte no quieres hacer los 7 mm de golpe porque no sabe posicionarse y aplasta el bloque, **dividir el salto en DOS partes grandes (nunca en micro-saltitos): hacer como mínimo 4 mm en el primer salto** (altura mínima para desalojar el cóndilo de la cavidad glenoidea) y luego una segunda fase con lo que falte.
- **¡REGLA CRÍTICA DE DISEÑO: SIEMPRE BLOQUES TIPO 1 (RECTOS) Y PROHIBIDO EL TIPO 2 (INCLINADO)!:**
  * Jamás elegir el bloque inclinado (Tipo 2): su superficie de apoyo es demasiado pequeña, cuando el niño relaja la musculatura se queda enganchado por detrás del pico y muerde mucho peor que al principio.
  * Pedir **SIEMPRE el Bloque Tipo 1 (más rectangular/recto, tipo Twin-Block)** acompañado **sí o sí de AngelButtons** para poner un **elástico suave de posicionamiento** (por la noche en ambos lados, y **también por la tarde en el lado que tenga más Clase II si es asimétrica** para estimular el estiramiento del lado corto).
- **¡REGLA CRÍTICA DE POSICIÓN: EL BLOQUE SUPERIOR DEBE CUBRIR COMO MÍNIMO EL PRIMER MOLAR INFERIOR DEFINITIVO (6)!:**
  * En los pacientes de Clase II la curva de Spee está aumentada porque el incisivo inferior se ha extruido al no tener contacto anterior, no porque el molar esté intruido. Si dejas el bloque A6 en la zona media (como lo pone el software casi por defecto), el bloque presiona e **intruye los molares posteriores**, impidiendo además que los incisivos anteriores se intruyan y dejando una **mordida abierta posterior enorme**.
  * **Instrucción obligatoria al técnico CAD:** Escribir al técnico hasta que haga caso que *"en dentición mixta el bloque A6 Tipo 1 debe ir lo más posterior posible y el bloque superior tiene que cubrir como mínimo el primer molar inferior definitivo (6)"*. (En adolescentes donde ya se perdió el pico de crecimiento y sí se busque extruir el molar inferior, se puede poner un botón cementado directo al 6 inferior con ataches de retención en 7 y 5).
- **Las 2 Fases de todo Avance A6 (Consolidación de 9 meses):**
  * En 20 alineadores no llegas a los **9 meses** necesarios para que el cambio muscular pase a ser remodelado esquelético. Por tanto, tras la **Fase I (activa con los bloques A6, usando dos juegos de material flexible por etapa: 5 días + 5 días)**, hay que hacer siempre una **Fase II de mantenimiento/estabilización** colocando **levantes de mordida anteriores inclinados** + elásticos nocturnos de Clase II mientras se gana profundidad de arcada (distalizando/recambiando).

D) CLASE III EN CRECIMIENTO Y EN ADULTOS (`19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`, `36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg`, `37_Caso_Clase_III_Pro_Evolucion_Intraoral.jpg`):
- **En niños con Clase III (Máscara Facial):** La tracción anterior con máscara facial sobre alineadores con **línea de corte alta (2.5 mm)** y **AngelButtons / Angel Hook** funciona de forma espectacular en 4 meses, permitiendo combinar al mismo tiempo la corrección de una mordida cruzada unilateral (expandiendo primero el lado comprimido).
- **En adultos jóvenes (Compensación con Angel Aligner Pro y Protocolo A8):** Distalización secuencial de los cuadrantes 3 y 4 (protocolo A8), intrusión anteroinferior para aplanar curva de Spee, uso de **Atache DGZ** o doble tip en caninos inferiores (33 y 43) controlando con el CBCT (IRS) que sus raíces entren en el hueso cortical, IPR anterior según Bolton y **elásticos de Clase III (3/16", 4.5 oz) de AngelButton a AngelButton**.

====================================================================
5. REGLAS DE AUDITORÍA DE CAPTURAS DE iORTHO (TABLA TM, BOLTON, OB/OJ, ARCADA, MovE)
====================================================================
Al auditar las capturas de pantalla de iOrtho subidas por el doctor:
1) **Bolton:** Identificar si el exceso (ej. 3-3 o 6-6) se debe a ausencias dentarias (`—` en la tabla M-D, como falta del 42, 17, 37) o desproporción anatómica, y proponer cómo compensarlo (IPR, reconstrucción o cierre con Atache DGZ).
2) **Gráfico MovE (Secuenciación):** Verificar número de etapas activas, ausencias (`X`), cementado de ataches (puntos rojos, recordando mirar siempre por palatino/lingual) y etapas de IPR (rombos azules). Si todos los dientes se mueven en bloque de la etapa 1 a la final en un adulto, exigir secuenciación (ej. patrón en V en distalizaciones o desrotar/expandir antes de retruir) y **adelantar el IPR a las primeras etapas o a las citas de los alineadores 7, 13, 19...**
3) **Tabla TM (Corona, Centro de resistencia y Ápice radicular):**
   - Detectar todas las celdas marcadas en amarillo/rojo Y las celdas en blanco que superen límites predecibles:
     * **Rotaciones >15° en caninos/premolares o >20° en incisivos:** exigir atache de rotación (recordando que en Angel el bisel corto es el activo y no hay que girarlo, o rotación vestibular + retención palatina), área de presión de rotación (en incisivos/caninos entre 12° y 25° respetando velocidad máx 2.2°/etapa en Pro o 1.8°/etapa en Select) y abrir espacio previo.
     * **Tip / Angulación >4-5° o cierre de espacios de extracción/agenesia/MARPE:** exigir **Atache DGZ (talla M en gingival y S en incisal)**, salvo en incisivos inferiores donde no cabe por tamaño.
     * **Torque >8-10° (`La`/`Li`):** exigir área de presión de torque (*torque ridge*) + **atache HBO subido al CENTRO de la corona clínica** + línea de corte alta a 2.5 mm.
     * **Extrusión (`E`) vs Intrusión (`I`):** Para extrusión en incisivos superiores poner HBO en el tercio incisal; en incisivos inferiores usar el atache convencional de retención. Para intrusión poner ataches de retención en dientes vecinos (ej. en 12 y 13 para intruir 11 y 21) y área de presión de intrusión si supera 2.5 mm.
4) **Anchura de la Arcada (`3-3`, `4-4`, `5-5`, `6-6`):** Alertar si hay estrechamiento/colapso severo de la distancia intercanina (`3-3` muy negativo, ej. `-4.3 mm`) o falta de ataches rectangulares/retención en expansiones que pueda causar proinclinación coronal y pérdida de torque.
5) **OB/OJ (Sobremordida y Resalte):** Si la sobremordida (OB) objetivo sube cerca de `3.0 mm` al retruir o cerrar espacios, alertar del riesgo de mordida profunda secundaria y pedir **levantes de mordida anteriores adaptativos (curvos, sin rellenar) de 3 a 3**, comprobando que con el resalte inicial (OJ) el paciente no quede atrapado por detrás del levante en céntrica.
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
    "basado en los manuales, artículos y cursos de los Dres. **David González Zamora y Romina Vignolo Lobato**."
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
        st.markdown("#### 1. Paciente, Biotipo y Hábitos (RNO)")
        tipo_paciente = st.selectbox(
            "Grupo de edad / Dentición",
            [
                "Adulto (Dentición permanente)",
                "Adolescente en crecimiento (Select / Pro)",
                "Adolescente que viene de un K1 previo - Candidato a KiD K2 (Select Unlimited)",
                "Niño con algún diente de leche - Candidato a Angel KiD (K1 - 2 años)",
                "Niño en Crecimiento - Dentición Mixta (Pico 5-7 años / C1-C2 - K1)",
                "Niño Pequeño - Dentición Temporal pura (<6 años - K1)"
            ]
        )
        biotipo = st.selectbox(
            "Biotipo Facial",
            [
                "Mesofacial",
                "Braquifacial (Tendencia a sobremordida / Levantes anteriores de 3 a 3)",
                "Dolicofacial / Vertical (Tendencia a mordida abierta / Bite bubbles + Salto virtual)"
            ]
        )
        estado_periodontal = st.selectbox(
            "Estado Periodontal y Colaboración",
            [
                "Periodonto sano / Buena colaboración (Apto para Pro 7+3)",
                "Paciente Periodontal / Recesiones (NO usar Pro, usar Select)",
                "Colaboración dudosa (Cuidado con biseles muy perpendiculares)",
                "Niño pequeño (Muerde los alineadores: pedir ataches grandes 'ladrillos' / de colores)"
            ]
        )
        habitos_atm = st.multiselect(
            "Hábitos, Lengua, Sueño, Postura y ATM",
            [
                "Sin alteraciones",
                "Respirador oral (Verificar paso nasal real con ORL antes de usar tapes)",
                "Lengua baja / asimétrica torsional (Posicionador Lingual + Logopeda)",
                "Interposición lingual / Succión digital (Esperar erupción incisiva y poner Tongue Crib)",
                "Duerme boca abajo / mete mano u hombro bajo la cara (Poner almohada a los pies)",
                "Masticación unilateral predominante (Cambiar lado 2 años para remodelar cóndilo)",
                "Falta de gateo en infancia / Hipertono posterior / Asimetría postural",
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
            "Etiología y Mecánica Sagital Principal",
            [
                "Dentoalveolar (Protocolo A8 de distalización secuencial)",
                "Discrepancia mixta / Expansión Centrífuga (Distalar + Expandir + Protruir + 0.5mm primate)",
                "Retrusión mandibular en crecimiento (Protocolo A6 Bloques Tipo 1 rectos cubriendo el 6)",
                "Clase II con resalte < 3 mm o Fase II post-A6 (Levantes anteriores inclinados)",
                "Hipoplasia maxilar Clase III en crecimiento (Máscara facial + Corte alto 2.5mm + Angel Hook/Buttons)",
                "Clase III compensable en adulto/adolescente (Pro 7+3 + A8 inferior + Elásticos CIII en AngelButtons)",
                "Caso de Extracción de Premolares (Protocolo A7 + Atache DGZ)"
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
                "Sobremordida aumentada / Curva de Spee marcada (Levantes adaptativos de 3 a 3 desde día 1)",
                "Intrusión incisiva > 2.5 mm necesaria (Área de presión de intrusión + retención en vecinos)",
                "Mordida borde a borde / Salto de mordida CIII (Levantes anteriores adaptativos hacia incisal)",
                "Mordida abierta anterior en vertical (Bite bubbles posteriores para apretar + Salto virtual vertical)",
                "Canteo del plano oclusal (Valorar TADs con cabeza de botón)"
            ]
        )
        problema_transversal = st.selectbox(
            "Situación Transversal",
            [
                "Arcadas simétricas y bien coordinadas",
                "Compresión bilateral simétrica (Expansión simétrica + ataches control torque + Arcada cuadrada)",
                "Mordida cruzada UNILATERAL DERECHA (1º Expansión unilateral derecha -> 2º Bilateral simétrica)",
                "Mordida cruzada UNILATERAL IZQUIERDA (1º Expansión unilateral izquierda -> 2º Bilateral simétrica)",
                "Mordida cruzada posterior BILATERAL",
                "Mordida en tijera (Brodie)",
                "Secuela post-MARPE en adulto (Diastema con raíces en tienda de campaña -> Atache DGZ)"
            ]
        )
        apinamiento_sup = st.selectbox("Espacio Arcada Superior", ["Sin apiñamiento", "Apiñamiento leve (<=2 mm)", "Apiñamiento moderado (3-5 mm)", "Apiñamiento severo (6-10 mm)", "Diastemas / Cierre post-MARPE (Atache DGZ)"])
        apinamiento_inf = st.selectbox("Espacio Arcada Inferior", ["Sin apiñamiento", "Apiñamiento leve (<=2 mm)", "Apiñamiento moderado (3-5 mm)", "Apiñamiento severo (6-10 mm)", "Diastemas / Espacios"])
        incisivos_inclinacion = st.selectbox("Inclinación de Incisivos (Torque inicial)", ["Normoinclinados", "Proinclinados superior e inferior", "Retroinclinados (HBO en el CENTRO de la corona + Torque Ridge + Corte alto)", "Superior proinclinado / Inferior retroinclinado", "Superior retroinclinado / Inferior proinclinado (Compensación CIII)"])

    notas_clinicas_ini = st.text_area(
        "Notas adicionales del caso (ausencias, dientes ectópicos con CBCT para compensador activo, recambio incisivo, etc.):",
        placeholder="Ej: Niño de 6 años con incisivos centrales erupcionando, mordida cruzada derecha y Clase II..."
    )

    if st.button("🚀 Generar Prescripción Inicial Completa y Esquemas Visuales", type="primary"):
        prompt_fase1 = f"""
Genera la PLANIFICACIÓN BIOMECÁNICA Y PRESCRIPCIÓN INICIAL COMPLETA para enviar este caso a Angel Aligner (iOrtho), aplicando al máximo todos los protocolos de los manuales y cursos de los Dres. David González Zamora y Romina Vignolo:

DATOS DIAGNÓSTICOS DEL PACIENTE:
- Edad / Dentición: {tipo_paciente}
- Biotipo facial: {biotipo} | Estado Periodontal/Colaboración: {estado_periodontal}
- Hábitos, Lengua, Sueño y Postura: {', '.join(habitos_atm)}
- Clase Molar: Derecha = {c_molar_d} | Izquierda = {c_molar_i}
- Clase Canina: Derecha = {c_canina_d} | Izquierda = {c_canina_i}
- Etiología sagital: {origen_sagital} | Resalte (Overjet) inicial: {resalte_oj} mm
- Línea Media Superior: {lm_sup} | Línea Media Inferior: {lm_inf}
- Sobremordida (Overbite) inicial: {sobremordida_ob} mm ({problema_vertical})
- Situación Transversal: {problema_transversal}
- Espacio Superior: {apinamiento_sup} | Espacio Inferior: {apinamiento_inf}
- Inclinación incisiva inicial: {incisivos_inclinacion}
- Notas clínicas adicionales: {notas_clinicas_ini if notas_clinicas_ini else 'Ninguna'}

Estructura tu respuesta detalladamente en estos 6 apartados:
1. **Producto Angel Aligner, Línea de Corte y Gestión Clínica:** (Elige entre Select 10/20/30/Unlimited, Pro 7+3 [prohibido en periodontales], o KiD K1/K2; define la Línea de Corte: Festoneada, Recta alta a 2.5 mm o Mixta si están erupcionando incisivos o es fase expansiva en adulto; incluye recomendaciones del kit de supervivencia o citas cada 6 alineadores con IPR en etapas 7, 13, 19...).
2. **Estrategia Transversal, RNO y Rehabilitación Funcional/Postural:** (Si es unilateral: 1º expandir lado comprimido y 2º bilateral simétrica hasta arcada cuadrada y líneas medias 100% centradas; control de torque molar con ataches para no abrir la mordida; espacio de primate de 0.5 mm en mesial y distal de caninos temporales; pautas de masticación durante 2 años por el lado no cruzado, truco de la almohada a los pies de la cama y rehabilitación de la lengua torsional).
3. **Estrategia Sagital y Secuenciación (Protocolos A6, A7, A8 o Expansión Centrífuga):** (Si es A6: exigir Bloque Tipo 1 recto —nunca Tipo 2—, cubriendo como mínimo el 1er molar inferior definitivo, salto mínimo de 4 mm —o dividido en 2 saltos si >7mm—, cambio 5+5 días, Fase I + Fase II hasta 9 meses; si es distalización en dentición mixta: acompasar 6 superior e inferior en Clase I y luego distalar molares de leche).
4. **Estrategia Vertical y Levantes de Mordida:** (Levantes anteriores curvos adaptativos de 3 a 3 sin cementar —verificando en céntrica que con el resalte inicial no muerda por detrás del levante—, levantes inclinados, o *bite bubbles* posteriores sin rellenar para apretar + salto virtual vertical en dolicofaciales).
5. **Diseño Exacto de Ataches (DGZ, HBO, Rotación, Retención), Compensadores y Elásticos en AngelButtons:** (Dónde pedir el Atache DGZ talla M gingival + S incisal; dónde poner HBO en incisal para extruir vs en el centro de la corona para torque; recordatorio de no girar los biseles de Angel; ataches grandes/de colores en niños; compensadores activos con CBCT o barras en caninos incluidos; pauta de elásticos advirtiendo de vigilar que la Clase II no pase a Clase III).
6. **📝 TEXTO EXACTO LISTO PARA COPIAR Y PEGAR EN LAS INSTRUCCIONES AL TÉCNICO CAD DE iORTHO.**
Cita siempre entre paréntesis los nombres exactos de los archivos `.jpg` de la biblioteca gráfica para que se muestren debajo de tu respuesta.
"""
        with st.spinner("Generando prescripción clínica completa y cargando esquemas gráficos..."):
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
        "La IA leerá cada celda y aplicará todas las reglas de los Dres. Zamora y Vignolo."
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
        placeholder="Ej: Revisar rotaciones de caninos, colapso del 3-3 inferior, posición de los bloques A6 o tiempos de IPR..."
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
1. **Resumen de Datos Leídos en las Capturas de iOrtho:** (Bolton 3-3 y 6-6, ausencias dentarias detectadas con `—` o `X`, número de alineadores en MovE, puntos rojos de cambio de ataches —recordando revisar por palatino—, etapas donde han puesto los rombos de IPR, Anchura 3-3/4-4/5-5/6-6 y OB/OJ inicial vs objetivo).
2. **Auditoría Diente por Diente de la Tabla TM (Alertas Amarillas y Riesgos Ocultos en Blanco):**
   - Lista con sus valores exactos los dientes que superen límites biomecánicos en Rotación (>12-15°), Torque (>8-10°), Tip/Angulación (>4°), Traslación V-L o M-D, y Extrusión/Intrusión.
3. **Análisis del Gráfico `MovE` (Secuenciación, Acompasamiento Sagital y Citas cada 6 alineadores):**
   - Evalúa si todos los dientes se mueven a la vez sin secuenciar, si al distalar en Clase I van acompasados arriba y abajo, y si los rombos de IPR están mal ubicados (recuerda la regla de David de programar el IPR al inicio o en las citas de los alineadores 7, 13, 19...).
4. **Análisis de Anchura de Arcada, Simetría Transversal y Sobremordida (OB/OJ):**
   - Alerta si hay colapso intercanino (`3-3` negativo), si han expandido ambos lados a la vez en una mordida cruzada unilateral en vez de simetrizar primero el lado comprimido, o si el Overbite final sube cerca de ~3 mm (riesgo de mordida profunda). Verifica si con el Overjet inicial hay riesgo de que el paciente muerda por detrás de los levantes anteriores en céntrica.
5. **Soluciones Biomecánicas Angel Aligner (Atache DGZ, HBO incisal vs centro, Áreas de Presión, Levantes y Bloques A6):**
   - Indica exactamente dónde colocar el **Atache DGZ** (talla M gingival y S incisal, recordando que no cabe en incisivos inferiores), dónde poner **HBO en tercio incisal (extrusión) vs en el centro de la corona (torque)**, atache de retención para extruir incisivos inferiores, **áreas de presión de rotación** (12-25°), o corrección de Bloques A6 (Tipo 1 recto cubriendo el 6 inferior).
6. **📝 TEXTO NUMERADO LISTO PARA COPIAR Y PEGAR AL TÉCNICO CAD DE iORTHO.**
Cita siempre entre paréntesis los nombres exactos de los archivos `.jpg` de la biblioteca gráfica (como `01_Atache_DGZ_Geometria_Vectores.jpg`, `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`, `13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`, `33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg`, etc.) para mostrar las referencias visuales.
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
        "(ej. '¿Por qué no debo girar los ataches de extrusión y rotación de Angel?', '¿Por qué el bloque A6 Tipo 1 debe cubrir el 6 inferior?' o 'Enséñame la imagen del atache DGZ')."
    )

    for msg in st.session_state.chat_angel:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["texto"])
            if msg["rol"] == "assistant":
                mostrar_fotos_referencia(msg["texto"])

    pregunta_chat = st.chat_input("Ej: ¿Cómo trato una mordida cruzada unilateral derecha según Romina y qué le digo al técnico?")

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
