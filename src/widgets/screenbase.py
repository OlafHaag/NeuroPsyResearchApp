from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, ColorProperty


class BaseScreen(Screen):
    color = ColorProperty()
    navbar_enabled = BooleanProperty(False)
