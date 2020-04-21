from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from ..i18n import _


class ScreenConsentCircleTask(Screen):
    """ Display that tells the user what to in next task. """
    consent_msg = StringProperty(_("Initiating..."))
    
    def __init__(self, **kwargs):
        super(ScreenConsentCircleTask, self).__init__(**kwargs)
    
    def on_pre_enter(self, *args):
        self.consent_msg = _('Consent\nDo you want to continue?')  # ToDo: More Information
