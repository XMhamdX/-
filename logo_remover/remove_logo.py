#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remove_logo.py — إزالة لوغو من فيديو بطريقتين.

الأنماط (modes):

  delogo   : سريع، بيستخدم فلتر ffmpeg. مناسب للّوغو الثابت فوق خلفية
             بسيطة (سما، لون متدرّج...). بيعيد بناء الخلفية من البكسلات
             المحيطة. مش محتاج كارت شاشة.

  propainter: للحالات الصعبة (خلفية معقّدة أو لوغو متحرك). بيستخدم نموذج
             ذكاء صناعي (ProPainter) بيراعي الزمن فيمنع الرعشة. بيحتاج
             ماسك + يُفضّل كارت شاشة (GPU).

أمثلة:
  # سريع — لوغو ثابت بمربع
  python remove_logo.py --mode delogo --video in.mp4 --box 25,62,232,110 --out out.mp4

  # ذكاء صناعي — بماسك جاهز
  python make_mask.py --video in.mp4 --box 25,62,232,110 --out mask.png
  python remove_logo.py --mode propainter --video in.mp4 --mask mask.png --out out.mp4
"""
import argparse
import os
import shutil
import subprocess
import sys


def run(cmd):
    print("+ " + " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True)


def check_tool(name):
    if shutil.which(name) is None:
        sys.exit(f"مطلوب '{name}' لكنه غير مثبّت. ثبّته الأول.")


def parse_box(text):
    parts = [int(p) for p in text.replace(" ", "").split(",")]
    if len(parts) != 4:
        sys.exit("صيغة --box لازم تكون: x,y,w,h  مثال: 25,62,232,110")
    return parts


def mode_delogo(args):
    check_tool("ffmpeg")
    if not args.box:
        sys.exit("نمط delogo محتاج --box x,y,w,h")
    x, y, w, h = parse_box(args.box)
    vf = f"delogo=x={x}:y={y}:w={w}:h={h}"
    run([
        "ffmpeg", "-y", "-i", args.video,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart",
        args.out,
    ])
    print(f"\nتم ✅  الناتج: {args.out}")


def mode_propainter(args):
    check_tool("ffmpeg")
    if not args.mask:
        sys.exit("نمط propainter محتاج --mask mask.png")
    pp_dir = os.environ.get("PROPAINTER_DIR", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ProPainter"))
    infer = os.path.join(pp_dir, "inference_propainter.py")
    if not os.path.isfile(infer):
        sys.exit(
            f"ProPainter غير موجود في: {pp_dir}\n"
            "شغّل الأول:  bash logo_remover/setup_propainter.sh\n"
            "أو حدّد المسار بمتغيّر البيئة PROPAINTER_DIR."
        )

    results_dir = os.path.abspath(args.workdir)
    os.makedirs(results_dir, exist_ok=True)

    cmd = [
        sys.executable, infer,
        "--video", os.path.abspath(args.video),
        "--mask", os.path.abspath(args.mask),
        "--output", results_dir,
        "--mask_dilation", str(args.mask_dilation),
    ]
    if args.fp16:
        cmd.append("--fp16")
    if args.resize_ratio != 1.0:
        cmd += ["--resize_ratio", str(args.resize_ratio)]
    run(cmd)

    name = os.path.splitext(os.path.basename(args.video))[0]
    inpainted = os.path.join(results_dir, name, "inpaint_out.mp4")
    if not os.path.isfile(inpainted):
        sys.exit(f"مالقيتش ناتج ProPainter المتوقّع: {inpainted}")

    # ProPainter بيشيل الصوت — نرجّعه من الأصل
    print("\nإرجاع الصوت الأصلي...")
    run([
        "ffmpeg", "-y",
        "-i", inpainted,
        "-i", os.path.abspath(args.video),
        "-map", "0:v", "-map", "1:a?",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart",
        args.out,
    ])
    print(f"\nتم ✅  الناتج: {args.out}")


def main():
    ap = argparse.ArgumentParser(description="إزالة لوغو من فيديو")
    ap.add_argument("--mode", choices=["delogo", "propainter"], required=True)
    ap.add_argument("--video", required=True, help="مسار الفيديو")
    ap.add_argument("--out", default="output_nologo.mp4", help="مسار الناتج")
    ap.add_argument("--box", help="delogo: إحداثيات x,y,w,h")
    ap.add_argument("--mask", help="propainter: مسار الماسك (PNG)")
    ap.add_argument("--mask_dilation", type=int, default=8,
                    help="propainter: توسيع الماسك بالبكسل")
    ap.add_argument("--resize_ratio", type=float, default=1.0,
                    help="propainter: تصغير مؤقّت لتوفير الذاكرة (مثال 0.5)")
    ap.add_argument("--fp16", action="store_true",
                    help="propainter: نصف الدقّة (أسرع وأخف على GPU)")
    ap.add_argument("--workdir", default="results",
                    help="propainter: مجلد النواتج المؤقّتة")
    args = ap.parse_args()

    if args.mode == "delogo":
        mode_delogo(args)
    else:
        mode_propainter(args)


if __name__ == "__main__":
    main()
