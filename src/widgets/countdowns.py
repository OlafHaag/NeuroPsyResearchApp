from kivy.uix.label import Label
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivymd.uix.label import MDLabel


class CountDownCircle(MDLabel):
    start_count = NumericProperty(
        3)  # Initial duration, replaced with CircleGame.trial_duration by ScreenCircleTask class.
    angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        kwargs.update(dict(halign='center'))
        super(CountDownCircle, self).__init__(**kwargs)
        self.register_event_type('on_count_down_finished')
        self.anim = None
    
    def start(self):
        self.angle = 0
        Animation.cancel_all(self)
        self.anim = Animation(angle=360, duration=self.start_count)
        self.anim.bind(on_complete=lambda animation, obj: self.finished())
        self.anim.start(self)
    
    def finished(self):
        self.dispatch('on_count_down_finished')
    
    def on_count_down_finished(self):
        pass
    
    def set_label(self, msg):
        self.text = msg
