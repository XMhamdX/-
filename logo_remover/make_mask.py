#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_mask.py — إنشاء ماسك (mask) للّوغو المراد إزالته.

الماسك = صورة بالأبيض والأسود بنفس مقاس الفيديو:
    - الأبيض = المنطقة اللي فيها اللوغو (اللي هتتشال / تتملى).
    - الأسود = الباقي (يفضل زي ما هو).

طريقتان للاستخدام:

1) بمربع (box) — لو اللوغو ثابت وتعرف إحداثياته:
       python make_mask.py --video in.mp4 --box 25,62,232,110 --out mask.png

2) بالرسم اليدوي (--draw) — تفتح أول فريم وترسم بالماوس مستطيل/مستطيلات
   حوالين اللوغو (شغّالة محليًا بشاشة عرض، مش على السيرفر):
       python make_mask.py --video in.mp4 --draw --out mask.png
   داخل النافذة:
       - اسحب بالماوس لرسم مستطيل حوالين اللوغو (ممكن أكتر من واحد).
       - z  = تراجع عن آخر مستطيل.
       - s  = حفظ الماسك والخروج.
       - q  = خروج بدون حفظ.

الماسك ده ثابت (نفس المكان لكل الفريمات). لو اللوغو بيتحرك، شوف README
لطريقة الماسك المتحرك.
"""
import argparse
import sys

import cv2
import numpy as np


def first_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        sys.exit(f"تعذّر قراءة الفيديو: {video_path}")
    return frame


def mask_from_boxes(shape, boxes, dilate=0):
    """boxes: list of (x, y, w, h). shape: (h, w[, c]) للفريم."""
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    for (x, y, bw, bh) in boxes:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(w, x + bw), min(h, y + bh)
        mask[y0:y1, x0:x1] = 255
    if dilate > 0:
        k = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate(mask, k)
    return mask


def draw_interactive(frame):
    """يفتح نافذة ويسمح برسم مستطيلات حوالين اللوغو. يرجّع قائمة boxes."""
    boxes = []
    state = {"drawing": False, "x0": 0, "y0": 0, "x1": 0, "y1": 0}
    win = "arsm mostateel 7awalin el logo | s=save z=undo q=quit"

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["drawing"] = True
            state["x0"], state["y0"] = x, y
            state["x1"], state["y1"] = x, y
        elif event == cv2.EVENT_MOUSEMOVE and state["drawing"]:
            state["x1"], state["y1"] = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            state["drawing"] = False
            x0, y0 = state["x0"], state["y0"]
            x1, y1 = x, y
            bx, by = min(x0, x1), min(y0, y1)
            bw, bh = abs(x1 - x0), abs(y1 - y0)
            if bw > 3 and bh > 3:
                boxes.append((bx, by, bw, bh))

    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_mouse)

    while True:
        disp = frame.copy()
        for (x, y, w, h) in boxes:
            cv2.rectangle(disp, (x, y), (x + w, y + h), (0, 0, 255), 2)
        if state["drawing"]:
            cv2.rectangle(disp, (state["x0"], state["y0"]),
                          (state["x1"], state["y1"]), (0, 255, 0), 1)
        cv2.imshow(win, disp)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("s"):
            break
        if key == ord("q"):
            boxes = []
            break
        if key == ord("z") and boxes:
            boxes.pop()

    cv2.destroyAllWindows()
    return boxes


def parse_box(text):
    parts = [int(p) for p in text.replace(" ", "").split(",")]
    if len(parts) != 4:
        sys.exit("صيغة --box لازم تكون: x,y,w,h  مثال: 25,62,232,110")
    return tuple(parts)


def main():
    ap = argparse.ArgumentParser(description="إنشاء ماسك للّوغو")
    ap.add_argument("--video", required=True, help="مسار الفيديو")
    ap.add_argument("--out", default="mask.png", help="مسار حفظ الماسك (PNG)")
    ap.add_argument("--box", help="إحداثيات المربع x,y,w,h (لو عارفها)")
    ap.add_argument("--draw", action="store_true", help="رسم يدوي على أول فريم")
    ap.add_argument("--dilate", type=int, default=6,
                    help="توسيع الماسك بالبكسل (هامش أمان حوالين اللوغو)")
    args = ap.parse_args()

    frame = first_frame(args.video)

    if args.box:
        boxes = [parse_box(args.box)]
    elif args.draw:
        boxes = draw_interactive(frame)
        if not boxes:
            sys.exit("مفيش مستطيلات — اتلغى الحفظ.")
        print("المستطيلات اللي رسمتها (x,y,w,h):")
        for b in boxes:
            print("  ", ",".join(map(str, b)))
    else:
        sys.exit("لازم تختار --box أو --draw")

    mask = mask_from_boxes(frame.shape, boxes, dilate=args.dilate)
    cv2.imwrite(args.out, mask)
    print(f"اتحفظ الماسك: {args.out}  (مقاس {mask.shape[1]}x{mask.shape[0]})")


if __name__ == "__main__":
    main()
