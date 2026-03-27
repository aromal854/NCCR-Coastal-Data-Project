from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io, os

# ─────────────────────────────────────────────────────────────────────────────
# NCCR — Certificate of Contribution Generator
# Certificate is issued ONLY after professor verification.
# ─────────────────────────────────────────────────────────────────────────────

def _try_font(size, bold=False):
    """Try to load a system font, fall back to default."""
    candidates_bold = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_regular
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_certificate(
    contributor_name: str,
    location: str,
    verified_by: str = "",
    contributor_email: str = "",
    num_records: int = 1,
) -> bytes:
    """
    Generate a formal NCCR Certificate of Contribution as PNG bytes.

    Args:
        contributor_name : Name of the data contributor.
        location         : Coastal region / location submitted.
        verified_by      : Professor/Scientist who verified the data.
        contributor_email: Contributor's email (used for display only).
        num_records      : Number of data records verified.

    Returns:
        PNG image as bytes (suitable for st.download_button or email attachment).
    """

    W, H = 1100, 800
    img = Image.new("RGB", (W, H), "#FAFAF7")
    draw = ImageDraw.Draw(img)

    # ── Background gradient bands ──────────────────────────────────────────
    navy   = (0, 31, 63)
    gold   = (182, 145, 49)
    white  = (255, 255, 255)
    cream  = (250, 250, 247)
    ink    = (20, 30, 48)
    mid    = (80, 100, 130)

    # Top & bottom navy banners
    draw.rectangle([0, 0, W, 80], fill=navy)
    draw.rectangle([0, H - 80, W, H], fill=navy)

    # Gold accent lines
    draw.rectangle([0, 80, W, 88], fill=gold)
    draw.rectangle([0, H - 88, W, H - 80], fill=gold)

    # ── Outer ornamental border ───────────────────────────────────────────
    draw.rectangle([18, 18, W - 18, H - 18], outline=navy, width=3)
    draw.rectangle([24, 24, W - 24, H - 24], outline=gold, width=2)

    # ── Fonts ─────────────────────────────────────────────────────────────
    f_title   = _try_font(28, bold=True)
    f_org     = _try_font(14, bold=False)
    f_heading = _try_font(22, bold=True)
    f_body    = _try_font(15, bold=False)
    f_name    = _try_font(32, bold=True)
    f_small   = _try_font(12, bold=False)
    f_label   = _try_font(11, bold=True)
    f_sig_ph  = _try_font(13, bold=False)

    # ── TOP BANNER: Organisation ──────────────────────────────────────────
    draw.text((W // 2, 30), "GOVERNMENT OF INDIA  ·  MINISTRY OF EARTH SCIENCES",
              fill=gold, font=f_org, anchor="mt")
    draw.text((W // 2, 52), "NATIONAL CENTRE FOR COASTAL RESEARCH (NCCR)",
              fill=white, font=f_title, anchor="mt")

    # ── CERTIFICATE HEADING ───────────────────────────────────────────────
    draw.text((W // 2, 110), "CERTIFICATE OF CONTRIBUTION",
              fill=navy, font=f_heading, anchor="mt")

    # Thin underline below heading
    uw = 420
    draw.rectangle([W // 2 - uw // 2, 142, W // 2 + uw // 2, 145], fill=gold)

    # ── CITATION TEXT ─────────────────────────────────────────────────────
    draw.text((W // 2, 168), "This is to certify that",
              fill=mid, font=f_body, anchor="mt")

    # Contributor name — prominent
    draw.text((W // 2, 200), contributor_name.upper(),
              fill=navy, font=f_name, anchor="mt")

    # Thin underline below name
    draw.rectangle([W // 2 - 260, 243, W // 2 + 260, 245], fill=gold)

    # Body paragraph
    record_word = "data record" if num_records == 1 else "data records"
    body_lines = [
        f"has made a verified contribution of {num_records} coastal {record_word} to the",
        f"NCCR Coastal-Marine Data Portal for the coastal region of",
        f"{location}.",
        "",
        "The submitted data has been independently reviewed and verified by the",
        "designated academic expert in accordance with NCCR data governance protocols.",
        "This contribution supports India's coastal monitoring, research, and",
        "sustainable management initiatives under the Ministry of Earth Sciences.",
    ]
    y_body = 266
    for line in body_lines:
        draw.text((W // 2, y_body), line, fill=ink, font=f_body, anchor="mt")
        y_body += 25

    # ── DATE ──────────────────────────────────────────────────────────────
    issue_date = datetime.now().strftime("%d %B %Y")
    draw.text((W // 2, y_body + 10), f"Date of Issue: {issue_date}",
              fill=mid, font=f_small, anchor="mt")

    # ── SIGNATURE SECTION ─────────────────────────────────────────────────
    sig_y_top    = H - 210
    sig_y_line   = H - 140
    sig_y_label  = H - 130

    left_cx  = W // 4
    right_cx = 3 * W // 4

    # --- Left signature: Verified By (Professor / Scientist) ---
    if verified_by:
        draw.text((left_cx, sig_y_top), verified_by,
                  fill=navy, font=f_sig_ph, anchor="mt")
    else:
        # Placeholder italics simulation via lighter colour
        draw.text((left_cx, sig_y_top), "(Scientist's Digital Signature)",
                  fill=(160, 160, 160), font=f_sig_ph, anchor="mt")

    draw.line([left_cx - 140, sig_y_line, left_cx + 140, sig_y_line], fill=navy, width=1)
    draw.text((left_cx, sig_y_label), "VERIFIED BY — ACADEMIC EXPERT",
              fill=gold, font=f_label, anchor="mt")
    if verified_by:
        draw.text((left_cx, sig_y_label + 18), verified_by,
                  fill=mid, font=f_small, anchor="mt")

    # --- Right signature: NCCR Authority ---
    draw.text((right_cx, sig_y_top), "(NCCR Authorised Signatory)",
              fill=(160, 160, 160), font=f_sig_ph, anchor="mt")
    draw.line([right_cx - 140, sig_y_line, right_cx + 140, sig_y_line], fill=navy, width=1)
    draw.text((right_cx, sig_y_label), "FOR DIRECTOR — NCCR",
              fill=gold, font=f_label, anchor="mt")
    draw.text((right_cx, sig_y_label + 18), "National Centre for Coastal Research",
              fill=mid, font=f_small, anchor="mt")

    # ── BOTTOM BANNER ─────────────────────────────────────────────────────
    draw.text((W // 2, H - 70),
              "NCCR Coastal-Marine Data Portal  ·  An Initiative of Ministry of Earth Sciences, Government of India",
              fill=white, font=f_small, anchor="mt")
    draw.text((W // 2, H - 50),
              "nccr.res.in  ·  This certificate is computer-generated and valid without physical signature.",
              fill=gold, font=f_small, anchor="mt")

    # ── Convert to bytes ──────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(150, 150))
    buf.seek(0)
    return buf.read()