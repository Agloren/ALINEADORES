import os
import re
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
# 2. MOTOR AUTO-EXTRACTOR DE LA BASE DE DATOS VISUAL (PDFs + FOTOS DEL CURSO)
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
    return re.sub(r"_+", "_", limpio).strip("_")

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
                for idx, img_info in enumerate(page.get_images(full=True), start=1):
                    base_img = doc.extract_image(img_info[0])
                    if base_img and base_img.get("image"):
                        ext = base_img.get("ext", "jpg")
                        sub_path = os.path.join(CARPETA_FOTOS, f"{prefijo_sub}_Fig{idx}.{ext}")
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

    # 1. Artículo Atache DGZ
    extraer_pagina_y_recortes(pdf_dgz, 4, "01_Atache_DGZ_Geometria_Vectores.jpg", True, "01_Recorte_DGZ_P4")
    extraer_pagina_y_recortes(pdf_dgz, 8, "02_Atache_DGZ_Cierre_Diastema_MARPE.jpg", True, "02_Recorte_DGZ_P8")
    extraer_pagina_y_recortes(pdf_dgz, 9, "03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg", True, "03_Recorte_DGZ_P9")
    extraer_pagina_y_recortes(pdf_dgz, 10, "04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg", True, "04_Recorte_DGZ_P10")

    # 2. Cuaderno Angel Academy (40 o 49 págs)
    if pdf_cuaderno and os.path.isfile(pdf_cuaderno):
        try:
            with fitz.open(pdf_cuaderno) as doc_c:
                total_pags = len(doc_c)
        except Exception:
            total_pags = 40

        mapa_pags = (
            [
                (2, "05_Notas_Tips_Trucos_Zamora_Vignolo.jpg", False, ""),
                (3, "05b_Indice_Ortodoncia_Interceptiva_Y_Protocolos.jpg", False, ""),
                (8, "06a_Esquema_3D_Vias_Aereas_Senos_Raices.jpg", False, ""),
                (11, "06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg", True, "06_Recorte_IRS"),
                (14, "07_Material_Dual_MasterControl_S_Y_MC.jpg", True, "07_Recorte_Material"),
                (15, "07b_Propiedades_MasterControl_S_Triple_Capa.jpg", False, ""),
                (16, "07c_Propiedades_MasterControl_Rigido_Pro.jpg", False, ""),
                (17, "08_Caso_Intraoral_AngelButton_Y_TADs.jpg", False, ""),
                (20, "09_Lineas_De_Corte_Variable_3_Tipos.jpg", True, "09_Recorte_Corte"),
                (21, "10_Esquema_3D_Ataches_Y_Areas_Presion.jpg", True, "10_Recorte_3D"),
                (22, "11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg", False, ""),
                (23, "12_Tabla_2_Ataches_De_Precision.jpg", False, ""),
                (24, "13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg", False, ""),
                (25, "14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg", False, ""),
                (26, "15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg", False, ""),
                (27, "16_Detalle_Clinico_AngelButton_TAD.jpg", False, ""),
                (28, "17_Detalle_Perfil_AngelButton_TPU.jpg", False, ""),
                (29, "18_Figura_4_Aplicaciones_AngelButton_360.jpg", True, "18_Recorte_AngelButton"),
                (30, "19_Figura_5_Angel_Hook_Protraccion_CIII.jpg", True, "19_Recorte_AngelHook"),
                (31, "20_Protocolo_A6_Reglas_Avance_Mandibular.jpg", False, ""),
                (32, "21_Figura_6_Avance_Mandibular_A6_Bloques.jpg", True, "21_Recorte_A6"),
                (34, "22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg", False, ""),
                (35, "23_Porfolio_Angel_Pro_7_Mas_3.jpg", False, ""),
                (36, "24_Protocolo_Angel_Kid_Notas_Romina.jpg", False, ""),
                (37, "25_Esquema_Angel_Kid_Levantes_Y_A6.jpg", False, ""),
                (38, "26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg", False, ""),
                (39, "27_Tabla_Aditamentos_Angel_Kid.jpg", False, ""),
                (40, "27b_Retenedores_MasterControl_076mm.jpg", False, ""),
            ]
            if total_pags <= 42
            else [
                (2, "05_Notas_Tips_Trucos_Zamora_Vignolo.jpg", False, ""),
                (7, "05b_Indice_Ortodoncia_Interceptiva_Y_Protocolos.jpg", False, ""),
                (17, "06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg", True, "06_Recorte_IRS"),
                (21, "07_Material_Dual_MasterControl_S_Y_MC.jpg", True, "07_Recorte_Material"),
                (24, "08_Caso_Intraoral_AngelButton_Y_TADs.jpg", False, ""),
                (27, "09_Lineas_De_Corte_Variable_3_Tipos.jpg", True, "09_Recorte_Corte"),
                (28, "10_Esquema_3D_Ataches_Y_Areas_Presion.jpg", True, "10_Recorte_3D"),
                (29, "11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg", False, ""),
                (30, "12_Tabla_2_Ataches_De_Precision.jpg", False, ""),
                (31, "13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg", False, ""),
                (32, "14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg", False, ""),
                (33, "15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg", False, ""),
                (34, "16_Detalle_Clinico_AngelButton_TAD.jpg", False, ""),
                (35, "17_Detalle_Perfil_AngelButton_TPU.jpg", False, ""),
                (36, "18_Figura_4_Aplicaciones_AngelButton_360.jpg", True, "18_Recorte_AngelButton"),
                (37, "19_Figura_5_Angel_Hook_Protraccion_CIII.jpg", True, "19_Recorte_AngelHook"),
                (38, "20_Protocolo_A6_Reglas_Avance_Mandibular.jpg", False, ""),
                (39, "21_Figura_6_Avance_Mandibular_A6_Bloques.jpg", True, "21_Recorte_A6"),
                (43, "22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg", False, ""),
                (44, "23_Porfolio_Angel_Pro_7_Mas_3.jpg", False, ""),
                (45, "24_Protocolo_Angel_Kid_Notas_Romina.jpg", False, ""),
                (46, "25_Esquema_Angel_Kid_Levantes_Y_A6.jpg", False, ""),
                (47, "26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg", False, ""),
                (48, "27_Tabla_Aditamentos_Angel_Kid.jpg", False, ""),
                (49, "27b_Retenedores_MasterControl_076mm.jpg", False, ""),
            ]
        )
        for pag, nom, sub, pref in mapa_pags:
            extraer_pagina_y_recortes(pdf_cuaderno, pag, nom, sub, pref)

    # 3. Catálogo General, Artículo SAO y Brochure
    extraer_pagina_y_recortes(pdf_angel1, 6, "28_IRS_Control_Corona_Raiz_CBCT.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 8, "29_Esquema_Biomecanico_A6_Avance_Mandibular.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 9, "30_Protocolos_A7_Extracciones_Y_A8_Distalizacion.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 12, "31_Catalogo_Visual_AngelAttach.jpg")
    extraer_pagina_y_recortes(pdf_angel1, 13, "32_Catalogo_Visual_Areas_Presion_Y_Auxiliares.jpg")
    extraer_pagina_y_recortes(pdf_sao, 3, "33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg", True, "33_Recorte_BloquesA6")
    extraer_pagina_y_recortes(pdf_sao, 4, "34_Curva_Crecimiento_Y_5_Pasos_Clase_II.jpg")
    extraer_pagina_y_recortes(pdf_sao, 5, "35_Opciones_Elasticos_Clase_II_Con_A6.jpg", True, "35_Recorte_ElasticosA6")
    extraer_pagina_y_recortes(pdf_brochure, 6, "36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg", True, "36_Recorte_SetupCIII")
    extraer_pagina_y_recortes(pdf_brochure, 7, "37_Caso_Clase_III_Pro_Evolucion_Intraoral.jpg")

    # 4. Fotos sueltas del curso (.JPG, .PNG, .HEIC)
    for raiz, _, archivos in os.walk("."):
        if CARPETA_FOTOS in raiz or ".git" in raiz:
            continue
        for f in sorted(archivos):
            if f.startswith("._"):
                continue
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
                try:
                    nombre_limpio = limpiar_nombre_archivo(os.path.splitext(f)[0])
                    if not nombre_limpio.startswith("Curso_"):
                        nombre_limpio = f"Curso_{nombre_limpio}"
                    out_img_path = os.path.join(CARPETA_FOTOS, f"{nombre_limpio}.jpg")
                    if not os.path.isfile(out_img_path):
                        im = Image.open(os.path.join(raiz, f)).convert("RGB")
                        im.thumbnail((1500, 1500))
                        im.save(out_img_path, "JPEG", quality=85)
                except Exception:
                    pass

construir_base_datos_visual()

# 3. Configurar API de Google Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def preparar_imagen_para_ia(archivo_subido):
    img = Image.open(archivo_subido).convert("RGB")
    img.thumbnail((1600, 1600))
    return img

def mostrar_fotos_referencia(texto_respuesta):
    if not os.path.isdir(CARPETA_FOTOS):
        return
    encontradas = list(dict.fromkeys(re.findall(r"[A-Za-z0-9_]+\.(?:jpg|png|jpeg)", texto_respuesta)))
    archivos_validos = [f for f in encontradas if os.path.isfile(os.path.join(CARPETA_FOTOS, f))]
    if archivos_validos:
        st.markdown("#### 🖼️ Esquemas y Documentos Gráficos de Referencia:")
        cols = st.columns(min(len(archivos_validos), 2))
        for idx, nombre_foto in enumerate(archivos_validos):
            with cols[idx % 2]:
                st.image(os.path.join(CARPETA_FOTOS, nombre_foto), caption=f"📌 {nombre_foto}", use_container_width=True)

# 4. Barra lateral: Biblioteca Gráfica
st.sidebar.title("🦷 Biblioteca Gráfica Angel")
archivos_graficos = sorted([
    f for f in os.listdir(CARPETA_FOTOS)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
]) if os.path.isdir(CARPETA_FOTOS) else []

if archivos_graficos:
    laminas_manuales = [f for f in archivos_graficos if not f.startswith("Curso_")]
    fotos_curso = [f for f in archivos_graficos if f.startswith("Curso_")]
    st.sidebar.caption(f"📚 {len(laminas_manuales)} láminas oficiales | 📸 {len(fotos_curso)} fotos curso")

    cat_visor = st.sidebar.radio("Categoría:", ["📘 Láminas Oficiales (PDFs)", "📸 Fotos Curso"], label_visibility="collapsed")
    lista_mostrar = laminas_manuales if "Láminas" in cat_visor else fotos_curso
    foto_sel = st.sidebar.selectbox("Ver lámina/foto:", ["Seleccionar..."] + lista_mostrar)
    if foto_sel != "Seleccionar...":
        st.sidebar.image(os.path.join(CARPETA_FOTOS, foto_sel), caption=foto_sel, use_container_width=True)

if st.sidebar.button("🗑️ Nueva consulta / Limpiar", use_container_width=True):
    st.session_state.chat_angel = []
    st.session_state.planificacion_unificada = ""
    st.rerun()

lista_archivos_disponibles = ", ".join(archivos_graficos) if archivos_graficos else "Ninguna"

# ==============================================================================
# 5. MOTOR BIOMECÁNICO OPTIMIZADO ("EL LADRILLO" — ALTA DENSIDAD, CERO PAJA)
# ==============================================================================
FRAMEWORK_BASE = """
Eres el Motor de Decisión Clínica y Auditoría Biomecánica en Angel Aligner (iOrtho).
PROHIBIDO usar saludos, introducciones genéricas o texto de relleno. Ve directo al grano con precisión quirúrgica.

JERARQUÍA CLÍNICA INNEGOCIABLE (PRIORIDAD ABSOLUTA Nº 1: DRES. DAVID GONZÁLEZ ZAMORA Y ROMINA VIGNOLO LOBATO):
En cualquier discrepancia entre ponentes, aplica SIEMPRE el protocolo de David González Zamora y Romina Vignolo:
1) BLOQUES AVANCE MANDIBULAR (A6): SIEMPRE Bloques Tipo 1 (rectos/planos con anti-skid) y PROHIBIDO al 200% el Tipo 2 (inclinado). En dentición mixta/crecimiento deben situarse LO MÁS POSTERIOR POSIBLE, y el bloque superior DEBE CUBRIR COMO MÍNIMO EL 1er MOLAR INFERIOR DEFINITIVO (6) para evitar intrusión molar y mordida abierta posterior (solo en dentición permanente adulta/adolescente tardía van más anteriores).
2) LEVANTES DE MORDIDA: JAMÁS rellenar ni cementar con composite los levantes anteriores ni posteriores. En sobremordida usar levantes anteriores curvos adaptativos de 3 a 3 desde el día 1. En pacientes verticales/mordida abierta usar bite bubbles posteriores huecos para que el niño los apriete y chafe cada semana (rehabilitación maseterina) + pedir "salto virtual vertical" nivelando planos superior e inferior por separado.

REFERENCIAS VISUALES AUTOMÁTICAS:
Archivos disponibles: [__LISTA_ARCHIVOS__].
Escribe siempre entre paréntesis el nombre exacto de las láminas relevantes para mostrarlas en pantalla:
- `01_Atache_DGZ_Geometria_Vectores.jpg`, `02_Atache_DGZ_Cierre_Diastema_MARPE.jpg`, `03_Atache_DGZ_Enderezamiento_Molar_Canino.jpg`, `04_Atache_DGZ_vs_Doble_Tip_Invisalign.jpg`: Atache DGZ (lóbulo M gingival + S incisal, d=10.7mm, F=0.19N).
- `05_Notas_Tips_Trucos_Zamora_Vignolo.jpg`, `05b_Indice_Ortodoncia_Interceptiva_Y_Protocolos.jpg`: Citas cada 6 alineadores (IPR en 7, 13, 19...), TADs con cabeza de botón, protocolos A8 y RNO.
- `06_iOrtho_Cefalometria_IA_E_IRS_CBCT.jpg`, `28_IRS_Control_Corona_Raiz_CBCT.jpg`: Sistema IRS (CBCT+STL).
- `07_Material_Dual_MasterControl_S_Y_MC.jpg`, `22_Porfolio_Angel_Select_10_20_30_Unlimited.jpg`, `23_Porfolio_Angel_Pro_7_Mas_3.jpg`: Select vs Pro (7+3).
- `09_Lineas_De_Corte_Variable_3_Tipos.jpg`: Corte festoneado (0mm), recto alto (+2.5mm) y mixto.
- `11_Tabla_1_Ataches_Convencionales_HBO_DGZ.jpg`, `12_Tabla_2_Ataches_De_Precision.jpg`, `13_Tabla_3_Areas_De_Presion_Torque_Rotacion.jpg`, `14_Tabla_4_Recortes_Elasticos_Boton_Bracket.jpg`, `15_Tabla_5_Levantes_De_Mordida_Bite_Turbos.jpg`: Tablas oficiales 1 a 5 de ataches, áreas de presión, recortes y levantes.
- `18_Figura_4_Aplicaciones_AngelButton_360.jpg`, `19_Figura_5_Angel_Hook_Protraccion_CIII.jpg`: Mecánicas con AngelButton y Angel Hook.
- `20_Protocolo_A6_Reglas_Avance_Mandibular.jpg`, `21_Figura_6_Avance_Mandibular_A6_Bloques.jpg`, `33_Comparativa_Bloques_A6_Rectos_vs_Inclinados.jpg`, `35_Opciones_Elasticos_Clase_II_Con_A6.jpg`: Protocolo A6.
- `24_Protocolo_Angel_Kid_Notas_Romina.jpg`, `26_Esquema_Angel_Kid_Posicionador_Y_Habitos.jpg`, `27_Tabla_Aditamentos_Angel_Kid.jpg`, `27b_Retenedores_MasterControl_076mm.jpg`: Angel KiD (K1/K2) y retenedores.
- `30_Protocolos_A7_Extracciones_Y_A8_Distalizacion.jpg`, `36_Caso_Clase_III_Pro_Distalizacion_A8_Setup.jpg`: Protocolos A7 y A8.

====================================================================
REGLAS CLÍNICAS Y BIOMECÁNICAS DE ALTA PRECISIÓN
====================================================================
1. SELECCIÓN DE PRODUCTO, MATERIAL Y GESTIÓN DE CITAS:
- Activación por etapa: Pro = hasta 0.33 mm lineal y 2.2° rotación (ahorra ~30% de etapas); Select = 0.26–0.27 mm lineal y 1.8° rotación.
- Select (`MasterControl S` multicapa): Select 10 (<=2mm apiñamiento, <=20° rot, <=1mm OB, 1 ref), Select 20 (<=5mm, <=2.5mm AP, <=40° rot, 2 ref), Select 30 (<=10mm, <=4.5mm AP/OB, <=60° rot, 3 ref), Select Unlimited (5 años ilimitado; OBLIGATORIO en pacientes periodontales).
- Pro (Dual `7+3`: 7 días `MasterControl S` flexible + 3 días `MasterControl` TPU rígido; en adultos muy complejos de hueso denso usar `7+5` días): 6 años ilimitado + 3 retenedores (0.76mm). PROHIBIDO en pacientes periodontales.
- KiD (K1 y K2): Permite tratar en dentición temporal pura sin 6s ni incisivos definitivos. Si queda aunque sea 1 solo diente de leche, abrir como K1 (24 meses de refinamientos ilimitados con A6 y aditamentos incluidos). K2 = Select Unlimited (5 años) con ventana de 10 años tras K1.
  * Hándicap Retenedores KiD (Romina): El retenedor final de KiD viene siempre con corte festoneado y NO admite barras, ataches ni compensadores. Si faltan dientes por erupcionar y hay que mantener espacio, NO pedir el retenedor: pedir un refinamiento con corte alto y barras.
- Gestión clínica (David): Citas cada 2 meses entregando 6 alineadores (60 días). Programar el IPR y acciones clínicas en las etapas **7, 13, 19...** (el alineador 12 —4 meses— es el punto de control donde ya debe verse el cambio transversal y vertical).
- Escaneado en refinamientos y "Punto Rojo": Escanear con los ataches puestos. En iOrtho, un **punto rojo** significa quitar ese atache antiguo y cementar uno nuevo; si ves punto rojo y no ves atache en vestibular, **revisar siempre por palatino/lingual**.

2. LÍNEA DE CORTE VARIABLE Y REQUISITOS DEL STL:
- Requisito STL: Mínimo **5 mm de encía/mucosa escaneada** para poder pedir línea alta o mixta sin que el software invente la encía y cause isquemia.
- Tipos: 1) Festoneada (0 mm): periodontales/recesiones. 2) Recta alta (+2.5 mm): expansiones, pseudo-disyunciones, A8 en coronas cortas, máscara facial, A6 y niños con autismo/hipersensibilidad (permite tratar sin ataches cambiando cada 7 días). Al pedir corte alto, reducir la retención de los ataches. Donde más roza es abajo por lingual (entregar "Kit de Supervivencia": tijerita de uñas fina, lima de cristal y ganchos extra). 3) Mixta (festoneada anterior + 2.5 mm posterior): obligatoria en niños en recambio incisivo (encía anterior cambiante) y en adultos con expansión larga (>20 etapas) o apiñamiento/recesión anterior.
- 6 Contraindicaciones de la Línea de Corte Alta Completa al inicio: 1) Periodontales/recesiones, 2) Implantes/puentes sobrecontorneados (pedir recortar 2 mm hasta el ecuador coronal en ese diente), 3) Espacio edéntulo con molar inclinado a mesial (triángulo negro retentivo), 4) *Round-tripping* inferior, 5) Al inicio en Sobremordida / Clase II div 2 severa (pedir el corte alto más adelante tras alinear el torque entre centrales y laterales), 6) Apiñamiento anterior severo o brazos de disyuntor aún cementados.

3. ATACHES, ATACHE DGZ, ADAPTACIÓN A CAUCÁSICOS Y AUXILIARES:
- Biseles de Angel Aligner (NO darles la vuelta): A diferencia de Invisalign/Spark (donde la cara activa es el bisel largo), en Angel Aligner **la superficie activa es el bisel más corto/estrecho** (evita el "efecto cáliz/cuña" de la 3ª Ley de Newton que intruye el diente en vez de extruirlo).
- Doble posición del Atache HBO en incisivos (David y Romina):
  * En el **borde/tercio incisal** (por defecto) = **EXTRUSIÓN**.
  * Subido al **CENTRO de la corona clínica** = **TORQUE** (combinado con *Torque Ridge*, rampas y corte alto más adelante).
- Extrusión de incisivos inferiores (David): Usar el **atache convencional de retención** (cabe en coronas estrechas y su cara gingival es casi perpendicular).
- Rotación + Extrusión en caninos/premolares: Hacer 1º la rotación y 2º la extrusión; poner atache de rotación por vestibular y de retención por palatino. No pedir los ataches de precisión de la Tabla 2.
- Ataches en Niños: Poner ataches grandes ("ladrillos") con composite fluido de color con carga (*Voco Twinky Star*) en posteriores (previo acuerdo con los padres, blancos delante). **PROHIBIDO poner ataches en dientes definitivos a medio erupcionar** (desadaptan la férula; poner compensador de erupción y dejar salir solo) y **PROHIBIDO poner ataches retentivos en dientes de leche con raíz reabsorbida/móviles** (mirar panorámica).
- ATACHE DGZ (Zamora & Vignolo, 2025): Lóbulo Gingival Talla M (mesial-gingival) + Lóbulo Incisal Talla S (distal-incisal). Separa los vectores a d = 10.7 mm pasando **a ambos lados del Centro de Resistencia** con solo 0.19 N. Pedirlo SIEMPRE en lugar del doble tip o rectangular para: 1) Cierre de diastemas post-MARPE (evita raíces en "tienda de campaña"), 2) Control de tip radicular en caninos (especialmente canino inferior en Clase III o extracciones A7) y premolares, 3) Enderezamiento molar. **No cabe en incisivos inferiores**.
- Adaptación del algoritmo asiático a pacientes caucásicos (Vilarrasa):
  1) **Quitar siempre los *Power Ridges* de los incisivos laterales superiores** (en caucásicos son pequeños/conoides y desajustan el plástico) y ponerles un atache HBO.
  2) Añadir **+6° a +10° de extra-torque radiculolingual** adicional en centrales superiores en los protocolos A8 y A7.
  3) En adultos con hueso cortical denso, aislar la retracción del canino de la de los 4 incisivos, y en intrusión anterior >2.5 mm pedir ***Frog Staging* de intrusión** (alternar 8 etapas caninos y 8 etapas incisivos) + ataches de retención en dientes vecinos (ej. en 12 y 13 para intruir 11 y 21).
- Compensadores, Barras y Pónticos:
  * Con CBCT se pueden pedir **compensadores de erupción activos** que empujan al diente palatinizado/ectópico hacia la arcada.
  * En caninos incluidos quirúrgicos (suturando el cemento quirúrgico para dejar acceso abierto) o huecos grandes: pedir **barras** (disponibles también en anterior sujetas por mesial y distal) en vez de compensadores grandes para que el alineador no se cuele en el hueco, + 10 alineadores pasivos.
  * En dientes desgastados a rehabilitar tras ortodoncia: pedir un **compensador de erupción acoplado al diente con la altura protésica definitiva**.
  * En adultos con desgaste severo generalizado: hacer antes **composites inyectados provisionales haciendo el match CBCT+STL** para respetar el eje real de la raíz.

4. LEVANTES DE MORDIDA, ANGELBUTTONS Y CONTROL VERTICAL:
- Levantes Anteriores (Curvos adaptativos de 3 a 3, SIN cementar):
  * **REGLA CRÍTICA EN CÉNTRICA:** Verificar antes de aprobar el setup que con el resalte (OJ) inicial el paciente **NO pueda quedarse atrapado mordiendo por detrás del levante en relación céntrica**. Si hay mucho resalte inicial, pedir los levantes anteriores **a partir de la etapa X** tras haber reducido el resalte con elásticos.
  * Levante anterior inclinado: para Clase II con resalte < 3 mm, desviaciones funcionales (*side-shift*), Fase II post-A6, o en Clase III compensable (sube hacia incisal para saltar la mordida; **prohibido poner levantes posteriores en Clase III si queremos aplanar la curva de Spee**).
- Mordida Abierta:
  * *En niños verticales (Romina):* Bite bubbles posteriores sin rellenar para apretar y chafar cada semana + nivelar planos superior e inferior por separado pidiendo un **"salto virtual vertical"** + *Tongue Crib* ("pinchitos") cuando los incisivos hayan salido lo suficiente para llevar ataches de retención.
  * *En adultos (León):* Sobrecorregir el Overbite final en el setup casi al doble (**+3.0 a +4.0 mm**) + **intrusión molar posterior de 0.5 a 1.0 mm** con *occlusal pads* sin cementar (1 mm de intrusión atrás cierra 2.5–3 mm delante por efecto bisagra) + control de la lengua en reposo pidiendo *Tongue Crib* por excepción o colocando **AngelButtons en la cara lingual de los incisivos inferiores**.
- Canteos Oclusales y Política de TADs (David y Romina):
  * David casi no usa TADs para sagital si hay colaboración; los reserva para **canteos e intrusiones verticales**, usando **TADs con cabeza de botón**. En canteos severos: 2 TADs superiores (vestibular y palatino) para intruir el lado descendido + botones directos inferiores con elásticos para extruir el antagonista.
- Mecánicas con AngelButton (TPU, soporta 500 g):
  * El AngelButton reparte la fuerza en bloque por toda la arcada; el botón cementado al diente concentra la fuerza en su raíz (extruyéndolo).
  * En Clase II braquifacial para extruir el molar inferior: **AngelButton en canino superior + botón directo en el 6 inferior + ataches de retención obligatorios en 7 y 5 inferiores** (elásticos 1/4" 4.5 oz).
  * En mordidas cruzadas con AngelButtons: poner siempre **atache de retención en la cara opuesta (palatino/vestibular) y en los dientes vecinos**.
  * Evitar elásticos en caja anteriores (*Anterior Box Elastics*) sobre AngelButtons porque desadaptan el alineador. No pedir el AngelButton hasta la etapa en que empiece a usarse el elástico.
  * En canino alto sin debilitar el plástico: poner **2 AngelButtons en los dientes vecinos + botón directo en el canino alto** y tirar en "tienda de campaña" (3/16" 4.5 oz).
  * **¡ALERTA EN REVISIONES CADA 2 MESES!:** Vigilar con fotos en cada cita porque con el uso constante de elásticos en AngelButtons **las Clases II pasan a Clase III quirúrgica y las Clases III pasan a Clase II**.

5. PROTOCOLOS ESPECÍFICOS POR MALOCLUSIÓN:
- MORDIDA CRUZADA UNILATERAL Y RNO (Romina y David):
  * En mordida cruzada no se cumple la 1ª Ley de Planas (el lado cruzado de menor dimensión vertical queda comprimido en el maxilar y la lengua sufre deformación torsional: ancha y baja en el lado cruzado; estrecha y larga en balanceo).
  * **Secuencia obligatoria en 2 etapas:** 1º Expansión **unilateral exclusiva del lado comprimido** hasta simetrizar con el lado sano -> 2º Expansión **bilateral simétrica** con forma de **arcada cuadrada** y líneas medias 100% centradas en su base ósea.
  * **Rehabilitación:** Masticar **2 años por el lado no cruzado** (para remodelar la trayectoria condílea), tallado selectivo con papel de articular (solo vertientes/rebordes, nunca cúspides), poner la **almohada a los pies de la cama** para cambiar el lado de dormir y verificar paso nasal real (test de aguantar agua 3 min en boca o 15 sentadillas con boca cerrada + ORL para cornetes/amígdalas) antes de usar *mouth tapes*.
- MORDIDA EN TIJERA / BRODIE (David): **1º Corregir primero el Brodie transversalmente** y **2º Corregir después la Clase II sagital** (nunca empezar a distalar sin haber descruzado antes el Brodie).
- EXPANSIÓN CENTRÍFUGA EN DENTICIÓN MIXTA (Sustituto del 2x4 / D-Gainer):
  * 1º Expandir y distalar los 6s a la vez (si están en Clase I, distalar 6 superior e inferior **acompasados a la par** sin que el inferior adelante nunca al superior; si están en Clase II, primero el superior hasta Clase I y luego juntos) -> 2º Distalar y expandir molares de leche -> 3º Alinear incisivos dejando **0.5 mm de espacio en mesial y 0.5 mm en distal de los caninos de leche (espacio de primate)**.
- PSEUDO-DISYUNCIÓN EN NIÑOS PEQUEÑOS (5–6 años, límite hasta salida de 6s y máx. 2 centrales) Y CLASE III INFANTIL (Dr. Reinhardt):
  * Pedir **Pro** cambiando cada **5+5 días**, línea de corte alta (2.5 mm), ataches posteriores muy retentivos y escribir al técnico: *"Simular expansión de disyuntor (~0.2 mm/diente, 4–6 mm totales), dejando la cúspide palatina superior en la fosa inferior y SIN mover ningún diente de forma individual"*.
  * En Clase III infantil temprana (técnica Dr. Reinhardt): poner **levantes posteriores arriba**, dejar **libre de alineador el 6 inferior** para que extruya y posterorrote la mandíbula, y traccionar con **Máscara de Delaire** (prohibida la de Petit de barra central por causar convergencia ocular/diplopía y chocar con las gafas) con elásticos **5/16" de 4.5 o 6.5 oz**.
- PROTOCOLO MARPE + ALINEADORES SEGÚN EDAD Y CBCT (David):
  * Medir en CBCT el Walla Ridge y el ángulo fosa-furca del 6 respecto al suelo nasal (norma Wilson: 95°–100°; >107° = proinclinado).
  * **<16 años:** 2 microimplantes + 2 apoyos dentales (o 4 en 6 y 4 si el 6 está >107°) con apoyos oclusales y **media banda** + tornillo convencional Leone (1 vuelta mañana + 1 noche hasta abrir diastema, luego 1/día).
  * **16–30 años:** 4 microimplantes (Osteogenos cilíndricos cabeza plana, 2 mm x 15–19 mm bicorticales, insertados a 20 rpm y máx. 35–40 N·cm apretando en cruz) + 4 apoyos + **Power Screw hexagonal** (2 vueltas mañana + 2 noche hasta abrir diastema, luego 1+1).
  * **30–40 años:** MARPE de 4 micros + Power Screw + **Corticotomía piezoeléctrica en sillón con 3 mini-incisiones** (2 descargas **perpendiculares** a la sutura palatina —nunca paralelas— y 1 anterior).
  * **Alerta Marca Verde:** El tornillo de 8 mm solo rinde 6 mm reales; avisar al paciente de **parar inmediatamente si ve la marca verde en la espiga**. Tras disyuntar (2 semanas): cortar patas, escanear, poner Essix rápido y pedir alineadores **comprimiendo dentoalveolarmente los premolares sobreexpandidos** para meterlos en su base ósea y cerrando el diastema con **Atache DGZ**.
- AVANCE MANDIBULAR PROTOCOLO A6:
  * Primer pico (5–7 años, C1–C2) o pico prepuberal (CS3–CS4). Salto mínimo de **4 mm** y máximo de **7 mm** (si tiene ~10 mm en niños pequeños, dividir en **2 saltos grandes**: 4 mm y luego el resto; nunca micro-saltitos). Escanear mordida constructiva con el **truco de la bolita de composite** fotopolimerizada en anterior frente al espejo.
  * **SIEMPRE Bloques Tipo 1 rectos** y en dentición mixta **cubriendo como mínimo el 6 inferior definitivo**. Vienen 2 juegos flexibles por etapa (**5+5 días**) + elásticos en AngelButtons (noche en ambos lados, y **tarde en el lado más corto si es asimétrica**). Completar **9 meses** entre Fase I (bloques A6) y Fase II (levante anterior inclinado + elásticos nocturnos).
- PROTOCOLO A8 (DISTALIZACIÓN), CLASE II SUBDIVISIÓN Y CIRUGÍA ORTOGNÁTICA:
  * Extraer 8s previos. Staging en V **1/2** (o **1/3** si se marcan microtornillos en la prescripción; TAD en tuberosidad hacia palatino tirando de botón directo en el 6). En cuanto el 7 llega a su sitio final (en verde), el alineador **viene recortado por distal del 7 y con refuerzo rígido molar** para no perder anclaje.
  * **Regla del 50% Salto Virtual en Clases II largas (40–45 etapas):** Pedir **50% distalización A8 + 50% salto virtual con elásticos**; parar y reescanear para cerrar espacios en cuanto alcance Clase I en boca.
  * **Clase II Subdivisión:** El problema suele ser rotación mandibular hacia el lado de masticación con línea media superior centrada; pedir **"rotar la arcada inferior y centrar la línea media inferior con la superior"**, expandiendo el lado hacia donde rota y usando el espacio distal al canino inferior.
  * **Clase II div 2 en adultos:** Cambiar de TIR a **PIR** (*Proinclinar a ~1.5°/etapa abriendo ligeros diastemas -> Intruir -> Retruir*).
  * **Cirugía Ortognática:** Escanear siempre en **Máxima Intercuspidación (MIC)** (nunca en céntrica). Cumplir los 3 requisitos: dientes en su hueso basal, líneas medias centradas con su hueso y **Curva de Spee 100% plana**. Tomar escaneado superior e inferior por separado justo antes del quirófano y pedir **10 alineadores pasivos** finales.
"""

FRAMEWORK_ANGEL_ALIGNER = FRAMEWORK_BASE.replace("__LISTA_ARCHIVOS__", lista_archivos_disponibles)

# 6. Inicializar el modelo Gemini con baja temperatura para máxima precisión clínica
modelo = genai.GenerativeModel(
    model_name="gemini-flash-lite-latest",
    system_instruction=FRAMEWORK_ANGEL_ALIGNER,
    generation_config={"temperature": 0.15}
)

# 7. Interfaz Principal Optimizada
st.title("🦷 Asistente Clínico de Ortodoncia — Angel Aligner (iOrtho)")
st.caption("Protocolos Clínicos y Auditoría 3D liderados por los Dres. **David González Zamora y Romina Vignolo Lobato**.")

if "chat_angel" not in st.session_state:
    st.session_state.chat_angel = []
if "planificacion_unificada" not in st.session_state:
    st.session_state.planificacion_unificada = ""

tab_unificada, tab_chat = st.tabs([
    "📋🔍 Planificación y Auditoría iOrtho",
    "💬 Chat Clínico y Buscador Visual"
])

# ==============================================================================
# PESTAÑA 1: PLANIFICACIÓN Y AUDITORÍA UNIFICADA (SIN CAMPOS REDUNDANTES)
# ==============================================================================
with tab_unificada:
    col1, col2, col3 = st.columns(3)

    with col1:
        tipo_paciente = st.selectbox(
            "1. Edad / Dentición",
            [
                "Adulto (Dentición permanente - Cortical densa)",
                "Adolescente en crecimiento (Select / Pro)",
                "Adolescente con K1 previo -> KiD K2 (Select Unlimited)",
                "Niño con algún diente de leche -> Angel KiD (K1 - 2 años)",
                "Niño en Crecimiento - Dentición Mixta (Pico 5-7 años / K1)",
                "Niño Pequeño - Dentición Temporal (<6 años - K1 o Pro)"
            ]
        )
        estado_periodontal = st.selectbox(
            "2. Periodonto, STL y Condicionantes",
            [
                "Periodonto sano / Colaborador (Apto Pro 7+3)",
                "Adulto muy complejo / hueso muy duro (Pro 7+5 días)",
                "Paciente Periodontal / Recesiones (PROHIBIDO Pro -> Select Unlimited)",
                "Implantes / Puentes / Round-tripping (SIN línea de corte alta)",
                "Gran desgaste para Rehabilitación (Composites inyectados CBCT+STL)",
                "Niño pequeño (Ataches grandes/colores; NO en leche móviles ni en erupción)",
                "Niño con autismo / hipersensibilidad (Corte alto 2.5mm SIN ataches)"
            ]
        )

    with col2:
        origen_sagital = st.selectbox(
            "3. Diagnóstico y Mecánica Sagital",
            [
                "Neutroclusión / Clase I (Alineación y coordinación)",
                "Clase II Dentoalveolar (Protocolo A8: Staging 1/2 + 50% salto virtual si es largo)",
                "Clase II >= 3 mm con Microtornillos (A8 Staging 1/3 + TAD tuberosidad/palatino)",
                "Clase II Subdivisión / Asimétrica (Rotar arcada inferior y centrar LM inferior)",
                "Clase II Retrusión Mandibular en crecimiento (A6 Bloques Tipo 1 rectos cubriendo el 6)",
                "Clase II leve (OJ < 3 mm) o Fase II post-A6 (Levantes anteriores inclinados)",
                "Discrepancia mixta / Expansión Centrífuga (Distalar + Expandir + Protruir + 0.5mm primate)",
                "Clase III en crecimiento (Máscara Delaire + Corte alto 2.5mm + Técnica Dr. Reinhardt)",
                "Clase III compensable adulto/adolescente (Pro 7+3 + A8 inferior sin 8s + Elásticos CIII)",
                "Extracción de Premolares (Protocolo A7 + Atache DGZ + Medio Póntico)",
                "Preparación Cirugía Ortognática (Escaneo en MIC, Spee plana y 10 etapas pasivas)"
            ]
        )
        problema_transversal = st.selectbox(
            "4. Diagnóstico y Mecánica Transversal",
            [
                "Arcadas simétricas / Coordinación estándar",
                "Compresión dentoalveolar simétrica (Expansión + control torque + Arcada cuadrada)",
                "Mordida cruzada UNILATERAL DERECHA (1º Expandir lado derecho -> 2º Bilateral)",
                "Mordida cruzada UNILATERAL IZQUIERDA (1º Expandir lado izquierdo -> 2º Bilateral)",
                "Compresión esquelética niño 5-6 años (Pseudo-disyunción Pro 5+5 días + corte alto)",
                "Compresión esquelética <16 años (MARPE 2 micros + 2 apoyos media banda + Leone)",
                "Compresión esquelética 16-30 años (MARPE 4 micros Osteogenos + 4 apoyos + Power Screw)",
                "Compresión esquelética 30-40 años (MARPE 4 micros + Power Screw + Piezo 3 incisiones)",
                "Cierre post-MARPE con diastema (Atache DGZ en centrales + comprimir premolares)",
                "Mordida en tijera / Brodie (1º Descruzar Brodie transversal -> 2º Corregir sagital)"
            ]
        )

    with col3:
        problema_vertical = st.selectbox(
            "5. Biotipo, Plano Vertical y Torque Incisivo",
            [
                "Mesofacial / Sobremordida y Torque normales",
                "Braquifacial / Sobremordida aumentada (Levantes curvos adaptativos 3 a 3 sin cementar)",
                "Clase II div 2 / Retroinclinados (Protocolo PIR o Torque Ridge + HBO centro + corte alto después)",
                "Intrusión anterior > 2.5 mm en adulto (Área intrusión + retención vecinos + Frog Staging 8+8)",
                "Mordida borde a borde / Salto CIII (Levantes anteriores adaptativos hacia incisal)",
                "Dolicofacial / Mordida abierta en niño (Bite bubbles posteriores para apretar + Salto virtual)",
                "Mordida abierta en adulto (Sobrecorregir OB a +3/+4mm + Intrusión molar 0.5-1mm + Botones linguales)",
                "Canteo del plano oclusal (Levantes post. lado bajo + TADs cabeza de botón + elásticos inf.)"
            ]
        )
        habitos_atm = st.multiselect(
            "6. Hábitos, Vía Aérea y Postura (RNO)",
            [
                "Respirador oral (Test 3 min agua / ORL cornetes antes de tapes)",
                "Lengua baja / torsional (Posicionador Lingual + Logopeda)",
                "Interposición lingual / Deglución atípica (Tongue Crib / Botones linguales)",
                "Duerme boca abajo / apoya mano u hombro (Almohada a los pies)",
                "Masticación unilateral (Comer 2 años por el lado no cruzado)",
                "Envoltura restringida (Kois) / Bruxismo / Sobrecarga ATM"
            ]
        )

    col_up, col_notas = st.columns([1.15, 1.0])
    with col_up:
        capturas_iortho = st.file_uploader(
            "📸 Capturas de iOrtho (`Tabla TM`, `Bolton`, `Anchura`, `OB/OJ`, `MovE`) o fotos del caso:",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True
        )
    with col_notas:
        notas_unificadas = st.text_area(
            "📝 Notas clínicas puntuales (ausencias, canino alto, diente para altura protésica, etc.):",
            height=105,
            placeholder="Ej: Ausencia del 42, canino 13 alto sin espacio, laterales superiores pequeños..."
        )

    imagenes_pil = []
    if capturas_iortho:
        cols_img = st.columns(min(len(capturas_iortho), 5))
        for i, archivo in enumerate(capturas_iortho):
            img_opt = preparar_imagen_para_ia(archivo)
            imagenes_pil.append(img_opt)
            with cols_img[i % 5]:
                st.image(img_opt, caption=archivo.name, use_container_width=True)

    if st.button("🚀 Generar Planificación Biomecánica e Instrucciones para iOrtho", type="primary", use_container_width=True):
        habitos_str = ", ".join(habitos_atm) if habitos_atm else "Ninguno reportado"
        modo_analisis = (
            "AUDITORÍA DE CAPTURAS DE iORTHO + DIAGNÓSTICO CLÍNICO: Extrae todos los números de las capturas adjuntas (OB/OJ, Bolton, Anchura 3-3 a 6-6, etapas/IPR/puntos rojos en MovE y valores críticos en Corona/CR/Ápice de la Tabla TM) y crúzalos con la selección clínica."
            if imagenes_pil
            else "PLANIFICACIÓN INICIAL DESDE CERO: No hay capturas de iOrtho adjuntas; diseña la estrategia inicial completa marcando los objetivos exactos."
        )

        prompt_unificado = f"""
MODO DE EJECUCIÓN: {modo_analisis}

SELECCIÓN CLÍNICA DEL DOCTOR:
- Edad / Dentición: {tipo_paciente}
- Periodonto / STL / Condicionantes: {estado_periodontal}
- Diagnóstico y Mecánica Sagital: {origen_sagital}
- Diagnóstico y Mecánica Transversal: {problema_transversal}
- Biotipo, Vertical y Torque: {problema_vertical}
- Hábitos, Vía Aérea y Postura (RNO): {habitos_str}
- Notas adicionales: {notas_unificadas if notas_unificadas else 'Ninguna'}

Responde DIRECTAMENTE (sin introducciones ni saludos) con estos 5 bloques concisos y ejecutables:

### 1. 🔍 Lectura y Auditoría Crítica del Setup (Tabla TM, MovE, Anchura, Bolton y OB/OJ)
- Si hay capturas adjuntas: resume en viñetas telegráficas los datos leídos en **OB/OJ** (inicial vs final, alertando si OB sube a ~3mm en retrusiones o si falta sobrecorregir a +3/+4mm en mordida abierta, y si con el OJ inicial hay riesgo de morder detrás del levante anterior en céntrica), **Bolton** (ausencias `—`/`X`), **Anchura 3-3 a 6-6** (alertar colapso intercanino), **MovE** (etapas, puntos rojos —recordar mirar por palatino— y si los rombos de IPR coinciden con las citas 7, 13, 19...) y lista diente por diente las alertas de la **Tabla TM** (amarillas y blancas que superen límites en Rotación >12-15°, Torque >8-10°, Tip >4°, Extrusión/Intrusión).
- Si no hay capturas: define en 3 líneas los límites de seguridad de OB/OJ, anchura y secuenciación para este caso.

### 2. 📦 Sistema Angel Aligner, Línea de Corte y Pauta de Citas
- Producto exacto, régimen de cambio de días (`10 días`, `7+3`, `7+5` o `5+5` en A6/pseudo-disyunción), Línea de Corte (Festoneada, Alta 2.5mm o Mixta; requisito >=5mm encía en STL y contraindicaciones aplicables) y protocolo de revisiones cada 6 alineadores (2 meses).

### 3. ⚙️ Estrategia Biomecánica 3D (Transversal, Sagital, Vertical y RNO)
- **Transversal:** Secuencia exacta (unilateral del lado comprimido primero vs bilateral hasta arcada cuadrada y líneas medias centradas; o protocolo MARPE por edad + marca verde + compresión premolar post-MARPE; o descruzar Brodie antes de Clase II).
- **Sagital:** Ejecución exacta del protocolo elegido (A6 con Bloques Tipo 1 rectos cubriendo como mínimo el 6 inferior definitivo, salto >=4mm, bolita de composite y 9 meses en 2 fases; o A8 con staging 1/2 o 1/3, recorte distal automático del 7 y 50% salto virtual si es largo; o rotación de arcada inferior en subdivisión; o Expansión Centrífuga con 0.5mm de primate; o Cirugía Ortognática en MIC con Spee plana y 10 pasivos).
- **Vertical y Miofuncional/RNO:** Levantes sin cementar, *Frog Staging* 8+8, PIR vs TIR, TADs con cabeza de botón si aplican, y pautas de rehabilitación (2 años masticando por el lado no cruzado, almohada a los pies, lengua torsional y test nasal).

### 4. 🎯 Mapa Diente por Diente de Ataches, Áreas de Presión y Elásticos
- Detalla en lista directa: dónde colocar **Atache DGZ** (talla M gingival + S incisal, nunca en incisivos inferiores), dónde colocar **HBO** (incisal para extruir vs centro coronal para torque, quitando *Power Ridges* de laterales caucásicos), atache de retención en incisivos inferiores para extruir o en vecinos para intruir, y posición exacta de **AngelButtons / Botones directos** con medidas de elásticos (alertando de vigilar cada 2 meses que la Clase II no pase a Clase III). Cita entre paréntesis los archivos `.jpg` de referencia.

### 5. 📋 Orden Directa para Copiar y Pegar al Técnico CAD en iOrtho
Escribe el texto exacto para el técnico CAD de iOrtho DENTRO DE UN BLOQUE DE CÓDIGO (```text ... ```), numerado punto por punto, en español claro y sin abreviaturas confusas.
"""
        with st.spinner("Auditando datos y generando planificación biomecánica..."):
            try:
                contenido_envio = [prompt_unificado] + imagenes_pil
                respuesta_uni = modelo.generate_content(contenido_envio)
                st.session_state.planificacion_unificada = respuesta_uni.text
            except Exception as e:
                st.error(f"Error de conexión con Google Gemini: {e}")

    if st.session_state.planificacion_unificada:
        st.markdown("---")
        st.markdown(st.session_state.planificacion_unificada)
        st.download_button(
            label="📥 Descargar Planificación e Instrucciones (.txt)",
            data=st.session_state.planificacion_unificada,
            file_name="Planificacion_iOrtho_AngelAligner.txt",
            mime="text/plain"
        )
        mostrar_fotos_referencia(st.session_state.planificacion_unificada)

# ==============================================================================
# PESTAÑA 2: CHAT CLÍNICO Y BUSCADOR VISUAL CONECTADO AL CASO ACTUAL
# ==============================================================================
with tab_chat:
    st.subheader("💬 Ajuste Fino del Caso y Buscador Visual del 'Ladrillo'")
    st.caption(
        "El chat recuerda automáticamente la planificación recién generada en la Pestaña 1. "
        "Pídele cualquier modificación rápida o consulta una lámina gráfica."
    )

    for msg in st.session_state.chat_angel:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["texto"])
            if msg["rol"] == "assistant":
                mostrar_fotos_referencia(msg["texto"])

    pregunta_chat = st.chat_input("Ej: 'Modifícame la orden al técnico para distalar solo el 1º cuadrante' o 'Enséñame la imagen del atache DGZ'...")

    if pregunta_chat:
        st.session_state.chat_angel.append({"rol": "user", "texto": pregunta_chat})
        with st.chat_message("user"):
            st.markdown(pregunta_chat)

        with st.chat_message("assistant"):
            try:
                historial_api = []
                if st.session_state.planificacion_unificada:
                    historial_api.append({
                        "role": "model",
                        "parts": [f"Planificación actual del paciente en memoria:\n{st.session_state.planificacion_unificada}"]
                    })
                for m in st.session_state.chat_angel[:-1]:
                    historial_api.append({
                        "role": "user" if m["rol"] == "user" else "model",
                        "parts": [m["texto"]]
                    })
                chat = modelo.start_chat(history=historial_api)
                resp = chat.send_message(pregunta_chat)
                st.markdown(resp.text)
                mostrar_fotos_referencia(resp.text)
                st.session_state.chat_angel.append({"rol": "assistant", "texto": resp.text})
            except Exception as e:
                st.error(f"Error de conexión con Google Gemini: {e}")
