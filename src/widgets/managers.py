import webbrowser

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from plyer import notification

from . import (SimplePopup,
               BlockingPopup,
               ConfirmPopup,
               TermsPopup,
               UsersPopup,
               UserEditPopup,
               TextInputPopup,
               NumericInputPopup,
               )
from ..i18n import _
from ..utility import get_app_details


class UiManager(ScreenManager):
    """ This class handles all major screen changes, popups and callbacks related to that. """
    settings = ObjectProperty()
    sidebar = ObjectProperty(None, allownone=True)
    # Different kinds of popups, objects stay in memory and only show with replaced content.
    # To avoid garbage collection of Popups and resulting ReferenceError because of translations, keep a reference.
    popup_terms = ObjectProperty(None, allownone=True)
    popup_info = ObjectProperty(None, allownone=True)
    popup_warning = ObjectProperty(None, allownone=True)
    popup_error = ObjectProperty(None, allownone=True)
    popup_user_select = ObjectProperty(None, allownone=True)
    popup_user_edit = ObjectProperty(None, allownone=True)
    popup_user_remove = ObjectProperty(None, allownone=True)
    popup_about = ObjectProperty(None, allownone=True)

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
        self.register_event_type('on_upload_response')
        self.register_event_type('on_upload_successful')
    
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        # Binds need to be executed 1 frame after on_kv_post, otherwise it tries to bind to not yet registered events.
        Clock.schedule_once(lambda dt: self.bind_callbacks(), 1)
    
    def bind_callbacks(self):
        self.bind_sidebar_callbacks()
        self.bind_screen_callbacks()
    
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
                 on_exit=lambda x: self.quit(),
                 )
        
    def bind_screen_callbacks(self):
        """ Handle screen callbacks here. """
        # Home
        self.get_screen('Home').bind(on_language_changed=self.on_language_changed_callback)
        # Circle Task
        self.get_screen('Circle Task').bind(
            on_task_stopped=lambda instance, last: self.task_finished(last),
            on_warning=lambda instance, text: self.show_warning(text),
        )
        # Webview
        # self.get_screen('Webview').bind(on_quit_screen=lambda instance: self.go_home())
    
    def open_settings(self):
        self.app.open_settings()
        self.sidebar.set_state('close')
        
    def open_website(self, url):
        webbrowser.open_new(url)

    def on_language_changed_callback(self, *args):
        self.show_terms()
        
    def show_terms(self):
        if not self.popup_terms:
            self.popup_terms = TermsPopup()
        self.popup_terms.open()
    
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
        # ToDo: Link to Source Code
        details = get_app_details()
        self.show_info(title=_("About"),
                       text=_("{}\n\n"
                              "Author: {}\n"
                              "Contact: {}\n"
                              "Version: {}").format(details['appname'],  # Alternatively self.app.get_application_name()
                                                    details['author'],
                                                    details['contact'],
                                                    details['version']))
            
    def on_info(self, title=None, text=None):
        self.show_info(title=title, text=text)
    
    def show_info(self, title=None, text=None):
        if not self.popup_info:
            self.popup_info = SimplePopup()
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
        
    def on_current(self, instance, value):
        """ When switching screens reset counter on back button presses on home screen. """
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
                if self.popup_terms.is_first_run:
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
                                                               NumericInputPopup)):
                self.app.root_window.children[0].dismiss()
            elif isinstance(self.app.root_window.children[0], BlockingPopup):
                return True  # Do nothing. # FixMe: prevent closing follow-up popup.
            elif self.sidebar.state == 'open':
                self.sidebar.set_state('close')
            # Handle back button on screens.
            elif self.current == 'Home':
                # When on home screen we want to be able to quit the app after 2 presses.
                self.n_home_esc += 1
                if self.n_home_esc == 1:
                    notification.notify(message=_("Press again to quit."), toast=True)
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
    
    def quit(self, *args):
        self.app.stop()
