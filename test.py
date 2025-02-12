from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen


class StartApp(Screen):
    def __init__(self, **kwargs):
        super(StartApp, self).__init__(**kwargs)

class WindowManager(ScreenManager):
    pass

class TestApp(App):
    def build(self):
        return WindowManager()
    
TestApp().run()
    
    