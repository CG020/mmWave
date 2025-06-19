import  os
import  matplotlib.pyplot as plt


def color_style():
    current_dir = os.path.dirname(__file__)
    style_path = os.path.join(current_dir, f'color.mplstyle')

    plt.style.use(style_path)
