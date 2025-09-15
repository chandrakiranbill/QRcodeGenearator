
#!/usr/bin/env python3
"""
QR Code Generator
Biox Systems - Assignment
Author: Chandra Kiran Billingi

Usage:
    python qr_generator.py --url "Site URL" --out "qrs/File-Name-to-be-saved.png" --caption "Caption is optional and can be added for reference in this section"
"""

import argparse
import re
from pathlib import Path
from typing import Optional

import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont

def is_plausible_url(url: str) -> bool:
    """
    Checking to see if `url` is plausibly valid HTTP or the HTTPS.
    Using regex—this is not full validation, just a guard.
    """
    # Regex pattern to match http(s):// + domain + optional path/query
    pattern = re.compile(
        r"^(https?://)"                         # protocol http or https
        r"[\w\.-]+"                             # the first part of domain
        r"(?:\.[\w\.-]+)+"                      # at least one dot-something in the url
        r"[/\w\-._~:?#[\]@!$&'()*+,;=]*$"        # optional path or the query provided by the user
        , re.IGNORECASE
    )
    return bool(pattern.match(url))


def _ensure_pil_image(img_wrapped: PilImage) -> Image.Image:
    """
    Unwraps PilImage wrapper if needed and ensures image is in RGB mode.
    which will Ensures the compatibility for compositing and pasting if needed.
    """
    try:
        # qrcodeing the  library version which might wrap the image;  instead we are trying to get actual PIL Image
        pil_img = img_wrapped.get_image()  
    except Exception:
        # If there is no wrapper, we can assume already its already a  PIL.Image
        pil_img = img_wrapped  

    # Converting  into RGB if it's not already so that later operations work consistently
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    return pil_img


def generate_qr(
    url: str,
    out_path: Path,
    box_size: int = 10,
    border: int = 4,
    caption: Optional[str] = None,
) -> Path:
    """
    Generating a QR code image from the given URL and writing into the out_path so that it can direct to so the user can scan it.
    Optionally adds a caption under the QR image if the user has provided it .
    Returns the output file path on success.
    Raises exceptions incase of any failures.
    """
    # Creating the  QRCode object with error correction and size settings
    qr = qrcode.QRCode(
        version=None,  # None which means we are automatically choose minimal version
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border
    )
    qr.add_data(url)   # embing the the URL data into the QR code
    qr.make(fit=True)  # computing the best fit for the QR version

    # Rendering the QR code into an image
    img_wrapped = qr.make_image(fill_color="black", back_color="white")
    qr_img = _ensure_pil_image(img_wrapped)
    qr_width, qr_height = qr_img.size

    # If suppose the user has provided  no caption, just save QR directly
    if not caption:
        # Make sure output directory exists for saving the file
        out_path.parent.mkdir(parents=True, exist_ok=True)
        qr_img.save(out_path)
        return out_path

    # If caption is provided, prepare the canvas to include caption by the user at the bottom
    draw_margin = 16  # adding the space between QR and caption
    caption_height = 40  # space reserved for the caption text

    # New image will be generated if there is caption but the width same as QR, height will be increased
    total_height = qr_height + caption_height + draw_margin * 2
    canvas = Image.new("RGB", (qr_width, total_height), "white")

    # Pasting the QR image at top-left (0,0)
    canvas.paste(qr_img, (0, 0))

    # Preparing to draw caption below
    draw = ImageDraw.Draw(canvas)
    try:
        # Loading a default font
        font = ImageFont.load_default()
    except Exception:
        font = None  # If this fails, drawing additional  text without any explicit font

    text = caption

    # Measuring the  text size anf try modern method and will fallback if needed
    try:
        bbox = draw.textbbox((0, 0), text, font=font)  
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except Exception:
        try:
            text_width, text_height = draw.textsize(text, font=font)
        except Exception:
            text_width = len(text) * 6
            text_height = 12

    # Computing the position to center caption
    x = (qr_width - text_width) // 2
    y = qr_height + draw_margin

    # Drawing the text
    draw.text((x, y), text, fill="black", font=font)

    # Ensure output directory exists to save the file 
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Saving the  final image (QR + caption)
    canvas.save(out_path)
    return out_path


def main(argv=None) -> int:
    """
    Parse command-line arguments, validate them, generate QR, and output status.
    Returns 0 on success, non-zero error codes for different failures.
    """
    parser = argparse.ArgumentParser(
        description="Generate a QR code PNG for a given URL."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="The URL to encode into the QR code."
    )
    parser.add_argument(
        "--out",
        default="qrs/qr.png",
        help="Output PNG path (default: qrs/qr.png)."
    )
    parser.add_argument(
        "--caption",
        default=None,
        help="Optional caption text under the QR."
    )
    parser.add_argument(
        "--box-size",
        type=int,
        default=10,
        help="QR box size in pixels (default 10)."
    )
    parser.add_argument(
        "--border",
        type=int,
        default=4,
        help="QR border width in boxes (default 4)."
    )
    args = parser.parse_args(argv)

    # Validating URL before proceeding
    if not is_plausible_url(args.url):
        print("[ERROR] The provided string does not look like a valid http(s) URL:", args.url)
        return 2

    try:
        # Generating the QR code for the given URL
        saved_path = generate_qr(
            url=args.url,
            out_path=Path(args.out),
            box_size=args.box_size,
            border=args.border,
            caption=args.caption
        )
    except Exception as exc:
        # THis will cathc all the exceptions report and exits the code for exceptions and uses non zero exir code
        print("[ERROR] Failed to generate QR:", exc)
        return 1

    # Prints the Path in which the QR code is saved
    print(f"[OK] QR code saved to: {saved_path}")
    return 0


if __name__ == "__main__":
    # Use SystemExit to ensure correct exit code when run as script
    raise SystemExit(main())
