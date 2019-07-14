from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty

from src.i18n import _


class ScreenOutro(Screen):
    """ Display at the end of a session. """
    settings = ObjectProperty()
    outro_msg = StringProperty(_("Initiating..."))
    
    def on_pre_enter(self, *args):
        self.outro_msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"  # Workaround for i18n.
        if self.settings.is_local_storage_enabled:
            dest = App.get_running_app().get_data_path()
            self.outro_msg += _("Files were{}saved to [i]{}[/i].").format(' ' if dest.exists() else _(' [b]not[/b] '),
                                                                          dest)
        else:
            self.outro_msg += _("Results were [b]not[/b] locally stored as files.\n"
                                "You can enable this in the settings.")
        
        app = App.get_running_app()
        app.upload_btn_enabled = self.settings.is_upload_enabled
