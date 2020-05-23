from kivy.app import App
from kivy.properties import (ObjectProperty,
                             StringProperty,
                             BooleanProperty,
                             )
from kivy.clock import Clock

from . import BaseScreen
from . import BlockingPopup

from ..i18n import _


class ScreenHome(BaseScreen):
    """ Display that gives general information. """
    msg = StringProperty()
    title = StringProperty()
    
    def on_pre_enter(self, *args):
        """ Reset data collection each time before a new task is started. """
        app = App.get_running_app()
        app.settings.reset_current()
        app.data_mgr.clear_data_collection()
        app.settings.current_task = None
        
        self.set_text()
        
    def set_text(self):
        app = App.get_running_app()
        # To get translation after language change, we have to trigger setting the texts.
        self.title = _("Welcome!")
        if app.settings.is_local_storage_enabled:
            storage_hint = _("Storing research data on the device is enabled. You can disable it in the settings.\n")
        else:
            storage_hint = _("Storing research data on the device is disabled. You can enable it in the settings.\n")
    
        self.msg = _("You can participate in a study by choosing from available studies below."
                     "\n\n") + storage_hint
        

class ScreenOutro(BaseScreen):
    """ Display at the end of a session. """
    msg = StringProperty(_("Loading..."))
    upload_btn_enabled = BooleanProperty(True)
    popup_block = ObjectProperty(None, allownone=True)

    def on_pre_enter(self, *args):
        app = App.get_running_app()
        
        self.msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"  # Workaround for i18n.
        if app.settings.is_local_storage_enabled:
            if not app.data_mgr.data_saved:
                app.data_mgr.write_data_to_files()
            dest = app.data_mgr.get_storage_path()
            self.msg += _("Files were{} saved to [i]{}[/i].\n").format('' if dest.exists() else _(' [b]not[/b]'), dest)
        else:
            self.msg += _("Results were [b]not[/b] locally stored as files. "
                          "You can enable this in the settings [i]before[/i] starting a study.\n")
        self.upload_btn_enabled = app.settings.is_upload_enabled
        if self.upload_btn_enabled:
            self.msg += _("You can now [b]upload[/b] the research data by pressing the button below. "
                          "Unless stated otherwise in the study's description we'd appreciate if you only upload "
                          "your data the first time you participated in this study. Thank you.\n")
        
    def on_upload(self):
        # Show we're busy. Heroku dyno sleeps so it can take some time for the response.
        if not self.popup_block:
            self.popup_block = BlockingPopup(title=_("Uploading..."), text=_("Waking up server.\nPlease be patient."))
        self.popup_block.open()
        app = App.get_running_app()
        # Workaround to make info popup show up.
        Clock.schedule_once(lambda dt: app.data_mgr.upload_data(app.get_upload_route()), 0)
        self.popup_block.dismiss()
