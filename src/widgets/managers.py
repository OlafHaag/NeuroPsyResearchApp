import webbrowser

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty, ConfigParserProperty
from kivy.clock import Clock

import plyer

from . import (ScreenConsentCircleTask,
               ScreenInstructCircleTask,
               ScreenCircleTask,
               ScreenOutro,
               SimplePopup,
               BlockingPopup,
               ConfirmPopup,
               LanguagePopup,
               TermsPopup,
               PolicyPopup,
               UsersPopup,
               UserEditPopup,
               TextInputPopup,
               NumericInputPopup,
               DemographicsPopup,
               )
from ..i18n import _
from ..utility import get_app_details

screen_map = {'Consent CT': ScreenConsentCircleTask,
              'Instructions CT': ScreenInstructCircleTask,
              'Circle Task': ScreenCircleTask,
              'Outro': ScreenOutro,
              }


class UiManager(ScreenManager):
    """ This class handles all major screen changes, popups and callbacks related to that. """
    settings = ObjectProperty()
    sidebar = ObjectProperty(None, allownone=True)
    # Different kinds of popups, objects stay in memory and only show with replaced content.
    # To avoid garbage collection of Popups and resulting ReferenceError because of translations, keep a reference.
    popup_language = ObjectProperty(None, allownone=True)
    popup_terms = ObjectProperty(None, allownone=True)
    popup_info = ObjectProperty(None, allownone=True)
    popup_warning = ObjectProperty(None, allownone=True)
    popup_error = ObjectProperty(None, allownone=True)
    popup_user_select = ObjectProperty(None, allownone=True)
    popup_user_edit = ObjectProperty(None, allownone=True)
    popup_user_remove = ObjectProperty(None, allownone=True)
    popup_about = ObjectProperty(None, allownone=True)
    popup_privacy = ObjectProperty(None, allownone=True)
    #
    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)
    orientation = ConfigParserProperty('portrait', 'General', 'orientation', 'app', val_type=str, force_dispatch=True)
    
    def __init__(self, **kwargs):
        super(UiManager, self).__init__(**kwargs)
        self.app = App.get_running_app()
        # Keep track of where we cae from.
        self.last_visited = 'Home'
        self.n_home_esc = 0  # Counter on how many times the back button was pressed on home screen.
        # Keep track of what study we're currently performing.
        self.task_consents = {'Circle Task': 'Consent CT'}
        self.task_instructions = {'Circle Task': 'Instructions CT'}
        # Events
        self.register_event_type('on_info')
        self.register_event_type('on_warning')
        self.register_event_type('on_error')
        self.register_event_type('on_invalid_session')
        self.register_event_type('on_upload_response')
        self.register_event_type('on_upload_successful')
    
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        # Binds need to be executed 1 frame after on_kv_post, otherwise it tries to bind to not yet registered events.
        Clock.schedule_once(lambda dt: self.bind_sidebar_callbacks(), 1)
        if self.is_first_run:
            Clock.schedule_once(lambda dt: self.show_popup_language(), 1)  # Doesn't open otherwise.
    
    def bind_sidebar_callbacks(self):
        """ Handle events in navigation drawer. """
        # Handle sidebar item callbacks.
        root = self.parent.parent
        nav = root.ids.content_drawer
        nav.bind(on_home=lambda x: self.go_home(),
                 on_users=lambda x: self.show_user_select(),
                 on_settings=lambda x: self.open_settings(),
                 on_website=lambda x: self.open_website(self.settings.server_uri),
                 on_about=lambda x: self.show_about(),
                 on_terms=lambda x: self.show_terms(),
                 on_privacy_policy=lambda x: self.show_privacy_policy(),
                 on_exit=lambda x: self.quit(),
                 )
    
    def bind_screen_callbacks(self, screen_name):
        """ Handle screen callbacks here. """
        # Circle
        if screen_name == 'Consent CT':
            self.get_screen(screen_name).bind(on_consent=self.show_popup_demographics)
        elif screen_name == 'Circle Task':
            self.get_screen(screen_name).bind(
                on_task_stopped=lambda instance, is_last_block: self.task_finished(is_last_block),
                on_warning=lambda instance, text: self.show_warning(text),
            )
        # Webview
        elif screen_name == 'Webview':
            self.get_screen(screen_name).bind(on_quit_screen=lambda instance: self.go_home())
    
    def toggle_orientation(self, instance):
        """ Toggles between portrait and landscape screen orientation. """
        # Update the icon.
        instance.icon = f'phone-rotate-{self.orientation}'
        # Switch orientation.
        if self.orientation == 'portrait':
            self.orientation = 'landscape'
        elif self.orientation == 'landscape':
            self.orientation = 'portrait'
            
    def on_orientation(self, instance, value):
        try:
            if value == 'landscape':
                plyer.orientation.set_landscape()
            elif value == 'portrait':
                plyer.orientation.set_portrait()
        except (NotImplementedError, ModuleNotFoundError):
            pass
        
    def open_settings(self):
        self.app.open_settings()
        self.sidebar.set_state('close')
        
    def open_website(self, url):
        webbrowser.open_new(url)

    def show_popup_language(self):
        """ Popup for language choice on first run of the app. """
        if not self.popup_language:
            self.popup_language = LanguagePopup()
            self.popup_language.bind(on_language_set=self.on_language_set)
        self.popup_language.open()
    
    def on_language_set(self, *args):
        """ After language was set for first run. """
        self.show_terms()
        # Once we accepted the terms, we don't want the language popup's on_current_language event to trigger the terms.
        self.remove_popup_language()
        self.get_screen('Home').set_text()
        
    def remove_popup_language(self):
        if self.popup_language:
            self.popup_language.unbind(on_language_set=self.on_language_set)
            #self.popup_language = None
        
    def show_terms(self):
        if not self.popup_terms:
            self.popup_terms = TermsPopup()
        self.popup_terms.open()
        
    def show_privacy_policy(self):
        if not self.popup_privacy:
            self.popup_privacy = PolicyPopup()
        self.popup_privacy.open()
    
    def show_user_select(self):
        if not self.popup_user_select:
            self.popup_user_select = UsersPopup()
            self.popup_user_select.bind(on_add_user=lambda instance: self.show_user_edit(add=True,
                                                                                         user_alias=_("New User")),
                                        on_edit_user=lambda instance, user_id, alias: self.show_user_edit(
                                                                                                    user_id=user_id,
                                                                                                    user_alias=alias),
                                        on_remove_user=lambda instance, user_id, alias: self.show_user_remove(user_id,
                                                                                                              alias),
                                        )
        self.popup_user_select.open()
    
    def show_user_edit(self, add=False, user_id=None, user_alias=''):
        if not self.popup_user_edit:
            self.popup_user_edit = UserEditPopup()
            self.popup_user_edit.bind(on_user_edited=self.settings.edit_user)
        self.popup_user_edit.open(add=add, user_id=user_id, user_alias=user_alias)
        
    def show_user_remove(self, user_id, user_alias):
        if not self.popup_user_remove:
            self.popup_user_remove = ConfirmPopup()
            # Now do some hacky stuff. ;)
            setattr(self.popup_user_remove, 'user_id', user_id)
            self.popup_user_remove.bind(on_confirm=lambda instance: self.settings.remove_user(
                                                                                        self.popup_user_remove.user_id))
            self.settings.bind(on_user_removed=lambda instance, user: self.popup_user_select.remove_item(user))
        self.popup_user_remove.title = _("Do you want to remove {}?").format(user_alias)
        setattr(self.popup_user_remove, 'user_id', user_id)
        self.popup_user_remove.open()
        
    def show_about(self):
        # ToDo: own popup class with scrollview.
        details = get_app_details()
        self.show_info(title=_("About"),
                       text=_("{appname}\n"  # Alternatively self.app.get_application_name()
                              "Version: {version}\n"
                              "\n"
                              "Author: {author}\n"
                              "Contact: [ref=mailto:{contact}][color=0000ff]{contact}[/color][/ref]\n"
                              "Source Code: [ref={source}][color=0000ff]{source}[/color][/ref]\n"
                              "\n"
                              "This app uses third-party solutions that may not be governed by the same license.\n"
                              "Third-Party Licenses: [ref={thirdparty}][color=0000ff]{thirdparty}[/color][/ref]"
                              ).format(appname=details['appname'],
                                       author=details['author'],
                                       contact=details['contact'],
                                       version=details['version'],
                                       source=details['source'],
                                       thirdparty=details['third-party'],
                                       ),
                       )
            
    def on_info(self, title=None, text=None):
        self.show_info(title=title, text=text)
    
    def show_info(self, title=None, text=None):
        if not self.popup_info:
            self.popup_info = SimplePopup()
            # Hack for making about dialog to fit into screen.
            self.popup_info.bind(on_dismiss=lambda instance: setattr(self, 'popup_info', None))
        if title:
            self.popup_info.title = title
        if text:
            self.popup_info.text = text
        self.popup_info.open()
    
    def on_warning(self, text):
        self.show_warning(text)
        
    def show_warning(self, text=None):
        if not self.popup_warning:
            self.popup_warning = SimplePopup(title=_("Warning"))
        if text:
            self.popup_warning.text = text
        self.popup_warning.open()
    
    def on_error(self, text):
        self.show_error(text)
    
    def show_error(self, text=None):
        if not self.popup_error:
            self.popup_error = SimplePopup(title=_("Error"))
        if text:
            self.popup_error.text = text
        self.popup_error.open()
    
    def show_popup_demographics(self, *args):
        popup = DemographicsPopup()
        # ToDo: This was a quick hack, don't want data_mgr reference here. Should keep separate.
        popup.bind(on_confirm=lambda instance, *largs: self.app.data_mgr.add_user_data(*largs))
        popup.open()
        
    def on_current(self, instance, value):
        """ When switching screens reset counter on back button presses on home screen. """
        if not self.has_screen(value):
            if value in screen_map:
                self.add_widget(screen_map[value](name=value))
                self.bind_screen_callbacks(value)
            else:
                return
            
        screen = self.get_screen(value)
        # Handle navbar access.
        try:
            if screen.navbar_enabled:
                self.sidebar.set_disabled(False)
            else:
                self.sidebar.set_disabled(True)
        except AttributeError:
            pass
        
        # Handle reset of back button presses on home screen.
        if screen != self.current_screen:
            self.n_home_esc = 0
        super(UiManager, self).on_current(instance, value)
    
    def on_upload_response(self, status, error_msg=None):
        if status is True:
            self.show_info(title=_("Success!"), text=_("Upload successful!"))
            # Inform whatever widget needs to act now.
            self.dispatch('on_upload_successful')
        else:
            if not error_msg:
                error_msg = _("Upload failed.\nSomething went wrong.")
            error_msg += "\n" + _("Please make sure the app is up-to-date.")
            self.show_error(text=error_msg)
    
    def on_upload_successful(self):
        pass
    
    def key_input(self, window, key, scancode, codepoint, modifier):
        """ Handle escape key / back button presses. """
        if platform == "android":
            back_keys = [27]
        else:
            back_keys = [27, 278]  # backspace = 8, but would need to check if we're typing in an input mask.
        if key in back_keys:  # backspace, escape, home keys.
            # Handle back button on popup dialogs:
            if self.app.root_window.children[0] == self.popup_terms:
                if self.is_first_run:
                    self.quit()
                else:
                    self.popup_terms.dismiss()
            elif self.app.root_window.children[0] == self.popup_user_select:
                self.popup_user_select.dismiss()
            elif self.app.root_window.children[0] == self.popup_user_edit:
                self.popup_user_edit.dismiss()
            elif isinstance(self.app.root_window.children[0], (SimplePopup,
                                                               ConfirmPopup,
                                                               TextInputPopup,
                                                               NumericInputPopup,)):
                self.app.root_window.children[0].dismiss()
            elif isinstance(self.app.root_window.children[0], DemographicsPopup):
                self.app.root_window.children[0].dismiss()
                self.go_home()
            elif isinstance(self.app.root_window.children[0], BlockingPopup):
                return True  # Do nothing. # ToDo: prevent closing follow-up popup.
            elif self.sidebar.state == 'open':
                self.sidebar.set_state('close')
            # Handle back button on screens.
            elif self.current == 'Home':
                # When on home screen we want to be able to quit the app after 2 presses.
                self.n_home_esc += 1
                if self.n_home_esc == 1:
                    plyer.notification.notify(message=_("Press again to quit."), toast=True)
                if self.n_home_esc > 1:
                    self.quit()
            elif self.current == 'Outro' and self.last_visited == 'Settings':
                # self.current == 'Settings' would never get called,
                # as screen already changed by app.close_settings() on esc.
                return True
            # If we are in a task, stop that task.
            elif self.current in ['Circle Task']:
                self.get_screen(self.current).stop_task(interrupt=True)
                self.go_home()
            elif self.current == 'Webview':
                self.get_screen('Webview').key_back_handler()
                self.go_home()
            else:
                self.go_home()
            return True  # override the default behaviour
        else:  # the key now does nothing
            return False
    
    def go_home(self, transition='down'):
        self.transition.direction = transition
        self.current = 'Home'
        self.sidebar.set_state('close')
    
    def start_task(self, task):
        # Make sure the correct user is selected.
        self.show_user_select()
        self.transition.direction = 'up'
        self.transition.duration = 0.5
        self.app.settings.current_task = task
        self.current = self.task_consents[task]
        
    def task_finished(self, was_last_block=False):
        # Outro after last block.
        if was_last_block:
            self.current = 'Outro'
        else:
            self.transition.direction = 'down'
            self.current = self.task_instructions[self.settings.current_task]
    
    def on_invalid_session(self, *args):
        """ Default event implementation. """
        pass
    
    def quit(self, *args):
        self.app.stop()
