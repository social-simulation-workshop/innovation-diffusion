import itertools
import matplotlib.pyplot as plt
import numpy as np
import os

class PlotLinesHandler(object):
    _ids = itertools.count(0)

    def __init__(self, xlabel, ylabel, ylabel_show, x_lim,
        figure_size=(12, 9), output_dir=os.path.join(os.getcwd(), "imgfiles")) -> None:
        super().__init__()

        self.id = next(self._ids)

        self.output_dir = output_dir
        self.title = "{}-{}".format(ylabel, xlabel)
        self.legend_list = list()

        plt.figure(self.id, figsize=figure_size, dpi=80)
        plt.title("{} - {}".format(ylabel_show, xlabel))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel_show)

        ax = plt.gca()
        # ax.set_ylim([-1.5, 1.5])
        ax.set_xlim([0, x_lim])

    def plot_line(self, data,
        linewidth=1, color="", alpha=1.0):

        plt.figure(self.id)
        if color:
            plt.plot(np.arange(data.shape[-1]), data,
                linewidth=linewidth, color=color, alpha=alpha)
        else:
            plt.plot(np.arange(data.shape[-1]), data, linewidth=linewidth)

    def save_fig(self, title_param=""):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        plt.figure(self.id)
        fn = "_".join([self.title, title_param]) + ".png"
            
        plt.savefig(os.path.join(self.output_dir, fn))
        print("fig save to {}".format(os.path.join(self.output_dir, fn)))