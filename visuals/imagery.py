import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider


def show_gray_with_value_adjustments(img: np.ndarray):
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(15, 15))
    plt.subplots_adjust(bottom=0.25)

    vmin = 0
    vmax = img.max()
    step = (vmax - vmin) / 250

    # Display the initial image
    im_display = ax.imshow(img, cmap='gray', vmin=vmin, vmax=vmax)
    ax.set_title('Grayscale Image with Contrast Adjustment')

    # Create axes for the sliders
    ax_min = plt.axes([0.25, 0.15, 0.65, 0.03])
    ax_max = plt.axes([0.25, 0.1, 0.65, 0.03])

    # Create the sliders
    min_slider = Slider(ax_min, 'Min Value', vmin, vmax, valinit=vmin, valstep=step)
    max_slider = Slider(ax_max, 'Max Value', vmin, vmax, valinit=vmax, valstep=step)

    def update(val):
        """Update the image display based on slider values"""
        vmin = min_slider.val
        vmax = max_slider.val

        # Ensure min is less than max
        if vmin >= vmax:
            if val == min_slider:  # If min slider caused the overlap
                min_slider.set_val(vmax - 1)
            else:  # If max slider caused the overlap
                max_slider.set_val(vmin + 1)
            return

        im_display.set_clim(vmin, vmax)
        fig.canvas.draw_idle()

    # Register the update function with each slider
    min_slider.on_changed(update)
    max_slider.on_changed(update)

    # Adding click event
    def onclick(event):
        if event.xdata != None and event.ydata != None:
            print((int(event.ydata), int(event.xdata)), ",", sep="")
    cid = fig.canvas.mpl_connect('button_press_event', onclick)

    plt.show()
