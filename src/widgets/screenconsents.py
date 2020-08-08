from kivy.app import App
from kivy.properties import StringProperty
from kivymd.uix.label import MDLabel
from plyer import email

from . import BaseScreen
from ..i18n import _
from ..utility import get_app_details


class ConsentLabel(MDLabel):
    """ Class with Pre-defined label style. Style defined in KV language. """
    pass


class ScreenConsentCircleTask(BaseScreen):
    """ Tell the user about conditions of participation and require consent. """
    title = StringProperty()
    
    def __init__(self, **kwargs):
        super(ScreenConsentCircleTask, self).__init__(**kwargs)
        self.register_event_type('on_consent')
    
    def on_ref(self, value):
        """ Handle clicks on links. """
        if value == 'privacy':
            self.manager.show_privacy_policy()
        elif value.startswith('mailto:'):
            recipient = value[7:]
            details = get_app_details()
            email.send(recipient=recipient, subject=f"{details['appname']}: Circle Task", create_chooser=True)
    
    def on_consent(self, *args):
        """ On to the next screen. We have consent, begin new data collection. """
        # Start collecting data for user_id.
        app = App.get_running_app()
        app.data_mgr.new_data_collection(app.settings.current_user)
    
    def get_duration(self):
        """ Estimate how long the study will take. """
        app = App.get_running_app()
        s = app.settings.circle_task
        duration = ((2 * s.n_practice_trials + s.n_blocks * s.n_trials)  # Number of total trials.
                    * (s.warm_up + s.trial_duration + s.cool_down)  # Duration per trial.
                    + ((bool(s.n_practice_trials) * 2 + s.n_blocks) * 90.0)  # Buffer for reading instructions.
                    )
        duration /= 60.0  # To minutes.
        duration = int(duration)  # Round.
        return duration
    
    def get_n_blocks(self):
        """ Get number of blocks for practice and tests. """
        app = App.get_running_app()
        s = app.settings.circle_task
        n_practice = 2 * bool(s.n_practice_trials)
        n_tests = s.n_blocks
        return n_practice, n_tests
        
    def on_pre_enter(self, *args):
        """ Setup information screen before we see it. """
        self.title = _("Consent")
        read_notice = _("Please read the following information carefully before proceeding.Use scrolling to go "
                        "through the text to the end.")
        
        explanation = _("[b]Explanation of the study:[/b]\n"
                        "We are very pleased that you are interested in participating in our study. "
                        "The neuromotor system of our human bodies has more elements (such as joints, digits, and "
                        "muscles) than are needed for accomplishing most typical tasks. For example, when pointing "
                        "your finger at a position, there's still room for your elbow and shoulder to move. You could "
                        "also reach that same position with either weak or strong muscle force. "
                        "The goal of this study is to investigate how the accuracy of performing a motion task "
                        "changes when the range of motion for solving the task gets limited by an additional "
                        "concurrent task. Such information could be beneficial for athlete training or rehabilitation. "
                        "The respective tasks are described and explained to you in detail "
                        "beforehand. No particular stress or even risks are to be expected when performing the "
                        "tasks.")
                             
        duration_msg = _("The study will take approximately {0} minutes to complete. ").format(self.get_duration())
        n_practice, n_tests = self.get_n_blocks()
        duration_msg += _("First, you will practice the tasks in {0} blocks. ").format(n_practice) * bool(n_practice)
        duration_msg += _("There will be {0} blocks to test your performance. ").format(n_tests)

        voluntariness = _("[b]Voluntary Participation:[/b]\n"
                          "Participation in the study is voluntary. "
                          "You can revoke your consent to participate in this study at any time while performing "
                          "the tasks and without giving reasons, without incurring any disadvantages. To do so just "
                          "press the back button during the study or close the app."
                          "After completing all the tasks you are offered to upload the collected research data to "
                          "the Internet. "
                          "You can therefore withdraw your consent to the online storage and processing of the data "
                          "until the end of task completion. "
                          "If you cancel your participation before completion, or if you decide not to transmit the "
                          "data after completing the tasks, no data will be transmitted. "
                          "You personally will not receive any benefits, financial or otherwise, from participating in "
                          "this study.")
        
        privacy_notice = _("Please review the [ref=privacy][color=0000ff]Privacy Policy (press here)[/color][/ref] "
                           "carefully for information on what kind of data we collect and how we intend to use them.")

        app = App.get_running_app()
        s = app.settings.circle_task
        contact = _("If you have any questions regarding this study, please direct them to the contacts listed below.\n"
                    "[b]Contact regarding this study:[/b]\n"
                    "Philipps-Universität Marburg\n"
                    "Department of Psychology\n"
                    "Work group: General and Biological Psychology\n"
                    "Research group Theoretical Neuroscience\n"
                    "PI: Prof. Dr. Dominik Endres\n"
                    "Researcher: {0}\n\n"
                    "Gutenbergstraße 18\n"
                    "D-35032 Marburg / Lahn\n"
                    "Tel .: +496421 - 2823818\n"
                    "[ref=mailto:dominik.endres@uni-marburg.de][color=0000ff]dominik.endres@uni-marburg.de"
                    "[/color][/ref]\n"
                    "[ref=mailto:{1}][color=0000ff]{1}[/color][/ref]").format(s.researcher, s.email_recipient)
        
        consent = _("I hereby confirm that I have read and understood the participation information described "
                    "above as well as the [ref=privacy][color=0000ff]Privacy Policy[/color][/ref]. "
                    "I agree to the conditions of participation and Privacy Policy.")
        
        messages = [read_notice, explanation, duration_msg, voluntariness, privacy_notice, contact, consent]
        # Clear the old message.
        self.ids.consent_labels.clear_widgets()
        # Add new message.
        for message in messages:
            label = ConsentLabel(text=message)
            label.bind(on_ref_press=lambda instance, value: self.on_ref(value))
            self.ids.consent_labels.add_widget(label)
