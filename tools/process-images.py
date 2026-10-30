"""
圖片處理：讀素材包原檔 → 裁切 → 實色矩形遮罩（可寫替代文字）→ 縮放 → WebP。
用法：.venv/bin/python -I tools/process-images.py <素材包路徑> [輸出資料夾]
設定全在 tools/redactions.json，座標為原圖像素。
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(HERE, "redactions.json"), encoding="utf-8"))
MAX_WIDTH = 1600


def load_font(size, bold=False):
    candidates = CONFIG["font_candidates_bold" if bold else "font_candidates"]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def apply_masks(img, masks):
    draw = ImageDraw.Draw(img)
    for m in masks:
        x0, y0, x1, y1 = m["box"]
        draw.rectangle([x0, y0, x1, y1], fill=m.get("fill", "#ffffff"))
        text = m.get("text")
        if not text:
            continue
        font = load_font(m.get("size", 27), m.get("bold", False))
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        th = b - t
        tw = r - l
        y = y0 + (y1 - y0 - th) / 2 - t
        if m.get("align") == "center":
            x = x0 + (x1 - x0 - tw) / 2 - l
        else:
            x = x0 + 4
        draw.text((x, y), text, font=font, fill=m.get("color", "#111111"))
    return img


def process_still(src_root, out_dir, spec):
    img = Image.open(os.path.join(src_root, spec["src"])).convert("RGB")
    # 先遮罩再裁切：設定檔座標一律以「未裁切的原圖」為準
    if spec.get("masks"):
        img = apply_masks(img, spec["masks"])
    if "crop" in spec:
        img = img.crop(tuple(spec["crop"]))
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
    out = os.path.join(out_dir, spec["out"])
    img.save(out, "WEBP", quality=85, method=6)
    print(f"{spec['out']}: {img.width}x{img.height}, {os.path.getsize(out)//1024} KB")


def process_gif(src_root, out_dir, spec):
    gif = Image.open(os.path.join(src_root, spec["src"]))
    probe = spec["sheets_probe"]
    px, py = probe["xy"]
    target = probe["rgb"]
    frames, durations = [], []
    for i in range(gif.n_frames):
        gif.seek(i)
        frame = gif.convert("RGB")
        r, g, b = frame.getpixel((px, py))
        is_sheets = all(abs(a - t) <= probe["tol"] for a, t in zip((r, g, b), target))
        frame = apply_masks(frame, spec["sheets_masks"] if is_sheets else spec["app_masks"])
        if frame.width > spec["width"]:
            frame = frame.resize((spec["width"], round(frame.height * spec["width"] / frame.width)), Image.LANCZOS)
        frames.append(frame)
        durations.append(max(gif.info.get("duration", 100), 50))
    out = os.path.join(out_dir, spec["out"])
    frames[0].save(out, "WEBP", save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, quality=spec["quality"], method=4)
    print(f"{spec['out']}: {frames[0].width}x{frames[0].height}, {len(frames)} frames, {os.path.getsize(out)//1024} KB")


def main():
    src_root = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    for spec in CONFIG["images"]:
        process_still(src_root, out_dir, spec)
    if "gif" in CONFIG:
        process_gif(src_root, out_dir, CONFIG["gif"])


if __name__ == "__main__":
    main()
