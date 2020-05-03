from configparser import ConfigParser
import webbrowser

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ConfigParserProperty
from kivy.clock import Clock

from . import LanguagePopup, BlockingPopup

from ..i18n import _


class ScreenHome(Screen):
    """ Display that gives general information. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    home_msg = StringProperty(_('Initiating...'))
    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)
    popup_lang = ObjectProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        # Procedure related.
        self.register_event_type('on_language_changed')
        
    def on_pre_enter(self, *args):
        """ Reset data collection each time before a new task is started. """
        App.get_running_app().settings.reset_current()
        self.home_msg = _('Welcome!')  # ToDo: General Information
    
        app = App.get_running_app()
        app.reset_data_collection()

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

    def visit_website(self):
        webbrowser.open_new(self.settings.server_uri)
