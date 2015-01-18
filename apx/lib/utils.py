import os
import shutil

def install_font(font_filename):
    fonts_dir = os.path.join(os.environ['HOME'], '.fonts')
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)

    font_path = os.path.join(fonts_dir, font_filename)
    if not os.path.exists(font_path):
        shutil.copyfile(os.path.join("assets", font_filename), font_path)


def full_pixels(space, data, gap_pixels=1):
    """returns the given data distributed in the space ensuring it's full pixels
    and with the given gap.
    this will result in minor sub-pixel inaccuracies.
    """
    available = space - (len(data) - 1) * gap_pixels # 8 recs 7 gaps

    res = []
    for i, val in enumerate(data):
        # convert data to 0..1 scale so we deal with fractions
        data_sum = sum(data[i:])
        norm = val * 1.0 / data_sum


        w = max(int(round(available * norm)), 1)
        res.append(w)
        available -= w
    return res
