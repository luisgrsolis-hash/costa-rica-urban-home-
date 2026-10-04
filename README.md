# Costa Rica Urban Home — versión Python local / publicable

Esta versión no usa Supabase, PostgreSQL, SQLite, claves API ni una base de datos externa.

## Qué incluye

- Sitio web completo con Python.
- Servidor HTTP usando solamente la biblioteca estándar de Python.
- Propiedades guardadas en `data/properties.json`.
- Imágenes nuevas guardadas en `uploads/`.
- 12 imágenes locales de muestra en `static/images/`.
- 8 propiedades de muestra.
- Español / English.
- USD / CRC.
- Acceso de propietario con PIN `1703`.
- Agregar propiedades.
- Subir imágenes JPG, PNG, WEBP o GIF de hasta 10 MB.
- Marcar propiedades como vendidas o disponibles.
- Eliminar propiedades.
- Galería visual.
- Diseño responsive.
- `Procfile` incluido para hosts que acepten aplicaciones Python.

## Ejecutar en PyCharm

1. Abre esta carpeta en PyCharm.
2. Abre `run.py`.
3. Ejecuta `run.py`.
4. El navegador abrirá `http://127.0.0.1:8000`.
5. Entra al panel de propietario con `1703`.

No necesitas instalar paquetes con pip.

## Publicar en internet

El servidor está preparado para escuchar en `0.0.0.0` y usar la variable `PORT` que entregue el proveedor de hosting.

El `Procfile` usa:

```text
web: python server.py
```

La carpeta completa debe subirse al servicio de hosting de Python que elijas.

### Importante sobre el almacenamiento

Como pediste una versión sin base de datos externa, las propiedades se guardan en un archivo JSON local. Esto funciona perfectamente en un servidor con almacenamiento persistente, VPS o hosting que conserve el disco. Algunos servicios serverless/efímeros pueden borrar archivos locales al reiniciar o redeplegar; en esos servicios las propiedades nuevas podrían perderse.

## Seguridad

El PIN del propietario es `1703`. El panel administrativo está protegido en el servidor por ese PIN.

Para un sitio comercial con muchos usuarios, conviene posteriormente migrar el almacenamiento a una base de datos persistente y usar autenticación de usuarios. Esta versión mantiene deliberadamente tu requisito de no utilizar base de datos externa.
