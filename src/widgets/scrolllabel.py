"""
Copyright (c) 2010-2015 Kivy Team and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
# Based on: https://github.com/noembryo/garden.scrolllabel

import re

from kivy.core.text import Label as CoreLabel
from kivy.logger import Logger
from kivy.metrics import sp
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import (NumericProperty, StringProperty, OptionProperty,
                             BooleanProperty, AliasProperty, ListProperty)
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

from kivy.graphics import Color, Rectangle  # Used in debug marking ref zones.

from ..i18n import _


class ScrollText(MDBoxLayout):
    text = StringProperty(_('Loading...'))
    
    def __init__(self, **kwargs):
        self.text = kwargs.pop('text', _("not found"))
        self.height = (Window.height * 0.8) - 80  # Adjust: height of ScrollText
        super(ScrollText, self).__init__(**kwargs)
        
        
class TextLine(MDLabel):
    def _get_rect_x(self):
        if self.halign in ["left", "justify"]:
            return 0
        elif self.halign == "center":
            ret = (self.width - self.texture_size[0]) / 2.
        else:
            ret = self.width - self.texture_size[0]
        return int(ret)

    _rect_x = AliasProperty(_get_rect_x, bind=("texture_size", "x", "width"))
    
    def on_ref_press(self, ref):
        self.parent.parent.parent.dispatch('on_ref_press', ref)
        #self._show_ref_bbox()
        
    def _show_ref_bbox(self):
        """ Debug ref-zone marker. """
        for name, boxes in self.refs.items():
            for box in boxes:
                with self.canvas:
                    Color(0, 1, 0, 0.25)
                    x_off = self._get_rect_x()
                    Rectangle(pos=(box[0]+x_off, box[1]+self.y),
                              size=(box[2] - box[0],
                                    box[3] - box[1]))


class RecycleLabel(Widget):
    """ Scrollable label with support for long texts.
    When kivy labels hold too much text they exceed the maximum texture size the GPU can handle.
    This uses the RecycleView to try to overcome this limitation.
    
    Issues:
        - Can remove spaces in marked up text.
        - halign 'justify' isn't working.
    """
    text = StringProperty()
    font_size = NumericProperty(sp(14))
    font_name = StringProperty("Roboto")
    halign = OptionProperty("center", options=("left", "center", "right", "justify"))  # ToDo: justify isn't working.
    line_height = NumericProperty()
    markup = BooleanProperty(False)
    color = ListProperty([1, 1, 1, 1])
    outline_width = NumericProperty(None)
    lines = ListProperty()

    def __init__(self, **kwargs):
        super(RecycleLabel, self).__init__(**kwargs)
        self.register_event_type('on_ref_press')
        self._style_stack = {}
        self._trigger_refresh_label = Clock.create_trigger(self.refresh_label)
        self.bind(text=self._trigger_refresh_label,
                  font_size=self._trigger_refresh_label,
                  font_name=self._trigger_refresh_label,
                  halign=self._trigger_refresh_label,
                  width=self._trigger_refresh_label,
                  markup=self._trigger_refresh_label,
                  outline_width=self._trigger_refresh_label,
                  )
        self._trigger_refresh_label()

    def get_markup_elements(self, text):
        """ Return the text with all the markup splitted into elements. """
        s = re.split('(\[.*?\])', text)
        s = [x for x in s if x != '']
        return s
    
    def get_lines(self, cached_lines):
        """ Returns text in cached lines as strings. """
        lines = [line.words[0].text if len(line.words) else "" for line in cached_lines]
        return lines
        
    def _push_style(self, k):
        if k not in self._style_stack:
            self._style_stack[k] = 0
        self._style_stack[k] += 1

    def _pop_style(self, k):
        if k not in self._style_stack or not self._style_stack[k]:
            #Logger.warning(f"Label: style {k} was not pushed to stack. Unable to pop.")
            return
        self._style_stack[k] -= 1
        
    def is_style_stack_empty(self):
        """ Returns whether all opening tags havve matching closing tags. """
        return not bool(sum(self._style_stack.values()))
    
    def on_lines(self, instance, lines):
        """ When a line is changed process the contained style tags. """
        try:
            self._style_push_pop(lines[-1])
        except IndexError:
            pass
    
    def _concat_style_tags(self, lines):
        """ When opening and closing style tags are not in balance, merge the lines. """
        for line in lines:
            if not self.is_style_stack_empty():
                # Concatenate lines and check again.
                self._style_stack.clear()
                try:
                    self.lines[-1] += line  # ToDo: Missing spaces after concatenation. Because of stripped lines?
                except IndexError:
                    self.lines.append(line)
            else:
                self.lines.append(line)
            
    def _style_push_pop(self, line):
        """ Check the given line for any opening and closing style tags.
        Used to match style tags to one-another.
        """
        spush = self._push_style
        spop = self._pop_style
        markup = self.get_markup_elements(line)
        for item in markup:
            if item == '[b]':
                spush('bold')
            elif item == '[/b]':
                spop('bold')
            elif item == '[i]':
                spush('italic')
            elif item == '[/i]':
                spop('italic')
            elif item == '[u]':
                spush('underline')
            elif item == '[/u]':
                spop('underline')
            elif item == '[s]':
                spush('strikethrough')
            elif item == '[/s]':
                spop('strikethrough')
            elif item[:6] == '[size=':
                spush('font_size')
            elif item == '[/size]':
                spop('font_size')
            elif item[:7] == '[color=':
                spush('color')
            elif item == '[/color]':
                spop('color')
            elif item[:6] == '[font=':
                spush('font_name')
            elif item == '[/font]':
                spop('font_name')
            elif item[:13] == '[font_family=':
                spush('font_family')
            elif item == '[/font_family]':
                spop('font_family')
            elif item[:14] == '[font_context=':
                spush('font_context')
            elif item == '[/font_context]':
                spop('font_context')
            elif item[:15] == '[font_features=':
                spush('font_features')
            elif item == '[/font_features]':
                spop('font_features')
            elif item[:15] == '[text_language=':
                spush('text_language')
            elif item == '[/text_language]':
                spop('text_language')
            elif item[:5] == '[sub]':
                spush('font_size')
                spush('script')
            elif item == '[/sub]':
                spop('font_size')
                spop('script')
            elif item[:5] == '[sup]':
                spush('font_size')
                spush('script')
            elif item == '[/sup]':
                spop('font_size')
                spop('script')
            elif item[:5] == '[ref=':
                spush('_ref')
            elif item == '[/ref]':
                spop('_ref')
            elif '[/' in item:
                spop('unknown')
            elif '[' in item:
                spush('unknown')

    def refresh_label(self, *args):
        lcls = CoreLabel
        label = lcls(text=self.text,
                     text_size=(self.width, None),
                     halign=self.halign,
                     font_size=self.font_size,
                     font_name=self.font_name,
                     markup=self.markup,
                     outline_width=self.outline_width,
                     )
        label.resolve_font_name()
        label.render()  # Generates label._cached_lines.
        
        lines = self.get_lines(label._cached_lines)
        self.lines.clear()
        self._concat_style_tags(lines)

        # get lines
        font_name = self.font_name
        font_size = self.font_size
        halign = self.halign
        markup = self.markup
        color = self.color
        outline_width = self.outline_width
        data = ({"text": line,
                 "font_name": font_name,
                 "font_size": font_size,
                 "height": label._cached_lines[0].h,  # line.h,  # ToDo: proper line height
                 "size_hint_y": None,
                 "halign": halign,
                 "markup": markup,
                 "color": color,
                 "outline_width": outline_width,
                 } for line in self.lines)
        self.ids.rv.data = data

    def on_ref_press(self, ref):
        pass
