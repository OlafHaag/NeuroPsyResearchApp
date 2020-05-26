from kivy.uix.slider import Slider


class ScaleSlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_grab')
        self.register_event_type('on_ungrab')
        super(ScaleSlider, self).__init__(**kwargs)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_grab', touch)
        return super(ScaleSlider, self).on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # Give us more wiggle room for determining if the touch_up event happened on this slider.
        if (self.x - 80) <= touch.pos[0] <= (self.right + 80) and self.y <= touch.pos[1] <= self.top:
            self.dispatch('on_ungrab', touch)
        return super(ScaleSlider, self).on_touch_up(touch)
    
    def on_grab(self, *args):
        pass

    def on_ungrab(self, *args):
        pass
