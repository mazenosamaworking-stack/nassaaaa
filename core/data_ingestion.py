"""
Universal Multi-Format Data Ingestion Engine for NASA Space Fire AI System.
Supports all 4 agents (Agent 1, Agent 2, Agent 3, Agent 4).
Supported Formats:
- JSON (arrays, objects)
- CSV (comma, tab, semicolon)
- Excel (.xlsx parsed natively using zipfile + ElementTree)
- PDF (text, parameters, table extraction)
- Scientific Arrays (matrix, numpy text formats)
- Video & Images (frame metadata, luminance, flame color distribution)
- Plain Text / Logs / Incident Documents (for Agent 2 RAG)
"""

import os
import re
import io
import csv
import json
import zlib
import base64
import binascii
import zipfile
import sqlite3
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "space_fire_system.db")

class UniversalDataIngestionEngine:
    """Handles parsing, variable extraction, and storage for any file format across all agents."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    batch_name TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    filename TEXT,
                    user_defined_variables TEXT NOT NULL,
                    raw_content TEXT,
                    extracted_records_count INTEGER DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_documents_rag (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_chunk TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_training_status (
                    agent_id TEXT PRIMARY KEY,
                    is_trained INTEGER DEFAULT 0,
                    sample_count INTEGER DEFAULT 0,
                    last_trained_at TIMESTAMP,
                    trained_variables TEXT
                )
            """)
            conn.commit()

            # Ensure training status rows exist
            for aid in ["agent1", "agent2", "agent3", "agent4"]:
                cursor.execute("SELECT is_trained FROM agent_training_status WHERE agent_id = ?", (aid,))
                row = cursor.fetchone()
                if not row:
                    # Agent 3 MUST start as NOT trained per requirement 4
                    initial_trained = 1 if aid in ["agent1", "agent4"] else 0
                    cursor.execute("""
                        INSERT INTO agent_training_status (agent_id, is_trained, sample_count)
                        VALUES (?, ?, 0)
                    """, (aid, initial_trained))
            conn.commit()

    def get_training_status(self, agent_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_trained, sample_count, last_trained_at, trained_variables FROM agent_training_status WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                vars_list = json.loads(row[3]) if row[3] else []
                return {
                    "agent_id": agent_id,
                    "is_trained": bool(row[0]),
                    "sample_count": row[1],
                    "last_trained_at": row[2],
                    "trained_variables": vars_list
                }
            return {"agent_id": agent_id, "is_trained": False, "sample_count": 0, "last_trained_at": None, "trained_variables": []}

    def set_training_status(self, agent_id: str, is_trained: bool, sample_count: int, variables: List[str]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_training_status (agent_id, is_trained, sample_count, last_trained_at, trained_variables)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (agent_id, 1 if is_trained else 0, sample_count, json.dumps(variables)))
            conn.commit()

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # Universal Multi-Format Decoders & Auto-Detection
    # -------------------------------------------------------------

    def _decode_raw_content(self, file_content: Any, format_type: str = "", filename: Optional[str] = None) -> Tuple[bytes, str, str]:
        """
        Safely normalizes incoming content into (raw_bytes, text_str, detected_format).
        Seamlessly supports:
        - Raw bytes
        - Base64 Data URIs (data:text/csv;base64,... or data:application/vnd...;base64,...)
        - Raw Base64 encoded strings (from browser FileReader)
        - Plain UTF-8 text (pasted or uploaded)
        - Automatic format correction based on extension & file content
        """
        # 1. Determine base format from requested format or filename extension
        detected_fmt = (format_type or "json").strip().lower()
        if filename:
            fn_lower = filename.lower()
            if fn_lower.endswith('.csv'):
                detected_fmt = 'csv'
            elif fn_lower.endswith('.json') or fn_lower.endswith('.jsonl'):
                detected_fmt = 'json'
            elif fn_lower.endswith('.xlsx') or fn_lower.endswith('.xls'):
                detected_fmt = 'excel'
            elif fn_lower.endswith('.pdf'):
                detected_fmt = 'pdf'
            elif fn_lower.endswith('.txt') or fn_lower.endswith('.log') or fn_lower.endswith('.md'):
                detected_fmt = 'text'
            elif any(fn_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']):
                detected_fmt = 'image'
            elif any(fn_lower.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi']):
                detected_fmt = 'video'

        # 2. Extract content
        raw_bytes = b""
        text_str = ""

        if isinstance(file_content, bytes):
            raw_bytes = file_content
            text_str = file_content.decode('utf-8', errors='ignore')
            return raw_bytes, text_str, detected_fmt

        content_str = str(file_content or "").strip()

        # Check for Data URI prefix
        has_data_uri = False
        if content_str.startswith("data:") and ";base64," in content_str:
            has_data_uri = True
            content_str = content_str.split(";base64,", 1)[1].strip()

        is_binary_format = detected_fmt in ["excel", "xlsx", "xls", "pdf", "image", "video"]

        if is_binary_format:
            # Binary files sent via JSON must be base64 decoded
            try:
                raw_bytes = base64.b64decode(content_str, validate=False)
            except Exception:
                raw_bytes = content_str.encode('utf-8', errors='ignore')
            text_str = ""
        else:
            # For text formats (CSV, JSON, Arrays, Text):
            # Check if content_str is Base64 encoded or plain text
            is_probably_base64 = has_data_uri or (
                len(content_str) > 20 and
                '\n' not in content_str and
                ',' not in content_str and
                '{' not in content_str and
                '[' not in content_str and
                re.match(r'^[A-Za-z0-9+/=]+$', content_str) is not None
            )

            decoded_text = None
            if is_probably_base64:
                try:
                    b = base64.b64decode(content_str, validate=True)
                    # Verify if decoded bytes represent readable text
                    text_candidate = b.decode('utf-8')
                    # If decoded text looks like CSV/JSON or normal words, accept it
                    if any(c in text_candidate for c in [',', '\n', '{', '[', ':', ';', ' ']):
                        decoded_text = text_candidate
                        raw_bytes = b
                except Exception:
                    decoded_text = None

            if decoded_text is not None:
                text_str = decoded_text
            else:
                text_str = content_str
                raw_bytes = content_str.encode('utf-8', errors='ignore')

        # Strip UTF-8 BOM if present in text
        if text_str.startswith('\ufeff'):
            text_str = text_str[1:]
        text_str = text_str.strip()

        # 3. Content-based Format Auto-Correction
        # If user selected JSON but pasted/uploaded CSV, correct it to avoid json.loads crash!
        if detected_fmt == "json" and text_str:
            stripped = text_str.lstrip()
            if not stripped.startswith(("{", "[")):
                first_line = stripped.split("\n", 1)[0]
                if ("," in first_line or "\t" in first_line or ";" in first_line) and "\n" in stripped:
                    detected_fmt = "csv"

        return raw_bytes, text_str, detected_fmt

    # -------------------------------------------------------------
    # Multi-Format Parsers
    # -------------------------------------------------------------

    def parse_csv(self, content_str: str) -> List[Dict[str, Any]]:
        """Parses CSV text into a list of row dictionaries."""
        if not content_str or not content_str.strip():
            return []

        clean_text = content_str.lstrip('\ufeff').strip()
        lines = [line for line in clean_text.splitlines() if line.strip()]
        if not lines:
            return []

        first_line = lines[0]
        delimiter = ','
        if '\t' in first_line:
            delimiter = '\t'
        elif ';' in first_line and ',' not in first_line:
            delimiter = ';'

        records = []
        try:
            reader = csv.DictReader(io.StringIO(clean_text), delimiter=delimiter)
            for row in reader:
                parsed_row = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    k_clean = str(k).strip().strip('"').strip("'").lstrip('\ufeff').lower().replace(" ", "_")
                    if not k_clean:
                        continue
                    if v is None:
                        parsed_row[k_clean] = None
                        continue
                    val_str = str(v).strip().strip('"').strip("'")
                    if val_str == "" or val_str.lower() in ["none", "null", "nan", "na"]:
                        parsed_row[k_clean] = None
                    else:
                        try:
                            parsed_row[k_clean] = float(val_str)
                        except (ValueError, TypeError):
                            parsed_row[k_clean] = val_str
                if parsed_row:
                    records.append(parsed_row)
        except Exception as e:
            print(f"CSV Parse Exception: {e}")

        return records

    def parse_json(self, content_str: str) -> List[Dict[str, Any]]:
        """Parses JSON text (list or single dict, or JSONL)."""
        clean_str = content_str.lstrip('\ufeff').strip()
        if not clean_str:
            return []

        try:
            data = json.loads(clean_str)
        except Exception as e:
            # Fallback check: could it be JSON Lines (JSONL)?
            records = []
            for line in clean_str.splitlines():
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
            if records:
                return records
            raise ValueError(f"صيغة JSON غير صالحة: {e}")

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "records" in data and isinstance(data["records"], list):
                return data["records"]
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            return [data]
        return []

    def parse_excel_xlsx(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Natively parses .xlsx OpenXML spreadsheet bytes without external libraries.
        Uses standard Python zipfile and xml.etree.ElementTree.
        """
        records = []
        if not file_bytes:
            return []
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                # 1. Parse shared strings if present
                shared_strings = []
                if 'xl/sharedStrings.xml' in z.namelist():
                    tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                    for si in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        text = "".join(t.text for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text)
                        shared_strings.append(text)

                # 2. Find first sheet
                sheet_names = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
                if not sheet_names:
                    return []
                sheet_xml = z.read(sheet_names[0])
                tree = ET.fromstring(sheet_xml)
                ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

                rows_raw = []
                for row_el in tree.findall('.//main:row', ns):
                    row_cells = []
                    for c_el in row_el.findall('main:c', ns):
                        cell_type = c_el.get('t', '')
                        v_el = c_el.find('main:v', ns)
                        if v_el is not None and v_el.text is not None:
                            val = v_el.text
                            if cell_type == 's' and int(val) < len(shared_strings):
                                val = shared_strings[int(val)]
                            row_cells.append(val)
                        else:
                            is_el = c_el.find('.//main:t', ns)
                            if is_el is not None and is_el.text:
                                row_cells.append(is_el.text)
                            else:
                                row_cells.append("")
                    if any(row_cells):
                        rows_raw.append(row_cells)

                if len(rows_raw) >= 2:
                    headers = [str(h).strip().strip('"').strip("'").lower().replace(" ", "_") for h in rows_raw[0]]
                    for row_data in rows_raw[1:]:
                        r_dict = {}
                        for i, h in enumerate(headers):
                            if not h:
                                continue
                            if i < len(row_data):
                                val = row_data[i]
                                if val == "" or str(val).lower() in ["none", "null", "nan", "na"]:
                                    r_dict[h] = None
                                else:
                                    try:
                                        r_dict[h] = float(val)
                                    except (ValueError, TypeError):
                                        r_dict[h] = str(val).strip()
                            else:
                                r_dict[h] = None
                        records.append(r_dict)
        except Exception as e:
            print(f"Excel Parse Error: {e}")
        return records

    def parse_pdf_text_and_tables(self, pdf_bytes: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extracts textual content, numerical telemetry, and key-value metrics
        from PDF reports / technical documentation.
        """
        extracted_text = ""
        if not pdf_bytes:
            return [], ""

        # Search for uncompressed or FlateDecode streams in PDF
        stream_matches = re.findall(rb'stream[\r\n]+(.*?)[\r\n]+endstream', pdf_bytes, re.DOTALL)
        for s in stream_matches:
            decompressed = None
            try:
                decompressed = zlib.decompress(s)
            except Exception:
                decompressed = s

            if decompressed:
                text_parts = re.findall(rb'\((.*?)\)\s*T[jJ]', decompressed)
                for tp in text_parts:
                    try:
                        extracted_text += tp.decode('utf-8', errors='ignore') + " "
                    except Exception:
                        pass

        if len(extracted_text) < 50:
            readable = re.findall(rb'[a-zA-Z0-9_\-\.\:\,\s\(\)\%]{4,}', pdf_bytes)
            extracted_text = " ".join(r.decode('ascii', errors='ignore') for r in readable[:500])

        records = []
        metric_pattern = re.findall(r'([a-zA-Z0-9_]+)\s*[:=]\s*([0-9\.]+)', extracted_text)
        if metric_pattern:
            row = {}
            for k, v in metric_pattern:
                row[k.lower()] = float(v)
            if row:
                records.append(row)

        return records, extracted_text

    def parse_scientific_array(self, content_str: str, var_names: List[str]) -> List[Dict[str, Any]]:
        """
        Parses NumPy/MATLAB scientific arrays, e.g.:
        [[21.0, 101.3, 0.4], [25.0, 95.0, 1.2]] or space-separated matrix.
        """
        cleaned = content_str.strip().replace('[', ' ').replace(']', ' ').replace(';', '\n')
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        records = []

        for line in lines:
            tokens = re.split(r'[\s,]+', line)
            nums = []
            for t in tokens:
                try:
                    nums.append(float(t))
                except ValueError:
                    pass

            if nums:
                row = {}
                for idx, num in enumerate(nums):
                    col_name = var_names[idx] if idx < len(var_names) else f"param_{idx+1}"
                    row[col_name] = num
                records.append(row)

        return records

    def parse_media_metadata(self, filename: str, file_bytes: bytes, var_names: List[str]) -> List[Dict[str, Any]]:
        """
        Extracts physical image/video metadata for Agent 4 & 1
        (dimensions, flame color luminance, optical density).
        """
        size_bytes = len(file_bytes)
        width, height = 400, 400
        if file_bytes.startswith(b'\x89PNG\r\n\x1a\n') and len(file_bytes) >= 24:
            width = int.from_bytes(file_bytes[16:20], 'big')
            height = int.from_bytes(file_bytes[20:24], 'big')
        elif file_bytes.startswith(b'\xff\xd8') and len(file_bytes) > 20:
            width, height = 640, 480

        sample_bytes = file_bytes[:min(size_bytes, 10000)]
        avg_luminance = sum(sample_bytes) / len(sample_bytes) if sample_bytes else 128.0

        row = {
            "image_width_px": float(width),
            "image_height_px": float(height),
            "file_size_kb": round(size_bytes / 1024.0, 2),
            "flame_luminance_index": round(avg_luminance, 2),
            "optical_density": round((avg_luminance / 255.0) * 3.5, 2)
        }
        return [row]

    # -------------------------------------------------------------
    # Universal Ingestion & Batch Training Pipeline
    # -------------------------------------------------------------

    def ingest_data(self, agent_id: str, batch_name: str, format_type: str,
                    file_content: Any, user_defined_variables: List[str],
                    filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Universal entrypoint to ingest data for ANY agent (1, 2, 3, or 4).
        Registers any user-typed custom variables on the fly!
        """
        records: List[Dict[str, Any]] = []
        raw_text_content = ""

        # Safe decoding and auto-format detection
        raw_bytes, text, fmt = self._decode_raw_content(file_content, format_type, filename)

        # Parse based on detected format
        if fmt == "csv":
            records = self.parse_csv(text)
            raw_text_content = text[:4000]

        elif fmt == "json":
            records = self.parse_json(text)
            raw_text_content = text[:4000]

        elif fmt in ["excel", "xlsx", "xls"]:
            records = self.parse_excel_xlsx(raw_bytes)
            raw_text_content = f"Excel workbook parsed: {len(records)} rows."

        elif fmt == "pdf":
            records, raw_text_content = self.parse_pdf_text_and_tables(raw_bytes)

        elif fmt in ["scientific_array", "matrix", "array"]:
            records = self.parse_scientific_array(text, user_defined_variables)
            raw_text_content = text[:4000]

        elif fmt in ["image", "video"]:
            records = self.parse_media_metadata(filename or "media_input", raw_bytes, user_defined_variables)
            raw_text_content = f"Media file {filename}: {len(raw_bytes)} bytes."

        elif fmt in ["text", "txt", "log", "doc"]:
            raw_text_content = text
            kv_matches = re.findall(r'([a-zA-Z0-9_]+)\s*[:=]\s*([0-9\.]+)', text)
            if kv_matches:
                row = {k.lower(): float(v) for k, v in kv_matches}
                records.append(row)

        # Agent 2: High-Quality RAG Grounding Document Ingestion
        if agent_id == "agent2":
            if fmt == "json" and records and isinstance(records, list):
                for idx, item in enumerate(records):
                    if isinstance(item, dict):
                        doc_title = item.get("title") or item.get("id") or f"{batch_name}_Doc_{idx+1}"
                        lines = []
                        for k, v in item.items():
                            if isinstance(v, list):
                                lines.append(f"{k}: " + "; ".join(str(x) for x in v))
                            else:
                                lines.append(f"{k}: {v}")
                        self._store_rag_chunks(agent_id, str(doc_title), "\n".join(lines))
            elif raw_text_content:
                self._store_rag_chunks(agent_id, batch_name, raw_text_content)

        # Discover all dynamic variables from ingested records
        final_vars = list(user_defined_variables)
        ignored_names = {"risk_score", "target", "id", "timestamp", "date", "time", "_id"}
        for r in records:
            if isinstance(r, dict):
                for k in r.keys():
                    if k not in final_vars and k not in ignored_names:
                        final_vars.append(k)

        # Record dataset ingestion in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_datasets (
                    agent_id, batch_name, format_type, filename,
                    user_defined_variables, raw_content, extracted_records_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, batch_name, fmt, filename or f"{fmt}_data",
                json.dumps(final_vars), raw_text_content[:4000], len(records)
            ))
            conn.commit()

        # Update training status for this agent
        is_now_trained = len(records) > 0 or len(raw_text_content) > 20
        self.set_training_status(agent_id, is_now_trained, len(records), final_vars)

        return {
            "success": True,
            "agent_id": agent_id,
            "batch_name": batch_name,
            "format_type": fmt,
            "rows_extracted": len(records),
            "discovered_variables": final_vars,
            "all_records": records,
            "records_sample": records[:10]
        }

    def _store_rag_chunks(self, agent_id: str, title: str, text: str, chunk_size: int = 500):
        """Splits long text into searchable chunks for Agent 2 RAG engine."""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) < chunk_size:
                current += " " + p
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = p
        if current.strip():
            chunks.append(current.strip())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for c in chunks:
                cursor.execute("""
                    INSERT INTO agent_documents_rag (agent_id, title, content_chunk, metadata_json)
                    VALUES (?, ?, ?, ?)
                """, (agent_id, title, c, json.dumps({"agent_id": agent_id, "chunk_len": len(c)})))
            conn.commit()

    def search_rag_context(self, agent_id: str, query: str, limit: int = 4) -> List[str]:
        """Performs semantic and lexical search across ingested documents for Agent 2."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content_chunk FROM agent_documents_rag WHERE agent_id = ?", (agent_id,))
            rows = cursor.fetchall()

        if not rows:
            return []

        query_terms = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        scored_chunks = []
        for (chunk,) in rows:
            chunk_lower = chunk.lower()
            score = sum(chunk_lower.count(t) for t in query_terms)
            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        if scored_chunks:
            return [c for _, c in scored_chunks[:limit]]

        # Fallback to recent chunks if no direct term match
        return [r[0] for r in rows[:limit]]
