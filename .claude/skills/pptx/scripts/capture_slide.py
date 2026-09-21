#!/usr/bin/env python3
"""
capture_slide.py — 사내 DRM 환경용 슬라이드 화면 캡처 및 토큰 절약형 이미지 압축기
(atelier app/shot.py 의 검증된 Pillow 압축 기전 계승)

왜 필요한가:
  사내 Fasoo DRM 환경에서는 slide.Export() 등 백그라운드 파일 저장이 차단되므로,
  파워포인트를 창으로 띄워 데스크톱 스크린샷(CopyFromScreen)으로 취득한다.
  하지만 원본 1080p/4K PNG는 수 MB에 달해 비전 모델 토큰을 과다 소모(1~2만 토큰)하므로,
  Pillow를 통해 720p/1080p 최적 리사이즈 및 JPEG 고압축을 거쳐 100~150KB(토큰 70% 이상 절감)로 누른다.

사용법:
  python scripts/capture_slide.py -i raw_screen.png -o qa_slide.jpg [--max-w 1280] [--quality 85]
"""
import os
import argparse
from PIL import Image

def compress_image(src_path, dest_path, max_width=1280, quality=85):
    """원본 스크린샷 이미지를 최적 해상도로 리사이즈 및 고압축하여 비전 토큰 소모를 70% 이상 절감."""
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    if w > max_width:
        ratio = max_width / float(w)
        new_h = int(h * ratio)
        im = im.resize((max_width, new_h), Image.Resampling.LANCZOS)
    
    im.save(dest_path, format="JPEG", quality=quality, optimize=True)
    orig_sz = os.path.getsize(src_path)
    new_sz = os.path.getsize(dest_path)
    print(f"[압축 완료] {orig_sz:,} B -> {new_sz:,} B ({(1 - new_sz/orig_sz)*100:.1f}% 절감) -> {dest_path}")
    return dest_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slide screenshot compressor for AI Vision QA")
    parser.add_argument("-i", "--input", required=True, help="Input raw screenshot PNG")
    parser.add_argument("-o", "--output", default="qa_slide.jpg", help="Output compressed image path")
    parser.add_argument("--max-w", type=int, default=1280, help="Max width in pixels (default: 1280)")
    parser.add_argument("-q", "--quality", type=int, default=85, help="JPEG quality (default: 85)")
    args = parser.parse_args()
    compress_image(args.input, args.output, args.max_w, args.quality)
