from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty


class BaseScreen(Screen):
    navbar_enabled = BooleanProperty(False)
