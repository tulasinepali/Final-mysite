import os
import sys

# Force UTF-8 stdout if available
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_optimizer():
    try:
        from PIL import Image
    except ImportError:
        print("[ERROR] Pillow not installed. Please activate your virtualenv first.")
        sys.exit(1)

    print("=" * 60)
    print("  TulasiNepali Media Optimizer (In-place safe compression)")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(base_dir, 'media')

    if not os.path.exists(media_dir):
        print(f"Directory {media_dir} not found.")
        return

    total_saved = 0
    count = 0

    for root, _, files in os.walk(media_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in ('.jpg', '.jpeg', '.png'):
                continue
            
            p = os.path.join(root, f)
            orig_size = os.path.getsize(p)
            if orig_size < 100000:  # Skip already small files (< 100KB)
                continue

            try:
                with Image.open(p) as im:
                    # Scale down if abnormally large
                    max_w, max_h = (400, 400) if 'site' in root else (1000, 1000)
                    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

                    if ext in ('.jpg', '.jpeg'):
                        im.save(p, 'JPEG', quality=82, optimize=True)
                    elif ext == '.png':
                        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                            im.save(p, 'PNG', optimize=True)
                        else:
                            im = im.convert('RGB')
                            im.save(p, 'JPEG', quality=82, optimize=True)

                new_size = os.path.getsize(p)
                if orig_size > new_size:
                    saved = orig_size - new_size
                    total_saved += saved
                    count += 1
                    print(f"[OK] {f}: {orig_size // 1024} KB -> {new_size // 1024} KB (Saved {saved // 1024} KB)")
            except Exception as e:
                print(f"[WARN] Could not optimize {f}: {e}")

    print("-" * 60)
    print(f"Optimized {count} files.")
    print(f"Total Bandwidth Saved: {total_saved // 1024} KB (~{round(total_saved / (1024 * 1024), 2)} MB)!")
    print("=" * 60)

if __name__ == '__main__':
    run_optimizer()
