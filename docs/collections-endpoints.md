# Endpoints de Colecciones

El módulo `collections` permite agrupar series de tiempo por dimensiones conceptuales (ej: IPC por región, categoría COICOP, etc.) y consultarlas de forma estructurada.

Base URL: `/collections/`

---

## GET `/collections/get_series/`

Busca series que coincidan con una colección, un concepto y/o filtros de dimensiones.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `collection_id` | string | No | ID de la colección (ej: `ipc`) |
| `concept_id` | string | No | ID del concepto (ej: `indec:ipc-indice`) |
| `dimensiones[<nombre>]` | string o lista | No | Filtra por valor de una dimensión. Se puede repetir para múltiples dimensiones o múltiples valores. |
| `mode` | string | No | Si es `data`, devuelve los datos temporales de las series encontradas en lugar de su metadata |
| `start_date` | string | Solo con `mode=data` | Fecha de inicio (ej: `2020-01-01`) |
| `end_date` | string | Solo con `mode=data` | Fecha de fin |
| `collapse` | string | Solo con `mode=data` | Colapso temporal: `day`, `month`, `quarter`, `year` |
| `collapse_aggregation` | string | Solo con `mode=data` | Función de agregación: `avg`, `sum`, `min`, `max`, `end_of_period` |
| `representation_mode` | string | Solo con `mode=data` | Modo de representación: `value`, `change`, `pct_change`, `change_since_beginning_of_year`, `pct_change_since_beginning_of_year` |
| `limit` | int | Solo con `mode=data` | Límite de filas en la respuesta |
| `start` | int | Solo con `mode=data` | Offset para paginación |

### Respuesta sin `mode=data`

Devuelve los objetos de metadata de las series encontradas (hasta 100 resultados).

```json
{
  "result": [
    {
      "id": "146.1_IPC_EQUIPANAL_DICI_T_46",
      "collection": "ipc",
      "concept": "indec:ipc-indice",
      "dimensions": [
        {"name": "region", "value": "nacional"},
        {"name": "clasificacion_coicop", "value": "coicop:muebles-conservacion-hogar"}
      ]
    }
  ]
}
```

### Respuesta con `mode=data`

Devuelve la respuesta estándar de la API de series de tiempo con los datos temporales de las series encontradas.

### Errores posibles

| Código | Descripción |
|---|---|
| `collection_not_found` | La colección indicada no existe. Incluye lista de colecciones disponibles. |
| `concept_not_found` | El concepto indicado no existe (o no pertenece a la colección indicada). Incluye lista de conceptos disponibles. |
| `invalid_dimensions` | Una o más dimensiones no existen en el concepto indicado. |
| `invalid_values` | Uno o más valores no son válidos para sus dimensiones. |

### Advertencias posibles

| Código | Descripción |
|---|---|
| `incompatible_dimensions` | Las dimensiones solicitadas no son compatibles entre sí. La búsqueda se ejecuta con el subconjunto compatible más grande. Incluye las dimensiones usadas y las compatibilidades disponibles. |

### Ejemplos

**Buscar todas las series de una colección:**
```
GET /collections/get_series/?collection_id=ipc
```

**Buscar series de un concepto específico con filtro de dimensión:**
```
GET /collections/get_series/?collection_id=ipc&concept_id=indec:ipc-indice&dimensiones[region]=nacional
```

**Múltiples valores para una dimensión:**
```
GET /collections/get_series/?concept_id=indec:ipc-indice&dimensiones[region]=nacional&dimensiones[region]=patagonia
```

**Obtener datos temporales con colapso anual:**
```
GET /collections/get_series/?collection_id=ipc&concept_id=indec:ipc-indice&dimensiones[region]=nacional&mode=data&collapse=year&collapse_aggregation=avg&start_date=2017-01-01
```

---

## GET `/collections/get_details/`

Devuelve la metadata completa de series específicas identificadas por su `field_id`.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `ids` | string | Sí | Uno o más `field_id` separados por coma |

### Respuesta

```json
{
  "series": [
    {
      "id": "146.1_IPC_EQUIPANAL_DICI_T_46",
      "collection": "ipc",
      "concept": "indec:ipc-indice",
      "dimensions": [
        {"name": "region", "value": "nacional"},
        {"name": "clasificacion_coicop", "value": "coicop:muebles-conservacion-hogar"}
      ]
    }
  ]
}
```

### Ejemplo

```
GET /collections/get_details/?ids=146.1_IPC_EQUIPANAL_DICI_T_46,146.1_IPC_VAR_DICI_T_23
```

---

## GET `/collections/all_collections/`

Lista todas las colecciones disponibles.

### Parámetros

Ninguno.

### Respuesta

```json
{
  "collections": [
    {"id": "ipc", "nombre": "Índice de Precios al Consumidor"},
    {"id": "pbi", "nombre": "Producto Bruto Interno"}
  ]
}
```

### Ejemplo

```
GET /collections/all_collections/
```

---

## GET `/collections/all_concepts/`

Lista todos los conceptos disponibles, con opción de filtrar por colección.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `collection_id` | string | No | Filtra los conceptos por colección |

### Respuesta

```json
{
  "concepts": [
    {
      "id": "indec:ipc-indice",
      "nombre": "IPC Índice",
      "collection_id": "ipc"
    },
    {
      "id": "indec:ipc-variacion",
      "nombre": "IPC Variación",
      "collection_id": "ipc"
    }
  ]
}
```

### Ejemplo

```
GET /collections/all_concepts/?collection_id=ipc
```

---

## GET `/collections/get_collection/`

Devuelve el detalle de una o más colecciones, incluyendo sus conceptos.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `ids` | string | Sí | Uno o más IDs de colección separados por coma |

### Respuesta

```json
{
  "collections": [
    {
      "id": "ipc",
      "nombre": "Índice de Precios al Consumidor",
      "descripcion": "Series del IPC publicadas por el INDEC.",
      "concepts": [
        {"id": "indec:ipc-indice", "nombre": "IPC Índice"},
        {"id": "indec:ipc-variacion", "nombre": "IPC Variación"}
      ]
    }
  ]
}
```

### Ejemplo

```
GET /collections/get_collection/?ids=ipc,pbi
```

---

## GET `/collections/get_concept/`

Devuelve el detalle de uno o más conceptos, incluyendo sus dimensiones y compatibilidades.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `ids` | string | Sí | Uno o más IDs de concepto separados por coma |

### Respuesta

```json
{
  "concepts": [
    {
      "id": "indec:ipc-indice",
      "nombre": "IPC Índice",
      "descripcion": "Índice de precios al consumidor base diciembre 2016.",
      "collection_id": "ipc",
      "dimensiones": [
        {
          "id": "region",
          "nombre": "Región estadística",
          "valores_posibles": ["nacional", "gba", "pampeana", "noroeste", "noreste", "cuyo", "patagonia"]
        },
        {
          "id": "clasificacion_coicop",
          "nombre": "Clasificación COICOP",
          "valores_posibles": ["coicop:nivel-general", "coicop:alimentos-bebidas-no-alcoholicas"]
        }
      ],
      "dimensiones_compatibles": [
        ["region"],
        ["clasificacion_coicop"],
        ["region", "clasificacion_coicop"]
      ]
    }
  ]
}
```

El campo `dimensiones_compatibles` lista los grupos de dimensiones que pueden combinarse en una misma consulta a `get_series`. Si se piden dimensiones fuera de un grupo compatible, el endpoint emite una advertencia y usa el subconjunto compatible más grande.

### Ejemplo

```
GET /collections/get_concept/?ids=indec:ipc-indice
```

---

## POST `/collections/unstack/`

Convierte un CSV con datos tabulares y un YAML de configuración en archivos listos para ser cargados como colección.

### Body (multipart/form-data)

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `csv_file` | archivo | Sí | CSV con columna de fecha, columnas descriptivas y columnas numéricas. Soporta encodings UTF-8, UTF-8-BOM, ISO-8859-1, latin1, cp1252. |
| `yaml_file` | archivo | Sí | YAML de configuración con las claves descritas abajo |

### Estructura del YAML

```yaml
# Columnas del CSV
date_col: fecha                    # columna de fechas (ISO 8601 o año entero)
descri_cols:                       # columnas descriptivas — una por dimensión
  - region_estadistica
  - clasificacion_coicop
div_col: ninguno                   # columna divisora para partir en múltiples datasets;
                                   # usar "ninguno" si no aplica

# Metadata de la colección
collection_id: ipc
collection_name: Índice de Precios al Consumidor
collection_description: Indicadores del IPC publicados por el INDEC.   # opcional

# Conceptos: uno por columna numérica del CSV
concepts:
  - id: indic:ipc-indice
    name: IPC Índice
    description: Número índice base diciembre 2016=100.   # opcional
    num_col: valor_indice

  - id: indic:ipc-variacion-mensual
    name: IPC Variación mensual
    num_col: variacion_mensual

# Combinaciones de dimensiones válidas para consultar juntas (opcional)
variables_compatibles:
  - [region_estadistica, clasificacion_coicop]
  - [region_estadistica]
```

### Respuesta

Devuelve un archivo ZIP con los siguientes contenidos:

| Archivo | Descripción |
|---|---|
| `collection.json` | Definición de la colección lista para cargar en el admin |
| `series_concept.json` | Mapeo de IDs de serie generados a colección, concepto y dimensiones |
| `df_<valor>.csv` | Uno o más CSVs con las series en formato wide, uno por valor de `div_col` (o uno solo si `div_col` es `ninguno`) |

### Ejemplo

```
POST /collections/unstack/
Content-Type: multipart/form-data

csv_file=@datos_ipc.csv
yaml_file=@config_ipc.yaml
```

---

---

## Setup para administradores

### Cargar colecciones

Las colecciones se pueden cargar de dos formas:

1. **Desde el admin Django** (`/admin/` → sección Collections): subir un archivo JSON con el formato descrito abajo. Ver `docs/collections_ipc_emae.json` como ejemplo completo.

2. **Generando el archivo con `/collections/unstack/`**: el ZIP resultante incluye un `collection.json` listo para subir al admin.

### Formato del archivo de colecciones

```json
{
  "collections": [
    {
      "id": "ipc",
      "nombre": "Índice de Precios al Consumidor",
      "descripcion": "Descripción de la colección.",
      "concepts": [
        {
          "id": "indic:ipc-indice",
          "nombre": "IPC Índice",
          "descripcion": "Descripción del concepto.",
          "variables": [
            {
              "id": "region_estadistica",
              "nombre": "Región estadística",
              "valores_posibles": ["Nacional", "AMBA", "Pampeana", "NOA", "NEA", "Cuyo", "Patagonia"]
            },
            {
              "id": "clasificacion_coicop",
              "nombre": "Clasificación COICOP",
              "valores_posibles": ["01-Alimentos y bebidas no alcohólicas", "02-Bebidas alcohólicas y tabaco"]
            }
          ],
          "variables_compatibles": [
            ["region_estadistica", "clasificacion_coicop"],
            ["region_estadistica"]
          ]
        }
      ]
    }
  ]
}
```

### Requisitos en el catálogo para que las series se indexen como parte de una colección

Para que una serie quede asociada a una colección al indexarse desde el catálogo, debe tener en su metadata de distribución:

- `field_specialType`: `"time_series"`
- `field_specialTypeDetails`: un objeto JSON con la clave `series_concept`:

```json
{
  "series_concept": {
    "collection": "ipc",
    "concept": "indic:ipc-indice",
    "dimensions": [
      {"name": "region_estadistica", "value": "Nacional"},
      {"name": "clasificacion_coicop", "value": "01-Alimentos y bebidas no alcohólicas"}
    ]
  }
}
```

La colección y el concepto referenciados deben estar cargados en la base de datos **antes** de indexar. Si no existen, la serie se indexa normalmente pero sin quedar vinculada a ninguna colección.

---

## Errores comunes

Todos los endpoints devuelven errores con el siguiente formato:

```json
{"error": "Descripción del error"}
```

O, en el caso de validación de `get_series`, con múltiples errores:

```json
{
  "errors": [
    {
      "code": "collection_not_found",
      "message": "La colección 'xyz' no existe.",
      "colecciones_disponibles": ["ipc", "pbi"]
    }
  ]
}
```

Los endpoints `get_details`, `get_collection` y `get_concept` devuelven lista vacía (no error 404) cuando ningún ID coincide.
