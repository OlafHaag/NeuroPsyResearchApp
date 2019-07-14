from kivy.uix.popup import Popup
from kivy.properties import StringProperty

from src.i18n import _


class SimplePopup(Popup):
    msg = StringProperty(_('Initiating...'))
    
    def __init__(self, **kwargs):
        super(SimplePopup, self).__init__(**kwargs)
