from kivy.uix.slider import Slider


class ScaleSlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_grab')
        super(ScaleSlider, self).__init__(**kwargs)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_grab', touch)
        return super(ScaleSlider, self).on_touch_down(touch)
    
    def on_grab(self, touch):
        pass
