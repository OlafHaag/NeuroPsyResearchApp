"""
Substantial portions of ScreenWebView class copyright (c) 2016 suchyDev (MIT License)
with code by Micheal Hines.

MIT License

Copyright (c) 2019 suchyDev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform

from src.config import WEBSERVER

if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass
    
    WebView = autoclass('android.webkit.WebView')
    CookieManager = autoclass('android.webkit.CookieManager')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
else:
    def run_on_ui_thread(func):
        """ dummy wrapper for desktop compatibility """
        return func
    
    
class ScreenWebView(Screen):
    """ Currently out of order. Crashes on create_webview!
    Shall display the analysed data after a session for individual feedback.
    """
    view_cached = None
    webview = None
    wvc = None
    webview_lock = False  # simple lock to avoid launching two webviews.
    url = StringProperty(WEBSERVER)
    
    def __init__(self, **kwargs):
        super(ScreenWebView, self).__init__(**kwargs)
        self.register_event_type('on_quit_screen')
    
    def on_enter(self, *args):
        super(ScreenWebView, self).on_enter(*args)
        
        self.url = App.get_running_app().settings.server_uri
        
        if platform == 'android':
            # On android create webview for website.
            self.ids['info_label'].text = _("Please wait\nAttaching WebView")
            self.webview_lock = True
            Clock.schedule_once(self.create_webview, 0)  # Call after the next frame.
        else:
            # On desktop just launch web browser.
            self.ids['info_label'].text = _("Please wait\nLaunching browser")
            import webbrowser
            webbrowser.open_new(self.url)
            
            # Only if we would want to manually upload data files.
            # if platform == 'win':
            #    subprocess.Popen(r'explorer "{}"'.format(App.get_running_app().get_data_path()))
    
    @run_on_ui_thread
    def key_back_handler(self, *args):
        if self.webview:
            Clock.schedule_once(self.detach_webview, 0)  # Call after the next frame.
    
    @mainthread
    def quit_screen(self, *args):
        self.dispatch('on_quit_screen')
    
    def on_quit_screen(self, *args):
        pass
    
    @run_on_ui_thread
    def create_webview(self, *args):  # FixMe: Crash - no attribute f2
        if self.view_cached is None:
            self.view_cached = activity.currentFocus
        self.webview = WebView(activity)
        
        cookie_manager = CookieManager.getInstance()
        cookie_manager.removeAllCookie()
        
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setUseWideViewPort(True)  # enables viewport html meta tags
        settings.setLoadWithOverviewMode(True)  # uses viewport
        settings.setSupportZoom(True)  # enables zoom
        settings.setBuiltInZoomControls(True)  # enables zoom controls
        settings.setSavePassword(False)
        settings.setSaveFormData(False)
        
        self.wvc = WebViewClient()
        self.webview.setWebViewClient(self.wvc)
        activity.setContentView(self.webview)
        self.webview.loadUrl(self.url)
        self.webview_lock = False
    
    @run_on_ui_thread
    def detach_webview(self, *args):
        if not self.webview_lock:
            if self.webview:
                self.webview.loadUrl("about:blank")
                self.webview.clearHistory()  # refer to android webview api
                self.webview.clearCache(True)
                self.webview.clearFormData()
                self.webview.freeMemory()
                # self.webview.pauseTimers()
                activity.setContentView(self.view_cached)
            Clock.schedule_once(self.quit_screen, 0)  # Call after the next frame.
