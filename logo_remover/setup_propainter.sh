#!/usr/bin/env bash
# setup_propainter.sh — تنزيل وتجهيز ProPainter للإزالة بالذكاء الصناعي.
#
# الاستخدام:
#   bash logo_remover/setup_propainter.sh
#
# بيعمل:
#   1) استنساخ مستودع ProPainter جوه logo_remover/ProPainter
#   2) تثبيت متطلباته
#   3) الأوزان (weights) بتتنزّل تلقائيًا أول مرة تشغّل الاستنتاج.
#
# ملاحظات:
#   - يُفضّل كارت شاشة NVIDIA (CUDA). بيشتغل على CPU بس أبطأ بكتير.
#   - لو عندك بايثون في بيئة افتراضية (venv/conda) فعّلها الأول.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PP_DIR="$HERE/ProPainter"

if [ ! -d "$PP_DIR/.git" ]; then
  echo ">> استنساخ ProPainter..."
  git clone https://github.com/sczhou/ProPainter.git "$PP_DIR"
else
  echo ">> ProPainter موجود بالفعل: $PP_DIR"
fi

echo ">> تثبيت المتطلبات..."
python -m pip install --upgrade pip
# PyTorch: لو مش متثبّت، ثبّت النسخة المناسبة لكارتك من https://pytorch.org
python -c "import torch" 2>/dev/null || {
  echo "!! PyTorch غير مثبّت. ثبّته حسب جهازك من https://pytorch.org ثم أعد التشغيل."
}
python -m pip install -r "$PP_DIR/requirements.txt"

echo ""
echo ">> تم التجهيز. جرّب:"
echo "   python logo_remover/make_mask.py --video in.mp4 --box 25,62,232,110 --out mask.png"
echo "   python logo_remover/remove_logo.py --mode propainter --video in.mp4 --mask mask.png --out out.mp4 --fp16"
