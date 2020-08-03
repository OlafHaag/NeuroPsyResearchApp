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
        Clock.schedule_once(lambda dt: self.topbar.update_icons(), 0)
    
    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda dt: self.topbar.update_icons(), 0)
        
    def set_text(self):
        app = App.get_running_app()
        # To get translation after language change, we have to trigger setting the texts.
        self.title = _("Welcome!")
        self.msg = _("There's currently 1 study available. You can participate in the study by clicking the button "
                     "below."
                     "\n"
                     "Please create a separate user account through the menu for each person who wants to participate "
                     "in the study on this device.")
        

class ScreenOutro(BaseScreen):
    """ Display at the end of a session. """
    msg = StringProperty(_("Loading..."))
    upload_btn_enabled = BooleanProperty(True)
    popup_block = ObjectProperty(None, allownone=True)
    
    def on_pre_enter(self, *args):
        # Local storage.
        app = App.get_running_app()
        if app.settings.is_local_storage_enabled and not app.data_mgr.is_data_saved:
            app.data_mgr.write_data_to_files()
        # Upload.
        self.upload_btn_enabled = app.settings.is_upload_enabled and (not app.data_mgr.is_invalid)
        self._set_msg()
        Clock.schedule_once(lambda dt: self.topbar.update_icons(), 0)
    
    def _set_msg(self):
        self.msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"
        if self.upload_btn_enabled:
            self.msg += _("You can now [b]upload[/b] the research data by pressing the button below. This may take up "
                          "to [i]30 seconds[/i], because the receiving server may have to start up first. "
                          "By uploading the data you are making an important contribution to scientific research."
                          "Unless stated otherwise in the study's description we'd appreciate if you only upload "
                          "your data the first time you participated in this study. Thank you.\n")
        # Local storage.
        app = App.get_running_app()
        dest = app.data_mgr.get_storage_path()
        if app.data_mgr.is_data_saved:
            self.msg += _("Files were{} saved to [i]{}[/i].\n").format('' if dest.exists() else _(' [b]not[/b]'), dest)
        else:
            self.msg += _("Research data were [b]not[/b] locally stored as files. "
                          "You can enable storing research data on the device in the settings. This, however, is only "
                          "useful to researchers in a laboratory setting with access to the files.\n")
        
    def on_upload(self):
        # Show we're busy. Heroku dyno sleeps so it can take some time for the response.
        if not self.popup_block:
            self.popup_block = BlockingPopup(title=_("Uploading..."), text=_("Waking up server.\nPlease be patient."))
        self.popup_block.open()
        app = App.get_running_app()
        # Workaround to make info popup show up.
        Clock.schedule_once(lambda dt: app.data_mgr.upload_data(app.get_upload_route()), 0)
        self.popup_block.dismiss()
