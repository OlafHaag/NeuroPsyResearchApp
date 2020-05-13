from configparser import ConfigParser

from kivy.app import App
from kivy.properties import (ObjectProperty,
                             StringProperty,
                             BooleanProperty,
                             ConfigParserProperty,
                             )
from kivy.clock import Clock

from . import BaseScreen
from . import LanguagePopup, BlockingPopup

from ..i18n import _


class ScreenHome(BaseScreen):
    """ Display that gives general information. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    home_msg = StringProperty(_('Loading...'))
    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)
    popup_lang = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        # Procedure related.
        self.register_event_type('on_language_changed')
    
    def on_pre_enter(self, *args):
        """ Reset data collection each time before a new task is started. """
        App.get_running_app().settings.reset_current()
    
        app = App.get_running_app()
        app.data_mgr.clear_data_collection()

        if self.is_first_run:
            # Wait 1 frame
            Clock.schedule_once(lambda dt: self.first_run_language_choice(), 1)

    def first_run_language_choice(self):
        if not self.popup_lang:
            self.popup_lang = LanguagePopup()
            self.popup_lang.bind(on_dismiss=lambda obj: self.dispatch('on_language_changed'))
        self.popup_lang.open()

    def on_language_changed(self):
        pass


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
            self.msg += _("Files were{} saved to [i]{}[/i].").format('' if dest.exists() else _(' [b]not[/b]'), dest)
        else:
            self.msg += _("Results were [b]not[/b] locally stored as files.\n"
                          "You can enable this in the settings.")
    
        self.upload_btn_enabled = app.settings.is_upload_enabled
        
    def on_upload(self):
        # Show we're busy. Heroku dyno sleeps so it can take some time for the response.
        if not self.popup_block:
            self.popup_block = BlockingPopup(title=_("Uploading..."), text=_("Waking up server.\nPlease be patient."))
        self.popup_block.open()
        app = App.get_running_app()
        # Workaround to make info popup show up.
        Clock.schedule_once(lambda dt: app.data_mgr.upload_data(app.get_upload_route()), 0)
        self.popup_block.dismiss()
