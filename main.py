import os

from utils import get_img_bins


def main(name):
    SAVE_DIR = f"local/{name}/"
    os.makedirs(SAVE_DIR, exist_ok=True)
    for i, v in enumerate(get_img_bins(name, limit=1, skip_ext_valid=True)):
        img = v[0]
        ext = v[1]
        filename = f'{i}{ext}'
        path = os.path.join(SAVE_DIR, filename)
        with open(path, 'wb') as f:
            f.write(img)


if __name__ == "__main__":
    main("プログラミング")
