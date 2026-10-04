#!/usr/bin/env python3
"""Costa Rica Urban Home - servidor 100% local, sin base de datos externa."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import secrets
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
UPLOADS_DIR = ROOT / "uploads"
STATIC_DIR = ROOT / "static"
PROPERTIES_FILE = DATA_DIR / "properties.json"
ADMIN_PIN = os.environ.get("ADMIN_PIN", "1703")
MAX_UPLOAD = 10 * 1024 * 1024
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")

DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

DEFAULT_PROPERTIES = [
    {"id":"p1","title_es":"Villa de Lujo con Vista al Volcán Arenal","title_en":"Luxury Villa with Arenal Volcano View","price":385000,"type":"Villa","location":"La Fortuna","beds":3,"baths":3.5,"area":"2,400 m²","image":"/static/images/villa.svg","desc":"Espectacular propiedad rodeada de naturaleza tropical. Cuenta con piscina privada, acabados elegantes y vista despejada al Volcán Arenal. Ideal para residencia o inversión turística.","desc_en":"Spectacular property surrounded by tropical nature. Features a private pool, elegant finishes and unobstructed Arenal Volcano views. Ideal as a residence or tourism investment.","featured":True,"status":"active"},
    {"id":"p2","title_es":"Quinta Campestre con Río en San Carlos","title_en":"Countryside Estate with River in San Carlos","price":215000,"type":"Finca","location":"San Carlos","beds":4,"baths":2,"area":"5,000 m²","image":"/static/images/farm.svg","desc":"Hermosa quinta con casa principal, jardines, árboles frutales y acceso a río. Un lugar privado para vivir rodeado de naturaleza.","desc_en":"Beautiful countryside estate with a main house, gardens, fruit trees and river access. A private place to live surrounded by nature.","featured":True,"status":"active"},
    {"id":"p3","title_es":"Lote Listo para Construir","title_en":"Build-Ready Lot","price":85000,"type":"Terreno","location":"San Carlos","beds":0,"baths":0,"area":"850 m²","image":"/static/images/land.svg","desc":"Terreno plano con servicios, acceso pavimentado y excelente ubicación para construir una residencia o inversión.","desc_en":"Flat lot with utilities, paved access and an excellent location for a residence or investment.","featured":True,"status":"active"},
    {"id":"p4","title_es":"Casa Moderna Familiar de 2 Plantas","title_en":"Modern 2-Story Family Home","price":195000,"type":"Casa","location":"Valle Central","beds":3,"baths":2.5,"area":"320 m²","image":"/static/images/modern.svg","desc":"Casa contemporánea con espacios amplios, cocina moderna, cochera y patio. Excelente opción familiar.","desc_en":"Contemporary home with spacious areas, modern kitchen, garage and patio. An excellent family option.","featured":False,"status":"active"},
    {"id":"p5","title_es":"Casa Tropical Cerca de la Playa","title_en":"Tropical Home Near the Beach","price":295000,"type":"Casa","location":"Playa / Costa","beds":3,"baths":2,"area":"1,100 m²","image":"/static/images/beach.svg","desc":"Propiedad tropical con amplias terrazas, jardines y ambiente relajado cerca de la costa.","desc_en":"Tropical property with large terraces, gardens and a relaxed atmosphere near the coast.","featured":True,"status":"active"},
    {"id":"p6","title_es":"Residencia Premium con Piscina","title_en":"Premium Residence with Pool","price":450000,"type":"Villa","location":"San Carlos","beds":4,"baths":3.5,"area":"1,800 m²","image":"/static/images/pool.svg","desc":"Residencia de alto nivel con piscina, áreas sociales y jardines diseñados para disfrutar y recibir invitados.","desc_en":"High-end residence with pool, social areas and landscaped gardens designed for entertaining.","featured":True,"status":"active"},
    {"id":"p7","title_es":"Finca con Montaña y Naturaleza","title_en":"Mountain Estate Surrounded by Nature","price":325000,"type":"Finca","location":"La Fortuna","beds":3,"baths":2,"area":"8,500 m²","image":"/static/images/mountain.svg","desc":"Amplia finca con vistas montañosas, senderos, jardines y espacio para desarrollar un proyecto turístico.","desc_en":"Large estate with mountain views, trails, gardens and room for a tourism project.","featured":False,"status":"active"},
    {"id":"p8","title_es":"Casa Elegante con Jardines Tropicales","title_en":"Elegant Home with Tropical Gardens","price":275000,"type":"Casa","location":"San Carlos","beds":3,"baths":2.5,"area":"1,250 m²","image":"/static/images/garden.svg","desc":"Casa elegante rodeada de jardines tropicales, terraza y espacios cómodos para la familia.","desc_en":"Elegant home surrounded by tropical gardens, a terrace and comfortable family spaces.","featured":False,"status":"active"},
]


def load_properties():
    if not PROPERTIES_FILE.exists():
        save_properties(DEFAULT_PROPERTIES)
    try:
        data = json.loads(PROPERTIES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        save_properties(DEFAULT_PROPERTIES)
        return list(DEFAULT_PROPERTIES)


def save_properties(properties):
    tmp = PROPERTIES_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(properties, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PROPERTIES_FILE)


def clean_filename(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-")[:50] or "property"
    ext = Path(name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    return f"{stem}-{secrets.token_hex(6)}{ext}"


def parse_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length > 2 * 1024 * 1024:
        raise ValueError("La solicitud es demasiado grande.")
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def parse_multipart(handler):
    content_type = handler.headers.get("Content-Type", "")
    boundary_match = re.search(r"boundary=(?:\"([^\"]+)\"|([^;]+))", content_type)
    if not boundary_match:
        raise ValueError("Formulario multipart inválido.")
    boundary = (boundary_match.group(1) or boundary_match.group(2)).encode()
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0 or length > MAX_UPLOAD + 1024 * 1024:
        raise ValueError("La imagen no es válida o supera 10 MB.")
    body = handler.rfile.read(length)
    delimiter = b"--" + boundary
    fields = {}
    for part in body.split(delimiter):
        part = part.strip(b"\r\n-")
        if not part or b"\r\n\r\n" not in part:
            continue
        header_bytes, content = part.split(b"\r\n\r\n", 1)
        headers = header_bytes.decode("utf-8", "replace")
        disposition = re.search(r'Content-Disposition:\s*form-data;\s*name="([^"]+)"(?:;\s*filename="([^"]*)")?', headers, re.I)
        if not disposition:
            continue
        name, filename = disposition.group(1), disposition.group(2)
        if filename is not None:
            ctype = re.search(r"Content-Type:\s*([^\r\n]+)", headers, re.I)
            fields[name] = {"filename": filename, "content_type": (ctype.group(1).strip() if ctype else "application/octet-stream"), "content": content}
        else:
            fields[name] = content.decode("utf-8", "replace")
    return fields


class Handler(BaseHTTPRequestHandler):
    server_version = "CRUH-Python/1.0"

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {fmt % args}")

    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        return secrets.compare_digest(self.headers.get("X-Admin-PIN", ""), ADMIN_PIN)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            return self.serve_file(ROOT / "index.html", "text/html; charset=utf-8")
        if path == "/api/health":
            return self.send_json({"ok": True, "storage": "local JSON + local files"})
        if path == "/api/properties":
            return self.send_json({"properties": load_properties()})
        if path.startswith("/api/"):
            return self.send_json({"error": "Not found"}, 404)
        return self.serve_public(path)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/admin/verify":
                data = parse_json(self)
                pin = str(data.get("pin", "")).strip()
                return self.send_json({"ok": secrets.compare_digest(pin, ADMIN_PIN)})
            if path == "/api/upload-image":
                if not self.authorized():
                    return self.send_json({"error": "Unauthorized"}, 403)
                fields = parse_multipart(self)
                image = fields.get("image")
                if not isinstance(image, dict):
                    return self.send_json({"error": "No se recibió la imagen."}, 400)
                content = image["content"]
                if len(content) == 0 or len(content) > MAX_UPLOAD:
                    return self.send_json({"error": "La imagen debe pesar 10 MB o menos."}, 400)
                ctype = image["content_type"].lower()
                allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
                if ctype not in allowed:
                    return self.send_json({"error": "Solo se permiten imágenes JPG, PNG, WEBP o GIF."}, 400)
                filename = clean_filename(image["filename"])
                target = UPLOADS_DIR / filename
                target.write_bytes(content)
                return self.send_json({"ok": True, "url": f"/uploads/{filename}"})
            if path == "/api/properties":
                if not self.authorized():
                    return self.send_json({"error": "Unauthorized"}, 403)
                p = parse_json(self)
                required = ["id", "title_es", "title_en", "price", "type", "location", "image"]
                if any(not p.get(k) for k in required):
                    return self.send_json({"error": "Faltan campos obligatorios."}, 400)
                properties = load_properties()
                if any(str(x.get("id")) == str(p["id"]) for x in properties):
                    return self.send_json({"error": "El ID de la propiedad ya existe."}, 409)
                properties.insert(0, p)
                save_properties(properties)
                return self.send_json({"ok": True, "properties": properties}, 201)
            return self.send_json({"error": "Not found"}, 404)
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 500)

    def do_PUT(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/properties/"):
            return self.send_json({"error": "Not found"}, 404)
        if not self.authorized():
            return self.send_json({"error": "Unauthorized"}, 403)
        try:
            pid = path.rsplit("/", 1)[-1]
            data = parse_json(self)
            properties = load_properties()
            found = next((p for p in properties if str(p.get("id")) == pid), None)
            if not found:
                return self.send_json({"error": "Propiedad no encontrada."}, 404)
            found["status"] = data.get("status", "active")
            save_properties(properties)
            return self.send_json({"ok": True, "properties": properties})
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 500)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/properties/"):
            return self.send_json({"error": "Not found"}, 404)
        if not self.authorized():
            return self.send_json({"error": "Unauthorized"}, 403)
        try:
            pid = path.rsplit("/", 1)[-1]
            properties = load_properties()
            target = next((p for p in properties if str(p.get("id")) == pid), None)
            if not target:
                return self.send_json({"error": "Propiedad no encontrada."}, 404)
            properties = [p for p in properties if str(p.get("id")) != pid]
            save_properties(properties)
            image = str(target.get("image", ""))
            if image.startswith("/uploads/"):
                file_path = UPLOADS_DIR / Path(image).name
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
            return self.send_json({"ok": True, "properties": properties})
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 500)

    def serve_public(self, path):
        rel = path.lstrip("/")
        if ".." in Path(rel).parts:
            return self.send_json({"error": "Not found"}, 404)
        candidates = [ROOT / rel]
        if rel.startswith("static/"):
            candidates.append(STATIC_DIR / rel.removeprefix("static/"))
        if rel.startswith("uploads/"):
            candidates.append(UPLOADS_DIR / rel.removeprefix("uploads/"))
        for file_path in candidates:
            if file_path.is_file():
                return self.serve_file(file_path)
        return self.send_json({"error": "Not found"}, 404)

    def serve_file(self, file_path: Path, content_type=None):
        try:
            raw = file_path.read_bytes()
        except OSError:
            return self.send_json({"error": "Not found"}, 404)
        ctype = content_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(raw)


def main():
    if not PROPERTIES_FILE.exists():
        save_properties(DEFAULT_PROPERTIES)
    print("=" * 58)
    print("COSTA RICA URBAN HOME - SERVIDOR PYTHON LOCAL")
    print(f"PIN DEL PROPIETARIO: {ADMIN_PIN}")
    print(f"Sitio: http://127.0.0.1:{PORT}")
    print("Para publicar en internet, usa HOST=0.0.0.0 y PORT=el-puerto-del-host.")
    print("=" * 58)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
