import json

from .i18n import _, list_languages, language_code_to_translation

LANGUAGE_CODE = "language"
LANGUAGE_SECTION = "Localization"


def get_settings_general_json():
    settings_json = json.dumps([
        {'type': 'optionmapping',
         'title': _("Language"),
         'desc': _("Display language for user interface."),
         'section': LANGUAGE_SECTION,
         'key': LANGUAGE_CODE,
         'options': {code: language_code_to_translation(code)
                     for code in list_languages()}},
        {'type': 'title',
         'title': _('Data Collection')},
        {'type': 'bool',
         'title': _('Local Storage'),
         'desc': _('Save data locally on device.'),
         'section': 'DataCollection',
         'key': 'is_local_storage_enabled'},
        {'type': 'bool',
         'title': _('Upload Data'),
         'desc': _('Offer to send collected data to server.'),
         'section': 'DataCollection',
         'key': 'is_upload_enabled'},
        {'type': 'string',
         'title': _('Upload Server'),
         'desc': _('Target server address to upload data to.'),
         'section': 'DataCollection',
         'key': 'webserver'},
        {'type': 'bool',
         'title': _('Send E-Mail'),
         'desc': _('Offer to send collected data via e-mail.'),
         'section': 'DataCollection',
         'key': 'is_email_enabled'},
    ])
    return settings_json


def get_settings_circle_task_json():
    settings_json = json.dumps([
        {'type': 'title',
         'title': _('PLEASE ONLY CHANGE THESE VALUES IF YOU ARE THE RESEARCHER')},
        {'type': 'numeric',
         'title': _('Number of practice trials'),
         'desc': _('Practice trials per condition.'),
         'section': 'CircleTask',
         'key': 'n_practice_trials'},
        {'type': 'numeric',
         'title': _('Number of trials'),
         'desc': _('Trials per block.'),
         'section': 'CircleTask',
         'key': 'n_trials'},
        {'type': 'numeric',
         'title': _('Number of Blocks'),
         'desc': _('Number of subsequent blocks per run.'),
         'section': 'CircleTask',
         'key': 'n_blocks'},
        {'type': 'numeric',
         'title': _('Constrained-Task Block'),
         'desc': _('Which of the blocks has the constrained task.'),
         'section': 'CircleTask',
         'key': 'constrained_block'},
        {'type': 'numeric',
         'title': _('Warm Up'),
         'desc': _('Pause before each trial to get ready. In seconds.'),
         'section': 'CircleTask',
         'key': 'warm_up_time'},
        {'type': 'numeric',
         'title': _('Trial Duration'),
         'desc': _('Countdown timer, in seconds.'),
         'section': 'CircleTask',
         'key': 'trial_duration'},
        {'type': 'numeric',
         'title': _('Cool Down'),
         'desc': _('Pause after each trial, in seconds.'),
         'section': 'CircleTask',
         'key': 'cool_down_time'},
        {'type': 'string',
         'title': _('E-Mail Recipient'),
         'desc': _('E-mail address to send data to.'),
         'section': 'CircleTask',
         'key': 'email_recipient'},
    ])
    return settings_json
