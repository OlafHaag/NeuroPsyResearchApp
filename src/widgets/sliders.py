from kivy.uix.slider import Slider


class ScaleSlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_grab')
        self.register_event_type('on_ungrab')
        self.register_event_type('on_leave')
        super(ScaleSlider, self).__init__(**kwargs)
    
    def is_touch_on_handle(self, touch, tolerance=1.0):
        handle = self.children[0]
        rx = handle.width * 0.5 * tolerance
        ry = handle.height * 0.5 * tolerance
        return ((handle.center_x - rx) <= touch.pos[0] <= (handle.center_x + rx) and
                (handle.center_y - ry) <= touch.pos[1] <= handle.center_y + ry)
            
    def on_touch_down(self, touch):
        if self.is_touch_on_handle(touch):
            self.dispatch('on_grab', touch)
        return super(ScaleSlider, self).on_touch_down(touch)
    
    def on_touch_up(self, touch):
        # Only dispatch when releasing the handle, not when clicking and releasing slider track.
        # Give us more wiggle room for determining if the touch_up event happened on this slider.
        if self.is_touch_on_handle(touch):
            self.dispatch('on_ungrab', touch)
        return super(ScaleSlider, self).on_touch_up(touch)
    
    def on_touch_move(self, touch):
        handle = self.children[0]
        rx = handle.width * 0.5
        # Only left-right check, moving handle fast loses track.
        if not (handle.center_x - rx) <= touch.pos[0] <= (handle.center_x + rx):
            self.dispatch('on_leave', touch)
        return super(ScaleSlider, self).on_touch_move(touch)
    
    def on_grab(self, *args):
        pass
    
    def on_ungrab(self, *args):
        pass
    
    def on_leave(self, *args):
        pass
