from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import os

class EmojiApp(App):
    def build(self):
        # Chemin vers la police NotoColorEmoji.ttf
        font_path = os.path.join(os.getcwd(), "Noto_color_Emoji(1)/NotoColorEmoji-Regular.ttf")
        
        # Vérifiez si la police existe
        if not os.path.exists(font_path):
            print(f"❌ Erreur : La police '{font_path}' est introuvable. Vérifiez le chemin.")
            return Label(text="❌ Police introuvable", font_size=24)

        # Créez un layout avec un label contenant des emojis
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(
            text="🚀 Test Emoji avec Kivy 🌟",
            font_name=font_path,
            font_size=48,
            color=(1, 1, 1, 1),  # Blanc
        )
        layout.add_widget(label)
        return layout

if __name__ == "__main__":
    EmojiApp().run()