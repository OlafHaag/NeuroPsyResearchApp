from configparser import ConfigParser
from hashlib import md5
import re
from typing import List, Callable
from uuid import uuid4

from kivy import platform
from kivy.core.window import Window

from plyer import uniqueid

from .i18n import _, change_language_to
from . import __version__ as app_version

# Conditional imports
if platform == 'android':
    from android.permissions import request_permission, check_permission, Permission
    from jnius import autoclass
else:
    class Permission:
        INTERNET = (
            "android.permission.INTERNET"
        )
        WRITE_EXTERNAL_STORAGE = (
            "android.permission.WRITE_EXTERNAL_STORAGE"
        )


# Variables.
time_fmt = '%Y_%m_%d_%H_%M_%S'  # For safe usage as file name.


# Function declarations.
if platform == 'win':
    def get_screensize():
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return screensize
else:
    def get_screensize():
        return Window.width, Window.height


def is_window_landscape():
    """ Return whether window is landscape or portrait. """
    if platform == 'android':
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        config = activity.getResources().getConfiguration()
        if config.orientation == 1:
            return False
        elif config.orientation == 2:
            return True
    else:
        width, height = get_screensize()
        return width > height
    
    
def switch_language(lang='en'):
    """ Change displayed translation. """
    try:
        # Popups and settings could be simplified by using change_language_to_translated() instead,
        # but since language name is written in its own language there could be UTF-8 issues when saving to config file.
        change_language_to(lang)
    except ReferenceError:
        # I spent hours trying to fix it. Now I just don't care anymore.
        print(f"WARNING: Couldn't translate everything. Possible weakref popups that don't exist anymore.")


def create_device_identifier(**kwargs):
    """ Returns an identifier for the hardware. """
    uid = uniqueid.get_uid().encode()
    hashed = md5(uid).hexdigest()
    # Shorten and lose information.
    ident = hashed[::4]
    return ident


def create_user_identifier(**kwargs):
    """ Return unique identifier for user. """
    uuid = uuid4().hex
    return uuid


def _on_permission_result(permissions, grant_results):
    """ Dummy callback for results of requested permissions.
    :type permissions: List[str]
    :type grant_results: List[bool]
    """
    pass


def ask_permission(permission, callback=_on_permission_result):
    """ Necessary on Android to request permission for certain actions.
    Returns immediate check for permissions and doesn't wait for results of request.
    Once results of request are in the callback must handle those.
    
    Note that if the request is interrupted the callback may contain an empty list of permissions,
    without permissions being granted. The App should check that each permission requested has been granted.
    
    :type permission: str
    :type callback: Callable
    :rtype: bool
    """
    if platform == 'android':
        # request_permissions should only be called with a callback
        # if calling check_permission has indicated that it is necessary.
        got_permission = check_permission(permission)
        if not got_permission:
            request_permission(permission, callback=callback)
        # Return doesn't wait for request's results. So it's False if permissions have not yet been granted.
        return got_permission
    # For any other platform assume given permission.
    return True


def get_app_details():
    """ Get app's name, author and contact information. """
    try:
        with open('android.txt') as f:
            file_content = '[dummy_section]\n' + f.read()
    except IOError:
        print("WARNING: android.txt wasn't found! Setting app details to " + _("UNKNOWN."))
        return {'appname': _("UNKNOWN."), 'author': _("UNKNOWN."), 'contact': _("UNKNOWN.")}
    
    config_parser = ConfigParser()
    config_parser.read_string(file_content)
    details = {'appname': config_parser.get('dummy_section', 'title', fallback=_("UNKNOWN.")),
               'author': config_parser.get('dummy_section', 'author', fallback=_("UNKNOWN.")),
               'contact': config_parser.get('dummy_section', 'contact', fallback=_("UNKNOWN.")),
               'source': config_parser.get('dummy_section', 'source', fallback=_("UNKNOWN.")),
               'third-party': config_parser.get('dummy_section', '3rdPartyLicenses', fallback=_("UNKNOWN.")),
               'webserver': config_parser.get('dummy_section', 'webserver', fallback="http://127.0.0.1:5000"),
               'version': app_version,
               }
    return details


# Code based on https://gist.github.com/sma/1513929
# and https://github.com/evandrocoan/MarkdownToBBCode/blob/master/MarkdownToBBCode.py
def markdown_to_bbcode(s):
    """ Convert markdown tags to kivy style bbcode tags.
    Does not always work reliably. Best to not mix URLs and tags on the same line in markdown.
    
    :type s: str
    """
    
    def tags_in_excepted_portion(text, start_index, end_index, exception_regex):
        """ Valid entrances are:
            _start without space between the _ and the first and last word.
            multilines are allowed. But one empty line gets out the italic mode._
            No effect inside URLs.
        """
        
        matches_iterator = re.finditer(exception_regex, text)
        
        for match in matches_iterator:
            match_start = match.start(0)
            match_end = match.end(0)
            
            if ((match_start <= start_index) and (start_index <= match_end)) \
                    or ((match_start <= end_index) and (end_index <= match_end)):
                return True
        return False
    
    def single_tag_context_parser(text, regex_expression, bb_code_tag, replacement_size=1):
        """ Valid entrances are:
            _start without space between the _ and the first and last word.
            multilines are allowed. But one empty line get out the italic mode._
            No effect inside URLs.
        """
    
        # Used to count how many iterations are necessary on the worst case scenario.
        matches_iterator = re.finditer(regex_expression, text)
    
        # The exclusion pattern to remove wrong blocks from being parsed.
        next_search_position = 0
    
        # Iterate until all the initial matches list to finish.
        for element in matches_iterator:
        
            # To perform a new search on the new updated string.
            match = re.search(regex_expression, text[next_search_position:])
        
            # Exit the parsing iteration when not more matches are found.
            if match is None:
                break
        
            start_index = match.start(0)
            end_index = match.end(0)
        
            start_index = start_index + next_search_position
            end_index = end_index + next_search_position
        
            next_search_position = start_index + replacement_size
            
            # Exclude from URLs.
            if tags_in_excepted_portion(text, start_index, end_index,
                                        # Also exclude gender asterisk in German.
                                        r"(<(https?:\S+)>)|(\[(.*?)\]\((.*?)\))|\w+\*([^.\s\n]*\w+)"):
                continue
        
            if end_index + replacement_size > len(text):
            
                text = text[0: start_index] \
                       + "[{0}]".format(bb_code_tag) \
                       + text[start_index + replacement_size: end_index] \
                       + "[/{0}]".format(bb_code_tag)
        
            else:
            
                text = text[0: start_index] \
                       + "[{0}]".format(bb_code_tag) \
                       + text[start_index + replacement_size: end_index] \
                       + "[/{0}]".format(bb_code_tag) \
                       + text[end_index + replacement_size:]
        return text

    def translate(formatting_rule="%s", target_group=1):
        def inline(match_object):
            """ Recursive function called by the `re.sub` for every non-overlapping occurrence of the pattern.
                
                :param match_object: An `sre.SRE_Match object` match object.
            """
            s = match_object.group(target_group)
            # Headers
            s = re.sub(r"^#\s+(.*?)\s*$", "[size=24dp][b]\\1[/b][/size]", s)  # Header first level
            s = re.sub(r"^##\s+(.*?)\s*$", "[size=20dp][b]\\1[/b][/size]", s)  # Header second level
            s = re.sub(r"^###\s+(.*?)\s*$", "[b]\\1[/b]", s)  # Header third level
            s = re.sub(r"^####\s+(.*?)\s*$", "[i][b]\\1[/b][/i]", s)  # Header fourth level
            
            # > Quote
            s = re.sub(r"^> (.*)$", "[color=A9A9A9]\\1[/color]", s)
            return formatting_rule % s
        
        return inline
    
    # Bold and italic.
    # It re-uses several expressions, needs to be parsed before everything else,
    # because it needs several hacks (?<=\s), as `_` symbol is often used in URLs.
    s = single_tag_context_parser(s, r"\*\*[^ \n]([^\*]+?)[^ \n](?=\*\*)", "b", 2)  # **Bold**
    s = single_tag_context_parser(s, r"{0}[^ \n]([^{0}]+?)[^ \n](?={0})".format("\*"), "i")  # *Italic*
    s = single_tag_context_parser(s, r"__[^ \n]([^_]+?)[^ \n](?=__)", "b", 2)  # __Bold__
    s = single_tag_context_parser(s, r"{0}[^ \n]([^{0}]+?)[^ \n](?={0})".format("_"), "i")  # _Italic_
    s = single_tag_context_parser(s, r"~~[^ \n]([\s\S]+?)[^ \n](?=~~)", "s", 2)  # ~Strikethrough~
    
    # URLs. Kivy Label style.
    s = re.sub(r"<(https?:\S+)>", "[color=0000ff][ref=\"\\1\"]\\1[/ref][/color]", s)
    s = re.sub(r"\[(.*?)\]\((.*?)\)", "[color=0000ff][ref=\"\\2\"]\\1[/ref][/color]", s)
    
    s = re.sub(r"(?m)^((?!~).*)$", translate(), s)
    s = re.sub(r"\[/quote]\n\[quote]", "\n", s)
    
    return s


def create_markdown_file(path, content_md):
    """ Write markdown file and fill in app-details.
    This is useful in production when you want to have in-app policies synchronized with online policies.
    """
    details = get_app_details()
    text = content_md.format(appname=details['appname'], author=details['author'], contact=details['contact'],
                             source=details['source'])
    path.write_text(text, encoding='UTF-8')
