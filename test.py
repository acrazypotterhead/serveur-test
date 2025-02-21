from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

class MatplotlibApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Créer une figure matplotlib
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        
        # Ajouter la figure à Kivy
        canvas = FigureCanvasKivyAgg(fig)
        layout.add_widget(canvas)
        
        return layout

if __name__ == "__main__":
    MatplotlibApp().run()

