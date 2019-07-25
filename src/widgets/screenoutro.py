from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock

from . import BlockingPopup

from ..i18n import _


class ScreenOutro(Screen):
    """ Display at the end of a session. """
    settings = ObjectProperty()
    outro_msg = StringProperty(_("Initiating..."))
    
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        
        self.outro_msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"  # Workaround for i18n.
        if self.settings.is_local_storage_enabled:
            app.write_data_to_files()
            dest = App.get_running_app().get_storage_path()
            self.outro_msg += _("Files were{}saved to [i]{}[/i].").format(' ' if dest.exists() else _(' [b]not[/b] '),
                                                                          dest)
        else:
            self.outro_msg += _("Results were [b]not[/b] locally stored as files.\n"
                                "You can enable this in the settings.")
    
        app.upload_btn_enabled = self.settings.is_upload_enabled
        
    def on_upload(self):
        # Show we're busy. Heroku dyno sleeps so it can take some time for the response.
        upload_info = BlockingPopup(title=_("Uploading..."))
        upload_info.msg = _("Waking up server.\nPlease be patient.")
        upload_info.open()
        app = App.get_running_app()
        # Workaround to make info popup show up.
        Clock.schedule_once(lambda dt: app.upload_data(), 0)
        upload_info.dismiss()
