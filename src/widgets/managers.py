import webbrowser

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from plyer import notification

from . import TermsPopup
from ..i18n import _


class UCMManager(ScreenManager):
    """ This class handles all major screen changes, popups and callbacks related to that. """
    settings = ObjectProperty()
    sidebar = ObjectProperty(None, allownone=True)
    popup_terms = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(UCMManager, self).__init__(**kwargs)
        self.n_home_esc = 0  # Counter on how many times the back button was pressed on home screen.
        self.task_consents = {'Circle Task': 'Consent CT'}
        self.task_instructions = {'Circle Task': 'Instructions CT'}
    
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        
        # Handle screen callbacks.
        self.get_screen('Home').bind(on_language_changed=self.on_language_changed_callback)
        self.get_screen('Circle Task').bind(on_task_stopped=lambda obj, last: self.task_finished(last))
        # self.get_screen('Webview').bind(on_quit_screen=lambda obj: self.go_home())
        # NOTE: This seems to have be executed after on_kv_post, otherwise it tries to bind not yet registered events.
        Clock.schedule_once(lambda dt: self.bind_sidebar_callbacks(), 1)
    
    def bind_sidebar_callbacks(self):
        """ Bind events in navigation drawer to actions. """
        # Handle sidebar item callbacks.
        root = self.parent.parent
        nav = root.ids.content_drawer
        nav.bind(on_home=lambda x: self.go_home())
        nav.bind(on_users=lambda x: print("Users clicked!"))
        nav.bind(on_settings=lambda x: self.open_settings())
        nav.bind(on_website=lambda x: self.open_website(self.settings.server_uri))
        nav.bind(on_about=lambda x: print("About clicked!"))
        nav.bind(on_terms=lambda x: self.show_terms())
        nav.bind(on_exit=lambda x: self.quit())
    
    def open_settings(self):
        app = App.get_running_app()
        app.open_settings()
        self.sidebar.set_state('close')

    def open_website(self, url):
        webbrowser.open_new(url)
        
    def on_language_changed_callback(self, *args):
        # ToDo: Redraw home screen somehow. _trigger_layout()?
        self.show_terms()
        
    def show_terms(self):
        if not self.popup_terms:
            self.popup_terms = TermsPopup()
        self.popup_terms.open()
        
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
        super(UCMManager, self).on_current(instance, value)
    
    def key_input(self, window, key, scancode, codepoint, modifier):
        """ Handle escape key / back button presses. """
        if platform == "android":
            back_keys = [27]
        else:
            back_keys = [27, 278]  # backspace = 8, but would need to check if we're typing in an input mask.
        if key in back_keys:  # backspace, escape, home keys.
            # Handle back button on popup dialogs:
            if App.get_running_app().root_window.children[0] == self.popup_terms:
                if self.popup_terms.is_first_run:
                    self.quit()
                else:
                    self.popup_terms.dismiss()
            # ToDo: handle other popups on back key.
            #elif isinstance(App.get_running_app().root_window.children[0], SimplePopup):
                #App.get_running_app().root_window.children[0].dismiss()
            # Handle back button on screens.
            elif self.current == 'Home':
                # When on home screen we want to be able to quit the app after 2 presses.
                self.n_home_esc += 1
                if self.n_home_esc == 1:
                    notification.notify(message=_("Press again to quit."), toast=True)
                if self.n_home_esc > 1:
                    self.quit()
            elif self.current == 'Settings':
                # Never gets called, screen already changed to 'Home' through app.close_settings() on esc.
                App.get_running_app().close_settings()
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
    
    def go_home(self, dir='down'):
        self.transition.direction = dir
        self.current = 'Home'
        
    def task_finished(self, was_last_block=False):
        # Outro after last block.
        if was_last_block:
            self.current = 'Outro'
        else:
            self.transition.direction = 'down'
            self.current = self.task_instructions[self.settings.task]
    
    def quit(self, *args):
        App.get_running_app().stop()
