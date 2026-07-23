"""Generate deterministic, clearly fictional binary fixtures for the public demo."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from openpyxl import Workbook
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "examples" / "synthetic_export"

CONTACTS_CSV = """name,email,phone,address
Avery North,avery.north@example.com,+1 (202) 555-0147,"1847 Example Street, Apt 5B"
Morgan Vale,morgan.vale@example.net,+1 (202) 555-0188,"22 Sample Road"
"""

PROFILE_JSON = {
    "profile": {
        "display_name": "Avery North",
        "email": "avery.north@example.com",
        "phone": "+1 (202) 555-0147",
        "government_id": "899-12-3456",
        "china_id_style": "990000199001010018",
    },
    "export_notes": {
        "address": "1847 Example Street, Apt 5B",
        "scope": "All values in this export are deterministic fiction.",
    },
}

NOTES_TEXT = """SYNTHETIC SECURITY REVIEW — NO REAL CREDENTIALS

The disclosure copy accidentally retained these intentionally non-working examples:
aws_access_key = AKIAIOSFODNN7EXAMPLE
github_token = ghp_000000000000000000000000000000000000
test_card = 4111 1111 1111 1111

The repeated contact is avery.north@example.com.
"""

DOCX_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml"
    ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>
"""

DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    Target="docProps/core.xml"/>
</Relationships>
"""

DOCX_CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
 xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Synthetic disclosure brief</dc:title>
  <dc:creator>Avery North — avery.north@example.com</dc:creator>
  <cp:lastModifiedBy>Morgan Vale</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z</dcterms:created>
</cp:coreProperties>
"""

DOCX_DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Synthetic disclosure review</w:t></w:r></w:p>
    <w:p><w:r><w:t>Contact Avery at avery.north@example.com.</w:t></w:r></w:p>
    <w:p><w:r><w:t>Remove 1847 Example Street before sharing.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def _write_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        entries = {
            "[Content_Types].xml": DOCX_CONTENT_TYPES,
            "_rels/.rels": DOCX_RELS,
            "docProps/core.xml": DOCX_CORE,
            "word/document.xml": DOCX_DOCUMENT,
        }
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content.encode("utf-8"))


def _write_xlsx(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Synthetic contacts"
    worksheet.append(["Field", "Value"])
    worksheet.append(["Contact", "avery.north@example.com"])
    worksheet.append(["Phone", "+1 (202) 555-0147"])
    worksheet.append(["Test card", "4111111111111111"])
    workbook.properties.creator = "Avery North"
    workbook.properties.lastModifiedBy = "Morgan Vale"
    workbook.properties.title = "Synthetic privacy audit workbook"
    workbook.save(path)
    workbook.close()


def _write_image(path: Path) -> None:
    image = Image.new("RGB", (960, 540), "#0a1715")
    draw = ImageDraw.Draw(image)
    draw.rectangle((52, 52, 908, 488), outline="#8fffc1", width=4)
    draw.text((88, 96), "SYNTHETIC EXPORT PHOTO", fill="#8fffc1")
    draw.text((88, 150), "EXIF contains fictional authorship and GPS.", fill="#dff7ef")
    draw.text((88, 204), "No real person or place is represented.", fill="#91a9a1")
    exif = Image.Exif()
    exif[270] = "Synthetic contact avery.north@example.com"
    exif[315] = "Avery North — synthetic fixture"
    exif[33432] = "CC0-1.0 synthetic fixture"
    exif[34853] = {
        1: "N",
        2: (31.0, 13.0, 49.44),
        3: "E",
        4: (121.0, 28.0, 25.32),
    }
    image.save(path, format="JPEG", quality=88, optimize=False, exif=exif)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate() -> None:
    resolved_root = ROOT.resolve()
    resolved_target = TARGET.resolve()
    if resolved_root not in resolved_target.parents:
        raise RuntimeError("sample target escaped the repository")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    (TARGET / "contacts.csv").write_text(CONTACTS_CSV, encoding="utf-8", newline="\n")
    (TARGET / "profile.json").write_text(
        json.dumps(PROFILE_JSON, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (TARGET / "review-notes.txt").write_text(NOTES_TEXT, encoding="utf-8", newline="\n")
    (TARGET / "README.txt").write_text(
        "All names, identifiers, addresses, credentials, metadata, and images in this folder "
        "are deterministic fictional test data. License: CC0-1.0.\n",
        encoding="utf-8",
        newline="\n",
    )
    (TARGET / "LICENSE.txt").write_text(
        "The synthetic fixtures in this directory are dedicated to the public domain under "
        "CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_docx(TARGET / "disclosure-brief.docx")
    _write_xlsx(TARGET / "contact-register.xlsx")
    _write_image(TARGET / "field-photo.jpg")

    manifest = {
        "dataset": "Data XRay Local deterministic synthetic export",
        "license": "CC0-1.0",
        "real_personal_data": False,
        "files": [
            {"path": path.name, "sha256": _sha256(path)}
            for path in sorted(TARGET.iterdir())
            if path.name != "MANIFEST.json"
        ],
    }
    (TARGET / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    generate()
