from kivy.uix.popup import Popup
from kivy.properties import StringProperty

from ..i18n import _


class SimplePopup(Popup):
    msg = StringProperty(_('Initiating...'))
    
    def __init__(self, **kwargs):
        super(SimplePopup, self).__init__(**kwargs)


class BlockingPopup(Popup):
    msg = StringProperty(_('Initiating...'))
    
    def __init__(self, **kwargs):
        super(BlockingPopup, self).__init__(**kwargs)
