import io
import os
import sys
import zipfile
from datetime import datetime

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse

from backend.config import CLASS_NAMES
from backend.utils.image_processor import process_image
from backend.utils.model_loader import classifier

router = APIRouter()

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

# ── Font cached at module level (register once per process) ──────────────────
_FONT: str | None = None
_FONT_B: str | None = None


def _get_font() -> tuple[str, str]:
    global _FONT, _FONT_B
    if _FONT is not None:
        return _FONT, _FONT_B

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    windir = os.environ.get("WINDIR", "C:/Windows") if sys.platform == "win32" else ""
    candidates = []
    if windir:
        candidates.append((f"{windir}/Fonts/arial.ttf", f"{windir}/Fonts/arialbd.ttf"))
    candidates += [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    for reg_path, bold_path in candidates:
        if os.path.exists(reg_path):
            try:
                pdfmetrics.registerFont(TTFont("EcoScanF",     reg_path))
                pdfmetrics.registerFont(TTFont("EcoScanF-Bold",
                                               bold_path if os.path.exists(bold_path) else reg_path))
                _FONT, _FONT_B = "EcoScanF", "EcoScanF-Bold"
                return _FONT, _FONT_B
            except Exception:
                pass

    _FONT, _FONT_B = "Helvetica", "Helvetica-Bold"
    return _FONT, _FONT_B


# ── Thumbnail helper ──────────────────────────────────────────────────────────

def _make_thumbnail(img_bytes: bytes, size: int = 90) -> bytes:
    """Return JPEG bytes of a square thumbnail (white-padded)."""
    from PIL import Image as PILImage
    img = PILImage.open(io.BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((size, size), PILImage.LANCZOS)
    bg = PILImage.new("RGB", (size, size), (255, 255, 255))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    bg.paste(img, offset)
    out = io.BytesIO()
    bg.save(out, format="JPEG", quality=75)
    out.seek(0)
    return out.getvalue()


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/batch-classify")
async def batch_classify(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".zip"):
        return JSONResponse({"error": "Vui long tai len file .zip!"}, status_code=400)

    try:
        contents = await file.read()
    except Exception as e:
        return JSONResponse({"error": f"Khong doc duoc file: {e}"}, status_code=400)

    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as zf:
            image_names = [
                n for n in zf.namelist()
                if os.path.splitext(n)[1].lower() in ALLOWED_EXTENSIONS
                and not n.startswith("__MACOSX")
                and not os.path.basename(n).startswith(".")
            ]

            if not image_names:
                return JSONResponse(
                    {"error": "Khong tim thay anh trong ZIP! Ho tro: JPG, PNG, WEBP, BMP"},
                    status_code=400,
                )

            results = []
            for name in image_names:
                basename = os.path.basename(name)
                raw = zf.read(name)
                try:
                    tensor = process_image(raw)
                    pred_class, confidence = classifier.predict(tensor)
                    thumb = _make_thumbnail(raw)
                    results.append({
                        "filename":   basename,
                        "class":      pred_class,
                        "class_name": CLASS_NAMES.get(pred_class, pred_class),
                        "confidence": confidence,
                        "thumb":      thumb,
                        "ok":         True,
                    })
                except Exception:
                    results.append({
                        "filename":   basename,
                        "class":      None,
                        "class_name": "Loi xu ly",
                        "confidence": 0,
                        "thumb":      None,
                        "ok":         False,
                    })

    except zipfile.BadZipFile:
        return JSONResponse({"error": "File ZIP khong hop le hoac bi hong!"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Loi xu ly ZIP: {e}"}, status_code=500)

    try:
        pdf_buf = _build_pdf(results)
    except Exception as e:
        return JSONResponse({"error": f"Loi tao bao cao PDF: {e}"}, status_code=500)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=EcoScan_Report_{ts}.pdf"},
    )


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(results: list) -> io.BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable, Image as RLImage, Paragraph,
        SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    font, font_b = _get_font()

    # Colours
    C_GREEN  = colors.HexColor("#2D5F3F")
    C_GLIGHT = colors.HexColor("#E8F5E9")
    C_GMID   = colors.HexColor("#A5D6A7")
    C_TEAL   = colors.HexColor("#0F766E")
    C_TLIGHT = colors.HexColor("#CCFBF1")
    C_RED    = colors.HexColor("#DC2626")
    C_RLIGHT = colors.HexColor("#FEF2F2")
    C_GRAY   = colors.HexColor("#6B7280")
    C_BORDER = colors.HexColor("#E5E7EB")
    WHITE    = colors.white

    # Stats
    total    = len(results)
    organic  = sum(1 for r in results if r["class"] == "O")
    recycle  = sum(1 for r in results if r["class"] == "R")
    ok_list  = [r for r in results if r["ok"]]
    avg_conf = (sum(r["confidence"] for r in ok_list) / len(ok_list)) if ok_list else 0

    # Style helper
    _cnt = [0]

    def ps(size, bold=False, color=colors.black, align="LEFT"):
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        _cnt[0] += 1
        return ParagraphStyle(
            name=f"_eco_{_cnt[0]}",
            fontName=font_b if bold else font,
            fontSize=size,
            textColor=color,
            alignment={"LEFT": TA_LEFT, "CENTER": TA_CENTER, "RIGHT": TA_RIGHT}.get(align, TA_LEFT),
            leading=size * 1.45,
        )

    def p(text, **kw):
        return Paragraph(text, ps(**kw))

    # Image cell helper
    IMG_W = 1.8 * cm
    IMG_H = 1.8 * cm

    def img_cell(thumb_bytes):
        if not thumb_bytes:
            return p("-", size=9, color=C_GRAY, align="CENTER")
        return RLImage(io.BytesIO(thumb_bytes), width=IMG_W, height=IMG_H)

    buf    = io.BytesIO()
    PAGE_W = A4[0] - 3.6 * cm   # ≈ 17.4 cm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2*cm,    bottomMargin=2*cm,
    )
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(p("EcoScan", size=26, bold=True, color=C_GREEN, align="CENTER"))
    story.append(Spacer(1, 4))
    story.append(p("Bao cao Phan loai Rac thai Hang loat",
                   size=12, bold=True, color=C_GRAY, align="CENTER"))
    story.append(Spacer(1, 4))
    story.append(p(datetime.now().strftime("Ngay tao: %d/%m/%Y   %H:%M:%S"),
                   size=9, color=C_GRAY, align="CENTER"))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=C_GREEN))
    story.append(Spacer(1, 14))

    # ── Summary cards ────────────────────────────────────────────────────────
    cw = (PAGE_W - 9) / 4

    def card_para(val, label, tc=C_GREEN):
        _cnt[0] += 1
        return Paragraph(
            f'<font size="20"><b>{val}</b></font><br/><font size="9">{label}</font>',
            ParagraphStyle(name=f"_card_{_cnt[0]}", fontName=font,
                           textColor=tc, alignment=1, leading=15),
        )

    summary = Table(
        [[card_para(total,              "Tong anh"),
          card_para(organic,            "Rac huu co"),
          card_para(recycle,            "Rac tai che", C_TEAL),
          card_para(f"{avg_conf:.1f}%", "Do tin cay TB")]],
        colWidths=[cw] * 4,
        rowHeights=[62],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0), C_GLIGHT),
        ("BACKGROUND",    (1,0), (1,0), C_GLIGHT),
        ("BACKGROUND",    (2,0), (2,0), C_TLIGHT),
        ("BACKGROUND",    (3,0), (3,0), C_GLIGHT),
        ("BOX",           (0,0), (0,0), 0.6, C_GMID),
        ("BOX",           (1,0), (1,0), 0.6, C_GMID),
        ("BOX",           (2,0), (2,0), 0.6, colors.HexColor("#99F6E4")),
        ("BOX",           (3,0), (3,0), 0.6, C_GMID),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(summary)
    story.append(Spacer(1, 18))

    # ── Detail table ─────────────────────────────────────────────────────────
    # Columns: STT | Anh | Ten file | Ket qua | Do tin cay | Nhom
    # Widths:  1.0  2.0   5.2        3.2        2.7          3.3  = 17.4 cm
    COL_W = [1.0*cm, 2.1*cm, 5.2*cm, 3.2*cm, 2.6*cm, 3.3*cm]

    story.append(p("Chi tiet ket qua", size=11, bold=True, color=C_GREEN))
    story.append(Spacer(1, 8))

    rows = [[
        p("STT",        size=8, bold=True, color=WHITE, align="CENTER"),
        p("Anh",        size=8, bold=True, color=WHITE, align="CENTER"),
        p("Ten file",   size=8, bold=True, color=WHITE),
        p("Ket qua",    size=8, bold=True, color=WHITE, align="CENTER"),
        p("Do tin cay", size=8, bold=True, color=WHITE, align="CENTER"),
        p("Nhom",       size=8, bold=True, color=WHITE, align="CENTER"),
    ]]

    ROW_H = IMG_H + 0.4 * cm   # row height fits thumbnail

    for i, r in enumerate(results, 1):
        fname = r["filename"][:40]
        thumb = img_cell(r.get("thumb"))

        if not r["ok"]:
            rows.append([
                p(str(i),      size=8, align="CENTER"),
                thumb,
                p(fname,       size=8),
                p("Loi xu ly", size=8, color=C_RED,  align="CENTER"),
                p("-",         size=8, color=C_GRAY, align="CENTER"),
                p("-",         size=8, color=C_GRAY, align="CENTER"),
            ])
        elif r["class"] == "O":
            rows.append([
                p(str(i),                        size=8, align="CENTER"),
                thumb,
                p(fname,                         size=8),
                p("Rac huu co",                  size=8, color=C_GREEN, align="CENTER"),
                p(f"{r['confidence']:.1f}%",     size=8, color=C_GREEN, align="CENTER"),
                p("Huu co",                      size=8, color=C_GREEN, align="CENTER"),
            ])
        else:
            rows.append([
                p(str(i),                        size=8, align="CENTER"),
                thumb,
                p(fname,                         size=8),
                p("Rac tai che",                 size=8, color=C_TEAL, align="CENTER"),
                p(f"{r['confidence']:.1f}%",     size=8, color=C_TEAL, align="CENTER"),
                p("Tai che",                     size=8, color=C_TEAL, align="CENTER"),
            ])

    # Build row heights list: header + data rows
    row_heights = [0.7*cm] + [ROW_H] * len(results)

    tbl = Table(rows, colWidths=COL_W, rowHeights=row_heights, repeatRows=1)

    tbl_style = [
        ("BACKGROUND",    (0,0), (-1,0),  C_GREEN),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
        ("LINEBELOW",     (0,0), (-1,0),  1.2, C_GREEN),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    ]
    for i, r in enumerate(results, 1):
        bg = C_RLIGHT if not r["ok"] else C_GLIGHT if r["class"] == "O" else C_TLIGHT
        tbl_style.append(("BACKGROUND", (0,i), (-1,i), bg))

    tbl.setStyle(TableStyle(tbl_style))
    story.append(tbl)
    story.append(Spacer(1, 20))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 6))
    story.append(p(
        f"Mo hinh ResNet50  |  Do chinh xac 97%  |  EcoScan (c) {datetime.now().year}",
        size=8, color=C_GRAY, align="CENTER",
    ))

    doc.build(story)
    buf.seek(0)
    return buf
