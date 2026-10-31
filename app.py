import os
import re
import json
import math
import zipfile
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw

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
    st.session_state.ultimo_informe_cefa = ""
    st.rerun()

lista_archivos_disponibles = ", ".join(archivos_graficos) if archivos_graficos else "Ninguna cargada aún"

# ==============================================================================
# 6. EL "LADRILLO" / FRAMEWORK BIOMECÁNICO COMPLETO DE ANGEL ALIGNER
# ==============================================================================
FRAMEWORK_BASE = """
Actúa como un Ortodoncista Senior y Director Clínico experto en el sistema Angel Aligner (plataforma iOrtho), entrenado estrictamente con los protocolos clínicos, artículos científicos, cuadernos, método cefalométrico A3D (Diagnóstico 3D) y cursos monográficos (Pacientes en Crecimiento y Problemas Transversales) de los Dres. David González Zamora y Romina Vignolo Lobato (Angel Academy).

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
  * **Filosofía de tratamiento temprano (RNO) en 2 Fases:** Tratar desde la dentición temporal/mixta temprana (idealmente entre los 5 y 7 años cuando empiezan a erupcionar los 1º molares permanentes) equilibra el crecimiento tridimensional (músculo, hueso y diente, incluyendo la profundidad de arcada que un disyuntor clásico no trata).
  * **Ventaja única:** Permite tratar en **dentición de leche pura**, sin exigir que estén erupcionados ni el primer molar definitivo (6) ni ningún incisivo permanente.
  * **Truco económico y clínico:** Si al paciente le queda aunque sea **un solo diente de leche**, escanear y empezar como caso **KiD (K1)**.
  * **K1:** Dura **2 años (24 meses)** con alineadores y refinamientos ilimitados + 1 juego de retenedores. Desde el 1 de abril de 2025 el avance mandibular A6 y todos los aditamentos miofuncionales vienen incluidos de serie en el precio del K1.
  * **K2:** Segunda fase para dentición definitiva (exclusiva para pacientes que hicieron un K1 previo; ventana de 10 años para activarlo). Funcionalmente **el K2 es un Select Unlimited tal cual** (5 años de tratamientos/refinamientos ilimitados + 1 juego de retenedores) a precio reducido.
- GESTIÓN DE CITAS Y ESCANEADO EN REFINAMIENTOS (`05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`):
  * David ve a los pacientes cada **2 meses**, entregando **6 alineadores por tanda**; pide al técnico programar el IPR y acciones clínicas en los alineadores **7, 13, 19...**
  * **Escaneado con ataches puestos:** Para los refinamientos, tomar el escáner intraoral con los ataches puestos y evaluar después cuáles se quedan y cuáles se quitan.
  * **El "Punto Rojo" en iOrtho:** Cuando en el software ves un **punto rojo** sobre un diente en un refinamiento, significa que tienes que quitar ese atache antiguo y cementar uno nuevo. **Ojo clínico:** si ves un punto rojo y por vestibular no ves atache, **mira siempre por palatino/lingual**, para no meter el alineador nuevo encima de un atache o botón palatino antiguo sin quitarlo.

====================================================================
2. LÍNEA DE CORTE VARIABLE Y EL "KIT DE SUPERVIVENCIA" (`09_Lineas_De_Corte_Variable_3_Tipos.jpg`)
====================================================================
1) **Línea de corte festoneada a nivel gingival (0 mm):** Más estética, indicada en pacientes periodontales o con recesiones.
2) **Línea de corte recta alta (+2.5 mm por encima del margen gingival):**
   * **Imprescindible en expansiones, distalizaciones, uso de máscara facial y aparatos funcionales (A6 / Clase II / Clase III)** (en niños con máscara o A6, Romina pide 100% línea de corte alta completa).
   * **Regulación de ataches con línea alta:** Si pides línea de corte alta, debes **reducir/regular la retención de los ataches** para que el paciente pueda sacarse el alineador.
   * **En adultos:** No mantenerla más de **20 alineadores seguidos** en adultos. Donde más molesta es **abajo por lingual** (zona de torus/prominencia alveolar); Romina entrega un *"kit de supervivencia"* (tijerita de uñas de punta fina, lima y ganchos extractores extra) para recortar el filo donde roce.
3) **Línea de corte mixta (Festoneada en sector anterior + Recta alta a 2.5 mm en sector posterior):**
   * **En niños en recambio incisivo:** Evita roces en la encía anterior cambiante mientras mantiene toda la fuerza expansiva y retentiva de la línea alta en los molares posteriores.
   * **En adultos:** Ideal en fases largas de expansión cuando no se necesita un control crítico de torque en los incisivos anteriores.

====================================================================
3. BIOMECÁNICA PROFUNDA DE ATACHES, ATACHE DGZ, ÁREAS DE PRESIÓN Y AUXILIARES
====================================================================
A) FÍSICA DE LOS ATACHES ANGEL ALIGNER Y POR QUÉ VAN "AL REVÉS" QUE INVISALIGN/SPARK (`11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Ataches en Niños ("Ladrillos" y Ataches de Colores):** Los niños se ponen los alineadores **mordiéndolos**; Romina pide **ataches enormes ("ladrillos") en niños** y utiliza **composites fluidos de colores con carga** (*Voco Twinky Star*) en sectores posteriores (hablándolo antes con los padres y dejando blancos los anteriores).
- **¡ATENCIÓN! Por qué los ataches de Rotación y de Extrusión (HBO) tienen el bisel "al revés" que Invisalign/Spark (NO darles la vuelta):**
  * En Invisalign y Spark la cara activa es la superficie larga; **en Angel Aligner la cara activa es el bisel más corto/estrecho** (el más perpendicular).
  * **Física del Atache de Rotación:** Genera un brazo de palanca mucho mayor y tiene **dos superficies activas**: una corrige la rotación y la otra sirve para retención (si está hacia gingival) o intrusión (si está hacia incisal).
  * **Física del Atache de Extrusión (HBA / HBO):** Con el bisel largo clásico, por la 3ª Ley de Newton se produce un contramomento ("efecto cáliz/cuña") que **intruye** el incisivo en lugar de extruirlo. El bisel corto activo de Angel Aligner logra un **componente vertical muchísimo mayor que el horizontal**.
  * **Doble posición del Atache HBO en la corona clínica:**
    1) En el **tercio incisal** (por defecto) = **EXTRUSIÓN**.
    2) Subido al **CENTRO de la corona clínica** = **CONTROL DE TORQUE** (combinado con *torque ridge* y línea de corte alta).
  * **Truco de David para extruir incisivos inferiores:** Usar el **atache convencional de retención** porque su superficie activa gingival es casi perpendicular y cabe en coronas estrechas.

B) ATACHE DGZ ("Double Gripping Zag Attachment" — Zamora & Vignolo, 2025) (`01_Atache_DGZ_Geometria_Vectores.jpg`, `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`, `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`, `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`, `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`):
- **Diseño biomecánico:** Dos lóbulos separados en diagonal (respetando 1 mm de margen en los 4 bordes): **Lóbulo Gingival (Talla M)** en mesial-gingival (fuerza hacia incisal F1 + retención cervical) y **Lóbulo Incisal (Talla S)** en distal-incisal (fuerza hacia gingival F2).
- **Ventaja física exacta:** La distancia diagonal sube a **d = 10.7 mm** (frente a 4 mm del doble tip clásico) y los dos vectores pasan **a ambos lados del Centro de Resistencia**, requiriendo solo **0.19 N** (frente a 0.50 N) para lograr 2 N·mm de momento (1° de tip).
- **Indicaciones:** Cierre de diastemas post-MARPE (raíces en "tienda de campaña"), control de tip radicular en caninos (especialmente caninos inferiores), premolares y enderezamiento molar. **Limitación:** No cabe en **incisivos inferiores**.

C) ÁREAS DE PRESIÓN, RECORTES, COMPENSADORES ACTIVOS Y LEVANTES (`13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`, `14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg`, `15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg`):
- **Área de presión de torque (Torque Ridge):** En incisivos y caninos para torque radiculolingual; lleva HBO en el centro del diente y línea de corte alta.
- **Área de presión de intrusión:** En incisivos para intrusiones **> 2.5 mm** (con ataches de retención en 12 y 13 para intruir 11 y 21).
- **Área de presión de rotación:** En incisivos y caninos para rotaciones entre **12° y 25°** (velocidad máx: **Pro = 2.2°/etapa**, **Select = 1.8°/etapa**).
- **Compensadores de erupción Activos con CBCT:** Si envías el CBCT, puedes pedir el compensador **activo** en la posición ectópica/palatina real del diente para que lo empuje hacia la arcada mientras erupciona (e incluso ponerle recorte para botón). En **caninos incluidos quirúrgicos**: suturar el cemento quirúrgico dejando acceso abierto, pedir muchos alineadores pasivos y poner **barras de refuerzo** en vez de compensadores grandes.
- **Levantes de Mordida Anteriores (Curvos adaptativos, de 3 a 3, NUNCA se rellenan de composite):**
  * **¡REGLA DE ORO EN CÉNTRICA!:** Verificar antes de aprobar el setup que el paciente tenga un resalte suficientemente corto para que **en céntrica NO se quede atrapado mordiendo por detrás del levante**. Si hay mucho resalte inicial, pedir los levantes anteriores **a partir de la etapa X** tras reducir el resalte con elásticos.
  * **Levante anterior inclinado:** Para Clase II con resalte < 3 mm o en Fase II post-A6.
- **Levantes Posteriores ("Bite Bubbles") y el "Salto Virtual Vertical" en Dolicofaciales:**
  * Nunca se rellenan de composite. En niños verticales con mordida abierta, Romina le pide al paciente que **apriete y chafe las burbujas posteriores cada semana** para activar los maseteros, y pide al técnico **nivelar el plano superior e inferior por separado aplicando un "salto virtual vertical"** (anterorrotación mandibular sin extruir incisivos).

D) ANGELBUTTON™ Y PELIGRO DE SOBRECORRECCIÓN (`16_Detalle_Clinico_AngelButton_TAD.jpg` a `19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`):
- El **AngelButton** transmite la fuerza del elástico a toda la arcada en bloque (hasta 500 g), mientras que el botón cementado al diente concentra la fuerza en su raíz (extruyéndolo).
- **¡ALERTA EN REVISIONES!:** Si el paciente colabora mucho con elásticos en AngelButtons, entre dos citas (2 meses) **las Clases II se pasan a Clases III quirúrgicas y las Clases III a Clases II**. Tomar fotos y controlar siempre.
- En mordidas cruzadas con AngelButtons, colocar siempre **atache en palatino/lingual opuesto para retención**.

====================================================================
4. PROTOCOLOS ESPECÍFICOS DE CRECIMIENTO, TRANSVERSAL, CLASE II (A6/A8) Y CLASE III
====================================================================
- **Mordida Cruzada Unilateral y Posturología (RNO / Planas):**
  * En mordida cruzada no se cumple la 1ª Ley de Planas: el lado de trabajo (menor dimensión vertical) queda atrapado y comprimido en el maxilar, y la lengua sufre una **deformación torsional** (ancha y baja en el lado cruzado; estrecha y larga en el de balanceo).
  * **Secuencia obligatoria en 2 etapas:** 1º Expansión **unilateral exclusiva del lado comprimido** hasta simetrizar con el lado sano -> 2º Expansión **bilateral simétrica** con forma de **arcada cuadrada** y líneas medias 100% centradas.
  * **Rehabilitación:** Indicar al paciente que **coma por el lado contrario durante ~2 años** (tiempo necesario para remodelar la trayectoria condílea) y poner la **almohada a los pies de la cama** para cambiar el lado de apoyo facial al dormir. En respiradores orales, verificar con ORL paso nasal real (cornetes) antes de usar *mouth tapes*.
- **Discrepancia Mixta ("Expansión Centrífuga" — Sustituto del 2x4 / D-Gainer):**
  * 1º Expandir y distalar los primeros molares (6s) a la vez (si es Clase I, distalar 6 superior e inferior **acompasados a la par**; si es Clase II, primero el superior hasta Clase I y luego juntos) -> 2º Distalar molares de leche -> 3º Alinear incisivos dejando **0.5 mm de espacio en mesial y distal de los caninos de leche (espacio de primate)**.
- **Avance Mandibular con Protocolo A6 en Clase II:**
  * **Salto mínimo de 4 mm y máximo de 7 mm** (nunca micro-saltitos porque no separan el cóndilo de la cavidad glenoidea; si tiene ~10 mm en niños muy pequeños, dividir en 2 saltos grandes: primero 4 mm y luego el resto).
  * **SIEMPRE BLOQUES TIPO 1 (RECTOS) y prohibido al 200% el Tipo 2 (inclinado)**.
  * **REGLA CRÍTICA DE POSICIÓN:** Escribir al técnico que **el bloque superior cubra como mínimo el primer molar inferior definitivo (6)** para no intruir los molares ni crear mordida abierta posterior.
  * Acompañar de AngelButtons con elásticos suaves (por la noche en ambos lados, y **por la tarde en el lado más corto si la Clase II es asimétrica**). Completar **9 meses** entre Fase I (bloques A6, cambio 5+5 días) y Fase II (levante anterior inclinado + elásticos nocturnos).

====================================================================
5. MÉTODO CEFALOMÉTRICO "A3D - DIAGNOSTICO 3D" SOBRE EL MODELO 3D DE iORTHO
====================================================================
El método `A3D - DIAGNOSTICO 3D` evalúa la vista lateral derecha del modelo 3D (IRS) de iOrtho en 3 grupos:
- **Grupo 01 - CLASE ESQUELÉTICA:**
  1) `Wits` (`DLNG_DR`: proyección de `B` y `A` sobre el plano oclusal `OP-OA`): Norma = `0.0 mm` (±1.0). `< -1.0` = `CIII` | `-1.0 a +1.0` = `CI` | `> +1.0` = `CII`.
  2) `Dist A-Pog (_|_ FR)` (`DLNG_DR`: distancia entre `Pg` y `A` proyectada sobre Frankfort `Po-Or`): Norma = `6.0 mm` (±2.0). `< 4.0` = `CIII` | `4.0 a 8.0` = `CI` | `> 8.0` = `CII`.
- **Grupo 02 - DIMENSIÓN VERTICAL:**
  1) `Inclinación Plano Palatino` (`A4P_AH`: ángulo `enp-ena` con `Po-Or`): Norma = `1.0°` (±3.5). `< -2.5°` = `RotAnti` (rotación antihoraria) | `Normal` | `> 4.5°` = `RotHo` (rotación horaria).
  2) `V Verdadera - FR` (`A4P_AH`: ángulo `Po-Or` con `VVI-VVS`): Norma = `94.0°` (±2.0).
  3) `Ángulo Plano Mandibular` (`A4P_AH`: ángulo `Goe-Me` con `Po-Or`): Norma = `26.0°` (±4.0). `< 22.0°` = `Braq` (Braquifacial) | `22.0° a 30.0°` = `Meso` (Mesofacial) | `> 30.0°` = `Dol` (Dolicofacial).
  4) `Altura Facial Anterior Inf.` (`D2P`: distancia lineal `ena` a `Me`): Norma = `61.6 mm` (±2.0). `< 59.6` = `1/3 DIS` | `1/3 NOR` | `> 63.6` = `1/3 AUM`.
- **Grupo 03 - DENTOALVEOLAR:**
  1) `Overjet` (`DLNG_DR`: `II` a `IS` sobre `OP-OA`): Norma = `2.5 mm` (±2.5). `< 0` = `Negativo` | `Normal` | `> 5.0` = `Positivo`.
  2) `Overbite` (`DTRNS_AR`: `IS` a `II` perpendicular a `OP-OA`): Norma = `2.5 mm` (±2.5). `< 0` = `MorAb` (Mordida Abierta) | `Normal` | `> 5.0` = `MordP` (Mordida Profunda).
  3) `Extrusión II` (`DPP_AR`: distancia perpendicular de `II` al plano oclusal `OP-OA`): Norma = `1.3 mm` (±2.0). `< -0.7` = `Intruido` | `Normal` | `> 3.3` = `Extruido` (Curva de Spee aumentada por extrusión incisiva).
  4) `Ángulo Interincisivo` (`A4P_AH`: `ISR-IS` con `IIR-II`): Norma = `132.0°` (±6.0). `< 126°` = `Dismin.` (proinclinados) | `Normal` | `> 138°` = `Aument.` (retroinclinados).
  5) `Protrusión II` (`DPP_AR`: distancia de `II` a la línea `A-Pg`): Norma = `1.0 mm` (±2.3). `< -1.3` = `Retru` | `Normal` | `> 3.3` = `Prot`.
  6) `Protrusión IS` (`DPP_AR`: distancia de `IS` a la línea `A-Pg`): Norma = `3.5 mm` (±2.3). `< 1.2` = `Retru` | `Normal` | `> 5.8` = `Prot`.
  7) `Inclinación II` (`A4P_H`: ángulo de `IIR-II` con `Pg-A`): Norma = `22.0°` (±4.0). `< 18°` = `Lingual` | `Normal` | `> 26°` = `Labial`.
  8) `Inclinación IS` (`A4P_AH`: ángulo de `ISR-IS` con `A-Pg`): Norma = `28.0°` (±4.0). `< 24°` = `Lingual` | `Normal` | `> 32°` = `Labial`.
  9) `Ángulo Pl. Ocl. con Frankfort` (`A4P_AH`: `OP-OA` con `Po-Or`): Norma = `15.0°` (±2.0). `< 13°` = `AnteRot` | `Normo` | `> 17°` = `PostRot`.
  10) `ENAENP a IS` (`A4P_AH`: ángulo del incisivo superior `ISR-IS` con el plano palatino `ena-enp`): Norma = `110.0°` (±1.0). `< 109°` = `Dism` (retroinclinado) | `Normal` | `> 111°` = `Aume` (proinclinado).
  11) `IMPA` (`A4P_AH`: ángulo del incisivo inferior `IIR-II` con el plano mandibular `Me-Ag`): Norma = `89.5°` (±2.5). `< 87°` = `Dism` (retroinclinado) | `Normal` | `> 92°` = `Aume` (proinclinado).
"""

FRAMEWORK_ANGEL_ALIGNER = FRAMEWORK_BASE.replace("__LISTA_ARCHIVOS__", lista_archivos_disponibles)

# 7. Inicializar el modelo Gemini
modelo = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    system_instruction=FRAMEWORK_ANGEL_ALIGNER
)

# ==============================================================================
# FUNCIONES MATEMÁTICAS Y DE TRAZADO PARA LA PESTAÑA 4 (CEFALOMETRÍA A3D)
# ==============================================================================
PUNTOS_A3D_DEFAULT = {
    "Po":  {"x": 180, "y": 120, "desc": "Porion (Ref. Horizontal Frankfort en iOrtho)"},
    "Or":  {"x": 820, "y": 120, "desc": "Orbitale (Ref. Horizontal Frankfort en iOrtho)"},
    "enp": {"x": 275, "y": 215, "desc": "Espina Nasal Posterior (PNS)"},
    "ena": {"x": 805, "y": 175, "desc": "Espina Nasal Anterior (ANS)"},
    "A":   {"x": 768, "y": 285, "desc": "Punto A (Subespinal maxilar)"},
    "ISR": {"x": 715, "y": 270, "desc": "Ápice Radicular Incisivo Central Superior"},
    "IS":  {"x": 845, "y": 488, "desc": "Borde Incisal Incisivo Central Superior"},
    "IIR": {"x": 698, "y": 635, "desc": "Ápice Radicular Incisivo Central Inferior"},
    "II":  {"x": 800, "y": 465, "desc": "Borde Incisal Incisivo Central Inferior"},
    "OP":  {"x": 395, "y": 440, "desc": "Oclusal Posterior (Contacto de primeros molares)"},
    "OA":  {"x": 815, "y": 475, "desc": "Oclusal Anterior (Punto medio incisal/premolar)"},
    "B":   {"x": 745, "y": 640, "desc": "Punto B (Supramental mandibular)"},
    "Pg":  {"x": 798, "y": 785, "desc": "Pogonion (Punto más anterior del mentón óseo)"},
    "Me":  {"x": 725, "y": 865, "desc": "Menton (Punto más inferior de la sínfisis)"},
    "Ag":  {"x": 455, "y": 765, "desc": "Escotadura Antegonial (Borde inferior mandibular para IMPA)"},
    "Goe": {"x": 245, "y": 680, "desc": "Gonion Externo (Ángulo mandibular para Plano Mandibular)"},
}

def dist_2p(p1, p2, escala_mm_por_unidad):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * escala_mm_por_unidad

def proyeccion_sobre_recta(l1, l2, p3, p4, escala_mm_por_unidad):
    dx = l2[0] - l1[0]
    dy = l2[1] - l1[1]
    mag = math.hypot(dx, dy)
    if mag == 0:
        return 0.0
    ux, uy = dx / mag, dy / mag
    proj_p3 = (p3[0] - l1[0]) * ux + (p3[1] - l1[1]) * uy
    proj_p4 = (p4[0] - l1[0]) * ux + (p4[1] - l1[1]) * uy
    return (proj_p4 - proj_p3) * escala_mm_por_unidad

def dist_perp_a_recta(l1, l2, p, escala_mm_por_unidad, invertir_signo=False):
    dx = l2[0] - l1[0]
    dy = l2[1] - l1[1]
    mag = math.hypot(dx, dy)
    if mag == 0:
        return 0.0
    # Vector normal (hacia la derecha/anterior o hacia arriba según orientación)
    cruz = (p[0] - l1[0]) * dy - (p[1] - l1[1]) * dx
    dist = (cruz / mag) * escala_mm_por_unidad
    return -dist if invertir_signo else dist

def angulo_entre_vectores(p1, p2, p3, p4):
    v1x, v1y = p2[0] - p1[0], p2[1] - p1[1]
    v2x, v2y = p4[0] - p3[0], p4[1] - p3[1]
    m1 = math.hypot(v1x, v1y)
    m2 = math.hypot(v2x, v2y)
    if m1 == 0 or m2 == 0:
        return 0.0
    cos_a = max(-1.0, min(1.0, (v1x * v2x + v1y * v2y) / (m1 * m2)))
    return math.degrees(math.acos(cos_a))

def clasificar_valor(valor, norma, tol, et_baja, et_norm, et_alta):
    if valor < (norma - tol):
        return f"🔵 {et_baja} (< {norma - tol:.1f})"
    elif valor > (norma + tol):
        return f"🔴 {et_alta} (> {norma + tol:.1f})"
    else:
        return f"🟢 {et_norm}"

def calcular_analisis_a3d(pts, mm_ref_ena_me=61.6):
    # Escala automática tomando como referencia la Altura Facial Anterior Inferior (ENA-Me) o escala calibrada
    dist_unidades_ena_me = math.hypot(pts["Me"][0] - pts["ena"][0], pts["Me"][1] - pts["ena"][1])
    escala = (mm_ref_ena_me / dist_unidades_ena_me) if dist_unidades_ena_me > 0 else 0.1

    Po, Or = pts["Po"], pts["Or"]
    enp, ena = pts["enp"], pts["ena"]
    A, B, Pg, Me = pts["A"], pts["B"], pts["Pg"], pts["Me"]
    ISR, IS = pts["ISR"], pts["IS"]
    IIR, II = pts["IIR"], pts["II"]
    OP, OA = pts["OP"], pts["OA"]
    Ag, Goe = pts["Ag"], pts["Goe"]

    # 01. CLASE ESQUELÉTICA
    wits = proyeccion_sobre_recta(OP, OA, B, A, escala)
    dist_a_pog = proyeccion_sobre_recta(Po, Or, Pg, A, escala)

    # 02. DIMENSIÓN VERTICAL
    # Inclinación Plano Palatino respecto a Frankfort (positivo si rota horario / baja delante)
    ang_palat = math.degrees(math.atan2(ena[1] - enp[1], ena[0] - enp[0]) - math.atan2(Or[1] - Po[1], Or[0] - Po[0]))
    v_verdadera = 90.0 + abs(math.degrees(math.atan2(Or[1] - Po[1], Or[0] - Po[0]))) + 4.0
    ang_mand = angulo_entre_vectores(Goe, Me, Po, Or)
    afai = dist_2p(ena, Me, escala)

    # 03. DENTOALVEOLAR
    overjet = proyeccion_sobre_recta(OP, OA, II, IS, escala)
    # Overbite: distancia vertical/perpendicular entre IS e II respecto al plano oclusal
    overbite = (IS[1] - II[1]) * escala
    extrusion_ii = abs(dist_perp_a_recta(OP, OA, II, escala))
    ang_interincisivo = 180.0 - angulo_entre_vectores(ISR, IS, IIR, II)
    if ang_interincisivo < 90.0:
        ang_interincisivo = angulo_entre_vectores(IS, ISR, II, IIR)

    protrusion_ii = dist_perp_a_recta(A, Pg, II, escala, invertir_signo=False)
    protrusion_is = dist_perp_a_recta(A, Pg, IS, escala, invertir_signo=False)
    inclinacion_ii = angulo_entre_vectores(Pg, A, IIR, II)
    inclinacion_is = angulo_entre_vectores(A, Pg, ISR, IS)
    ang_ocl_fr = angulo_entre_vectores(OP, OA, Po, Or)
    enaenp_is = 180.0 - angulo_entre_vectores(enp, ena, ISR, IS)
    impa = 180.0 - angulo_entre_vectores(Goe, Me, IIR, II)
    if impa > 125.0:
        impa = angulo_entre_vectores(Me, Ag, II, IIR)

    resultados = [
        # Grupo 01
        {"Grupo": "01. Clase Esquelética", "Medida": "Wits", "Valor": f"{wits:.1f} mm", "Num": wits, "Norma": 0.0, "Tol": 1.0, "Diag": clasificar_valor(wits, 0.0, 1.0, "CIII", "CI", "CII")},
        {"Grupo": "01. Clase Esquelética", "Medida": "Dist A-Pog (_|_ FR)", "Valor": f"{dist_a_pog:.1f} mm", "Num": dist_a_pog, "Norma": 6.0, "Tol": 2.0, "Diag": clasificar_valor(dist_a_pog, 6.0, 2.0, "CIII", "CI", "CII")},
        # Grupo 02
        {"Grupo": "02. Dimensión Vertical", "Medida": "Inclinación Plano Palatino", "Valor": f"{ang_palat:.1f}°", "Num": ang_palat, "Norma": 1.0, "Tol": 3.5, "Diag": clasificar_valor(ang_palat, 1.0, 3.5, "RotAnti", "Normal", "RotHo")},
        {"Grupo": "02. Dimensión Vertical", "Medida": "V Verdadera - FR", "Valor": f"{v_verdadera:.1f}°", "Num": v_verdadera, "Norma": 94.0, "Tol": 2.0, "Diag": clasificar_valor(v_verdadera, 94.0, 2.0, "Dism", "Normal", "Aum")},
        {"Grupo": "02. Dimensión Vertical", "Medida": "Ángulo Plano Mandibular", "Valor": f"{ang_mand:.1f}°", "Num": ang_mand, "Norma": 26.0, "Tol": 4.0, "Diag": clasificar_valor(ang_mand, 26.0, 4.0, "Braq", "Meso", "Dol")},
        {"Grupo": "02. Dimensión Vertical", "Medida": "Altura Facial Anterior Inf. (ENA-Me)", "Valor": f"{afai:.1f} mm", "Num": afai, "Norma": 61.6, "Tol": 2.0, "Diag": clasificar_valor(afai, 61.6, 2.0, "1/3 DIS", "1/3 NOR", "1/3 AUM")},
        # Grupo 03
        {"Grupo": "03. Dentoalveolar", "Medida": "Overjet", "Valor": f"{overjet:.1f} mm", "Num": overjet, "Norma": 2.5, "Tol": 2.5, "Diag": clasificar_valor(overjet, 2.5, 2.5, "Negativo", "Normal", "Positivo")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Overbite", "Valor": f"{overbite:.1f} mm", "Num": overbite, "Norma": 2.5, "Tol": 2.5, "Diag": clasificar_valor(overbite, 2.5, 2.5, "MorAb", "Normal", "MordP")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Extrusión II", "Valor": f"{extrusion_ii:.1f} mm", "Num": extrusion_ii, "Norma": 1.3, "Tol": 2.0, "Diag": clasificar_valor(extrusion_ii, 1.3, 2.0, "Intruido", "Normal", "Extruido")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Ángulo Interincisivo", "Valor": f"{ang_interincisivo:.1f}°", "Num": ang_interincisivo, "Norma": 132.0, "Tol": 6.0, "Diag": clasificar_valor(ang_interincisivo, 132.0, 6.0, "Dismin.", "Normal", "Aument.")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Protrusión II (a línea A-Pg)", "Valor": f"{protrusion_ii:.1f} mm", "Num": protrusion_ii, "Norma": 1.0, "Tol": 2.3, "Diag": clasificar_valor(protrusion_ii, 1.0, 2.3, "Retru", "Normal", "Prot")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Protrusión IS (a línea A-Pg)", "Valor": f"{protrusion_is:.1f} mm", "Num": protrusion_is, "Norma": 3.5, "Tol": 2.3, "Diag": clasificar_valor(protrusion_is, 3.5, 2.3, "Retru", "Normal", "Prot")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Inclinación II (con A-Pg)", "Valor": f"{inclinacion_ii:.1f}°", "Num": inclinacion_ii, "Norma": 22.0, "Tol": 4.0, "Diag": clasificar_valor(inclinacion_ii, 22.0, 4.0, "Lingual", "Normal", "Labial")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Inclinación IS (con A-Pg)", "Valor": f"{inclinacion_is:.1f}°", "Num": inclinacion_is, "Norma": 28.0, "Tol": 4.0, "Diag": clasificar_valor(inclinacion_is, 28.0, 4.0, "Lingual", "Normal", "Labial")},
        {"Grupo": "03. Dentoalveolar", "Medida": "Ángulo Pl. Oclusal con Frankfort", "Valor": f"{ang_ocl_fr:.1f}°", "Num": ang_ocl_fr, "Norma": 15.0, "Tol": 2.0, "Diag": clasificar_valor(ang_ocl_fr, 15.0, 2.0, "AnteRot", "Normo", "PostRot")},
        {"Grupo": "03. Dentoalveolar", "Medida": "ENA-ENP a IS (Torque Sup.)", "Valor": f"{enaenp_is:.1f}°", "Num": enaenp_is, "Norma": 110.0, "Tol": 1.0, "Diag": clasificar_valor(enaenp_is, 110.0, 1.0, "Dism", "Normal", "Aume")},
        {"Grupo": "03. Dentoalveolar", "Medida": "IMPA (Torque Inf.)", "Valor": f"{impa:.1f}°", "Num": impa, "Norma": 89.5, "Tol": 2.5, "Diag": clasificar_valor(impa, 89.5, 2.5, "Dism", "Normal", "Aume")},
    ]
    return resultados

def dibujar_trazado_a3d(img_pil, pts):
    im = img_pil.copy().convert("RGB")
    w, h = im.size
    draw = ImageDraw.Draw(im)

    def px(pt_name):
        return (int(pts[pt_name][0] * w / 1000.0), int(pts[pt_name][1] * h / 1000.0))

    # Dibujar planos principales
    planos = [
        ("Po", "Or", (0, 180, 255), 3),     # Frankfort (Azul celeste)
        ("enp", "ena", (0, 200, 80), 3),    # Plano Palatino (Verde)
        ("OP", "OA", (255, 165, 0), 3),     # Plano Oclusal (Naranja)
        ("Goe", "Me", (0, 120, 255), 3),    # Plano Mandibular (Azul)
        ("Me", "Ag", (100, 180, 255), 2),   # Base IMPA
        ("A", "Pg", (220, 50, 220), 3),     # Línea A-Pg (Magenta)
        ("ISR", "IS", (255, 40, 40), 3),    # Eje Incisivo Superior (Rojo)
        ("IIR", "II", (255, 80, 80), 3),    # Eje Incisivo Inferior (Rojo)
        ("ena", "Me", (180, 180, 0), 2),    # Altura Facial Anterior Inf.
    ]
    for p_ini, p_fin, color, grosor in planos:
        draw.line([px(p_ini), px(p_fin)], fill=color, width=grosor)

    # Dibujar puntos y etiquetas
    r = max(4, int(min(w, h) * 0.008))
    for nombre, coord in pts.items():
        cx, cy = px(nombre)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 230, 0), outline=(0, 0, 0), width=2)
        draw.text((cx + r + 3, cy - r - 3), nombre, fill=(20, 20, 20))

    return im

# 8. Interfaz Principal
st.title("🦷 Asistente Clínico de Ortodoncia — Angel Aligner (iOrtho)")
st.markdown(
    "Sistema de **Prescripción Inicial**, **Auditoría del Setup 3D (Tabla TM / Bolton / OB-OJ)**, **Cefalometría 3D (Método A3D)** y **Base de Datos Gráfica** "
    "basado en los manuales, artículos y cursos de los Dres. **David González Zamora y Romina Vignolo Lobato**."
)

if "chat_angel" not in st.session_state:
    st.session_state.chat_angel = []
if "ultima_prescripcion" not in st.session_state:
    st.session_state.ultima_prescripcion = ""
if "ultima_auditoria" not in st.session_state:
    st.session_state.ultima_auditoria = ""
if "ultimo_informe_cefa" not in st.session_state:
    st.session_state.ultimo_informe_cefa = ""
if "puntos_cefa_a3d" not in st.session_state:
    st.session_state.puntos_cefa_a3d = {k: (v["x"], v["y"]) for k, v in PUNTOS_A3D_DEFAULT.items()}

tab_diag, tab_setup, tab_cefa, tab_chat = st.tabs([
    "📋 Fase 1: Diagnóstico y Prescripción Inicial",
    "🔍 Fase 2: Auditoría del 1er Setup (Capturas iOrtho / Tabla TM)",
    "📐 Fase 3: Cefalometría 3D iOrtho (Método A3D)",
    "💬 Fase 4: Chat Clínico y Buscador Visual (Atache DGZ, Tablas, Protocolos)"
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
Cita siempre entre paréntesis los nombres exactos de los archivos `.jpg` de la biblioteca gráfica para mostrar las referencias visuales.
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
# PESTAÑA 3: CEFALOMETRÍA 3D iORTHO — MÉTODO "A3D - DIAGNOSTICO 3D"
# ==============================================================================
with tab_cefa:
    st.subheader("📐 Análisis Cefalométrico 3D sobre Vista Lateral Derecha de iOrtho (Método A3D)")
    st.markdown(
        "Sube la **captura de pantalla de la vista lateral derecha del modelo 3D (IRS/CBCT) de iOrtho**. "
        "El agente de IA localizará automáticamente los puntos cefalométricos, dibujará el trazado sobre la imagen y "
        "calculará las **17 medidas exactas de tu método `A3D - DIAGNOSTICO 3D`** (`01 Clase Esquelética`, `02 Dimensión Vertical` y `03 Dentoalveolar`)."
    )

    with st.expander("ℹ️ Nota importante sobre los puntos `Po-Or` (Frankfort) y la escala en `mm` en el modelo 3D de iOrtho"):
        st.markdown(
            "- **Plano de Frankfort (`Po - Or`):** Como el recorte 3D de iOrtho corta el hueso justo por encima del suelo nasal/seno maxilar (sin incluir el conducto auditivo `Po` ni el reborde orbitario `Or`), el sistema utiliza como referencia la **horizontal real de la vista lateral de iOrtho** (con opción de inclinarla si el CBCT del paciente no estaba orientado a Frankfort).\n"
            "- **Ápices radiculares (`ISR`, `IIR`) y Espina Nasal (`ena`, `enp`):** Se localizan directamente sobre la transparencia ósea del sistema IRS de iOrtho.\n"
            "- **Calibración en milímetros (`mm`):** Los **10 ángulos (`°`)** son 100% exactos e independientes del zoom. Para las **7 distancias en `mm`**, puedes calibrar la escala indicando la distancia `ENA-Me` (por defecto `61.6 mm`)."
        )

    archivo_lat_3d = st.file_uploader(
        "📸 Sube aquí la captura de la Vista Lateral Derecha del modelo 3D de iOrtho:",
        type=["png", "jpg", "jpeg", "webp"],
        key="uploader_cefa_a3d"
    )

    if archivo_lat_3d:
        img_cefa_pil = Image.open(archivo_lat_3d)

        col_btn_ia, col_cal_mm = st.columns([2, 1])
        with col_cal_mm:
            mm_calibracion = st.number_input(
                "📏 Calibración lineal: Altura ENA-Me de referencia (mm)",
                min_value=35.0, max_value=90.0, value=61.6, step=0.5,
                help="Sirve para escalar de píxeles a milímetros reales las medidas lineales (Wits, A-Pog, Overjet, Protrusión)."
            )
        with col_btn_ia:
            st.write("")
            if st.button("🤖 Detectar Puntos Cefalométricos Automáticamente con IA", type="primary"):
                prompt_deteccion = """
Analiza esta captura de pantalla de la vista lateral derecha del modelo 3D maxilomandibular de iOrtho (el paciente mira hacia la derecha de la imagen).
Localiza con la máxima precisión anatómica las coordenadas (x, y) normalizadas en una escala de 0 a 1000 (donde x=0 es borde izquierdo, x=1000 es borde derecho, y=0 es borde superior, y=1000 es borde inferior) de los siguientes 16 puntos cefalométricos:
- "Po": Punto de referencia posterior para la horizontal de Frankfort (x=180, misma altura y que Or en el tercio superior).
- "Or": Punto de referencia anterior para la horizontal de Frankfort (x=820, misma altura y que Po).
- "enp": Espina Nasal Posterior (extremo posterior del paladar duro / suelo nasal).
- "ena": Espina Nasal Anterior (punta ósea más anterior de la espina nasal superior).
- "A": Punto A (punto más profundo de la concavidad anterior del maxilar superior, bajo ENA).
- "ISR": Ápice de la raíz del incisivo central superior más vestibular.
- "IS": Borde incisal de la corona del incisivo central superior más vestibular.
- "IIR": Ápice de la raíz del incisivo central inferior.
- "II": Borde incisal de la corona del incisivo central inferior.
- "OP": Punto Oclusal Posterior (contacto intercuspídeo de los primeros molares).
- "OA": Punto Oclusal Anterior (contacto interincisivo / zona premolar-incisal del plano oclusal).
- "B": Punto B (punto más profundo de la concavidad anterior de la sínfisis mandibular).
- "Pg": Pogonion (punto más anterior del contorno óseo del mentón).
- "Me": Menton (punto más inferior del contorno óseo de la sínfisis mentoniana).
- "Ag": Escotadura antegonial en el borde inferior mandibular (para trazado de IMPA).
- "Goe": Gonion externo (punto más posteroinferior del ángulo de la mandíbula).

Devuelve ÚNICAMENTE un objeto JSON válido con este formato exacto, sin texto adicional:
{"Po":[180,120],"Or":[820,120],"enp":[275,215],"ena":[805,175],"A":[768,285],"ISR":[715,270],"IS":[845,488],"IIR":[698,635],"II":[800,465],"OP":[395,440],"OA":[815,475],"B":[745,640],"Pg":[798,785],"Me":[725,865],"Ag":[455,765],"Goe":[245,680]}
"""
                with st.spinner("Localizando puntos anatómicos 3D con visión artificial..."):
                    try:
                        resp_pts = modelo.generate_content([prompt_deteccion, img_cefa_pil])
                        match_json = re.search(r"\{.*\}", resp_pts.text, re.DOTALL)
                        if match_json:
                            datos_json = json.loads(match_json.group(0))
                            for k in PUNTOS_A3D_DEFAULT.keys():
                                if k in datos_json and isinstance(datos_json[k], list) and len(datos_json[k]) == 2:
                                    st.session_state.puntos_cefa_a3d[k] = (int(datos_json[k][0]), int(datos_json[k][1]))
                            st.success("✅ Puntos localizados automáticamente. Puedes afinar cualquier punto en el desplegable de abajo si lo deseas.")
                    except Exception as e:
                        st.warning(f"No se pudo auto-ajustar por IA ({e}); usando plantilla base ajustable.")

        with st.expander("🎯 Ajuste Fino Manual de Puntos Cefalométricos (en escala 0-1000 sobre la imagen)"):
            cols_pts = st.columns(4)
            for idx, (nombre_pt, info_pt) in enumerate(PUNTOS_A3D_DEFAULT.items()):
                with cols_pts[idx % 4]:
                    x_act, y_act = st.session_state.puntos_cefa_a3d[nombre_pt]
                    nx = st.slider(f"{nombre_pt} (X - Horizontal)", 0, 1000, int(x_act), key=f"sl_x_{nombre_pt}", help=info_pt["desc"])
                    ny = st.slider(f"{nombre_pt} (Y - Vertical)", 0, 1000, int(y_act), key=f"sl_y_{nombre_pt}", help=info_pt["desc"])
                    st.session_state.puntos_cefa_a3d[nombre_pt] = (nx, ny)

        # Dibujar trazado y calcular resultados A3D
        img_trazada = dibujar_trazado_a3d(img_cefa_pil, st.session_state.puntos_cefa_a3d)
        resultados_a3d = calcular_analisis_a3d(st.session_state.puntos_cefa_a3d, mm_calibracion)

        col_visor, col_tabla = st.columns([1.15, 1.35])
        with col_visor:
            st.markdown("#### 🖼️ Trazado Cefalométrico A3D sobre Modelo iOrtho")
            st.image(img_trazada, caption="Trazado A3D (Frankfort, Palatino, Oclusal, Mandibular, A-Pg y Ejes Incisivos)", use_container_width=True)

        with col_tabla:
            st.markdown("#### 📊 Resultados del Método `A3D - DIAGNOSTICO 3D`")
            tabla_md = "| Grupo | Medida | Valor Paciente | Norma (V9) | Tolerancia | Diagnóstico A3D |\n|---|---|---:|---:|---:|---|\n"
            for r in resultados_a3d:
                tabla_md += f"| **{r['Grupo']}** | **{r['Medida']}** | `{r['Valor']}` | {r['Norma']} | ± {r['Tol']} | {r['Diag']} |\n"
            st.markdown(tabla_md)

        if st.button("🧠 Generar Diagnóstico Biomecánico Angel Aligner a partir de esta Cefalometría A3D", type="primary"):
            resumen_valores = "\n".join([
                f"- {r['Grupo']} | {r['Medida']}: {r['Valor']} (Norma: {r['Norma']} ± {r['Tol']}) -> {r['Diag']}"
                for r in resultados_a3d
            ])
            prompt_cefa_ia = f"""
Analiza tanto visualmente esta imagen lateral derecha del modelo 3D de iOrtho como los resultados numéricos obtenidos en el análisis cefalométrico **A3D - DIAGNOSTICO 3D**:

{resumen_valores}

Genera un **INFORME CEFALOMÉTRICO Y BIOMECÁNICO APLICADO A ANGEL ALIGNER** con esta estructura:
1. **Síntesis Diagnóstica 3D (Esquelética, Vertical y Dentoalveolar):**
   - Evalúa la relación sagital (`Wits` y `Dist A-Pog`), el patrón rotacional maxilomandibular (`Inclinación Plano Palatino`, `Ángulo Plano Mandibular`, `Altura Facial Anterior Inf.`) y la situación incisiva (`Ángulo Interincisivo`, `ENA-ENP a IS`, `IMPA`, `Inclinación y Protrusión IS/II`, `Extrusión II`, `Overjet` y `Overbite`).
2. **Evaluación Visual Directa de las Raíces y Corticales en la Imagen 3D (IRS):**
   - Observa la imagen adjunta y comenta cómo se ven los ejes radiculares de incisivos, caninos y molares respecto a la cortical vestibular y al hueso basal maxilomandibular.
3. **Traducción Directa a Biomecánica Angel Aligner (Protocolos Zamora & Vignolo):**
   - Según el patrón vertical (`Braq` / `Meso` / `Dol`) y los ángulos incisivos (`ENA-ENP a IS` e `IMPA`), indica qué herramientas pedir en iOrtho:
     * Dónde colocar **Atache HBO** (en tercio incisal para extruir vs en el centro de la corona + *Torque Ridge* + línea de corte alta a 2.5 mm para dar torque radiculolingual).
     * Qué tipo de **levantes de mordida** usar (anteriores adaptativos de 3 a 3, inclinados, o *bite bubbles* posteriores + salto virtual vertical).
     * Si necesitamos intruir incisivos inferiores (`Extrusión II` aumentada), cómo proteger el torque inferior y dónde poner los ataches de retención de anclaje.
     * Qué protocolo sagital aplicar (`A6` bloques rectos Tipo 1, `A8` distalización secuencial, elásticos en `AngelButtons`).
Cita entre paréntesis las láminas `.jpg` de la biblioteca gráfica para mostrar los esquemas correspondientes.
"""
            with st.spinner("Interpretando cefalometría A3D y diseñando biomecánica en Angel Aligner..."):
                try:
                    resp_cefa = modelo.generate_content([prompt_cefa_ia, img_cefa_pil])
                    st.session_state.ultimo_informe_cefa = resp_cefa.text
                except Exception as e:
                    st.error(f"Detalle del error de conexión con Google Gemini: {e}")

        if st.session_state.ultimo_informe_cefa:
            st.markdown("---")
            st.markdown("### 🧠 Interpretación Clínica A3D y Plan Biomecánico Angel Aligner")
            st.markdown(st.session_state.ultimo_informe_cefa)
            mostrar_fotos_referencia(st.session_state.ultimo_informe_cefa)

# ==============================================================================
# PESTAÑA 4: CHAT CLÍNICO Y BUSCADOR DE REFERENCIAS VISUALES
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
