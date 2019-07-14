from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty

from plyer import notification

from src.i18n import _


class UCMManager(ScreenManager):
    settings = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(UCMManager, self).__init__(**kwargs)
        self.n_home_esc = 0  # Counter on how many times the back button was pressed on home screen.
        self.task_instructions = {'Circle Task': 'Instructions CT'}
    
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        self.get_screen('Circle Task').bind(on_task_stopped=lambda obj, last: self.task_finished(last))
        # self.get_screen('Webview').bind(on_quit_screen=lambda obj: self.go_home())
    
    def on_current(self, instance, value):
        """ When switching screens reset counter on back button presses on home screen. """
        screen = self.get_screen(value)
        if screen != self.current_screen:
            self.n_home_esc = 0
        super(UCMManager, self).on_current(instance, value)
    
    def key_input(self, window, key, scancode, codepoint, modifier):
        """ Handle escape key / back button presses. """
        if key == 27:
            if self.current == 'Home':
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
    
    def go_home(self):
        self.transition.direction = 'down'
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
