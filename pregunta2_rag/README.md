# Pregunta 2 - RAG documental con PostgreSQL y pgvector

## Funcionalidad implementada

- Carga de PDF con texto seleccionable y control de 300 páginas por archivo / 900 en total.
- Página física numerada desde 1, registro de páginas sin texto y errores de lectura.
- Fragmentación con solapamiento y embeddings multilingües de 384 dimensiones.
- Persistencia de documentos, páginas, fragmentos y vectores en PostgreSQL con pgvector.
- Idempotencia por SHA-256: reingestar un archivo idéntico no duplica documentos ni fragmentos.
- Búsqueda vectorial conjunta o filtrada por documento.
- Generación en español con Amazon Bedrock, Ollama u OpenAI; instrucciones estrictas para citar y declarar evidencia insuficiente.
- Presentación de pasajes recuperados con documento, página y puntuación.

## Ejecución

```bash
cp .env.example .env
docker compose up --build
```

La primera codificación descargará el modelo multilingüe. Abra `http://localhost:8001`.

### Opción local con Ollama

Instale Ollama en el host y ejecute:

```bash
ollama pull llama3.2:3b
ollama serve
```

Use `GENERATOR_PROVIDER=ollama`. En Linux puede requerirse agregar `extra_hosts: ["host.docker.internal:host-gateway"]` al servicio web.

### Opción por API

Use `GENERATOR_PROVIDER=openai`, configure `OPENAI_API_KEY` y, si corresponde, cambie `OPENAI_MODEL`. La clave no debe versionarse.

### Opción AWS con Amazon Bedrock

Use `GENERATOR_PROVIDER=bedrock`, `AWS_REGION=us-east-2` y `BEDROCK_MODEL=us.amazon.nova-lite-v1:0`. El código usa la API Converse, fija `BEDROCK_MAX_TOKENS=800` y reintentos adaptativos. En EC2 no se guardan keys: boto3 obtiene credenciales temporales del rol de instancia, que necesita `bedrock:InvokeModel`.

## Pruebas de aceptación

1. Cargar tres PDF; verificar que cada documento muestre sus páginas y fragmentos.
2. Repetir la carga de uno; confirmar que los conteos no cambian.
3. Reiniciar `docker compose`; confirmar que los documentos siguen disponibles.
4. Preguntar por los tres documentos y luego filtrar uno.
5. Verificar que cada afirmación relevante incluya `[documento, p. N]` y que los pasajes mostrados correspondan.
6. Formular una pregunta fuera del contenido; la respuesta debe indicar que la evidencia es insuficiente.
7. Probar un PDF con página vacía o dañada; revisar los contadores de páginas sin texto y errores.

## Evidencias sugeridas

- `SELECT COUNT(*) FROM documents;` y `SELECT COUNT(*) FROM chunks;` antes y después de reingestar.
- `CREATE EXTENSION vector` y esquema de tablas.
- pantalla con respuesta, citas y pasajes.
- reinicio de contenedores manteniendo el volumen `rag_db`.
