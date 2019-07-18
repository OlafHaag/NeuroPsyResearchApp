from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from ..i18n import _


class ScreenHome(Screen):
    """ Display that gives general information. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    home_msg = StringProperty(_('Initiating...'))
    
    def on_pre_enter(self, *args):
        """ Reset data collection each time before a new task is started. """
        App.get_running_app().settings.reset_current()
        self.home_msg = _('Welcome!')  # ToDo: General Information
    
        app = App.get_running_app()
        app.reset_data_collection()
