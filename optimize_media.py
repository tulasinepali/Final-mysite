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
        is_site_dir = 'site' in root.replace('\\', '/').split('/')
        size_threshold = 8000 if is_site_dir else 80000

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in ('.jpg', '.jpeg', '.png'):
                continue
            
            p = os.path.join(root, f)
            orig_size = os.path.getsize(p)
            if orig_size < size_threshold:
                continue

            try:
                with Image.open(p) as im:
                    # Maximum dimensions: 120x120 for site logos/icons, 1000x1000 for content
                    max_w, max_h = (120, 120) if is_site_dir else (1000, 1000)
                    im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

                    if ext in ('.jpg', '.jpeg'):
                        im.save(p, 'JPEG', quality=82, optimize=True)
                    elif ext == '.png':
                        if is_site_dir or orig_size > 50000:
                            # Use adaptive palette to compress PNGs significantly while preserving transparency
                            im_opt = im.convert('P', palette=Image.Palette.ADAPTIVE)
                            im_opt.save(p, 'PNG', optimize=True)
                        elif im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
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
