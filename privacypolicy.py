"""
This file contains the source text for the privacy policy.
It's written in markdown so it can easily be written to file.
When displayed in the app it gets converted to BBCode for compatibility with kivy labels.
Having only 1 source for the policy reduces maintenance and ensures consistency.
"""

from src.i18n import _


# Wrap terms in getter so that translation kicks in when necessary.
def get_policy():
    policy_md = _(
    "\n"  # Hack for fitting title into popup.
    "# Privacy Policy\n"
    "The purpose of the {appname} app is to collect anonymous research data that its users, like yourself, "
    "provide to us **voluntarily** by participating in the studies the {appname} app offers. "
    "Participation in these studies is completely voluntary and users have a choice to share the collected "
    "research data with us after each completed study."
    "\n\n"
    "## Types of Collected Data\n"
    "- Research Data\n"
    "- De-identified Device Information\n"
    "- Personal Data\n"
    "\n\n"
    "### Research Data\n"
    "For each study, that a user participates in, the {appname} app collects research data that is relevant "
    "to the study's research question. These data may include, but is not limited to, for example, "
    "the time of day the study was conducted, and psychometric measures such as reaction times and scores."
    "\n\n"
    "For each user account created in the app, a randomly generated character string is created as part of "
    "the research data so that the data can be attributed to an anonymously participating person. "
    "The name chosen for the user account is not part of the research data and will not be transmitted "
    "when uploading the data.  \n"
    "The collected research data will not reveal the identity of the participating user."
    "\n\n"
    "It is the responsibility of the participants to protect their user account and the device "
    "against unauthorized access."
    "\n\n"
    "### De-identified Device Information\n"
    "To associate research data that was recorded on the same device, a character string is transmitted, "
    "which does not allow personal identification of the device or its users. "
    "We also collect device information such as the screen resolution and which type of operating "
    "system the {appname} app is running on. These data are considered part of the research data."
    "\n\n"
    "### Personal Data\n"
    "The {appname} app does **not** collect sensitive or personally identifiable information such as a user's name, "
    "address, telephone number, IP-address, passwords, payment details, or social security number.  \n"
    "However, if a user decides to contact us via e-mail, which is completely optional, we and the "
    "third-parties providing the e-mail services will process the e-mail address and its content "
    "to provide the service. After receiving an e-mail by a user, any research data that was sent with it "
    "will be extracted and therefore separated from any personally identifiable information the user may have "
    "provided to us within the e-mail. This way the research data can not be used to reveal the identity of the "
    "user. The e-mail will be deleted alongside any personal information that was provided to us within "
    "10 days of receiving the e-mail. We will not share any e-mail address or any personal information "
    "of users with other third parties."
    "\n\n"
    "## Local Storage of Research Data\n"
    "Users can opt-in to store the collected information locally on the device by enabling the option in "
    "the settings of the {appname} app. Any locally stored research data from a user account will be removed "
    "when the user account is removed from the {appname} app.  \n"
    "All locally stored research data by the {appname} app is removed when the app is removed from the device."
    "\n\n"
    "## Sharing of Research Data\n"
    "When a user decides to share the collected research data with us, the data will be transferred to "
    "a database on servers within the European Union which are provided by a third party. "
    "You can find out more about the data protection measures of the third-party provider at the following "
    "Internet address:"
    "\n\n"
    "<https://www.heroku.com/policy/security#data-security>"
    "\n\n"
    "After transfer of the research data to the database, complete deletion of the research "
    "data collected can no longer be guaranteed, since we can not attribute the anonymous data to "
    "a specific person. Furthermore, backup copies of the data are created within the infrastructure "
    "of the third-party provider. Moreover, immediate public access to the research data and its "
    "results from automated processing is possible, see **Usage of Anonymized Data**."
    "\n\n"
    "## Usage of Anonymized Data\n"
    "The results and collected research data from any study in the {appname} app will be published "
    "as a scientific publication. This is done in anonymized form, i.e. without the research data on its "
    "own being able to identify a specific person. The fully anonymized data from these studies "
    "are made available on the Internet as open data under the "
    "[CC-BY-SA license](https://creativecommons.org/licenses/by-sa/3.0/). This means "
    "that the research data can also be used for any purposes other than the studies they were originally "
    "collected for, including commercial purposes."
    "\n\n"
    "The collected research data will be processed to perform statistical analysis for scientific inquiries "
    "in a semi-automatic fashion. A link to the web-interface for analyzing the research data is provided "
    "within the {appname} app."
    "\n\n"
    "After completing a study, the data will possibly be stored and published in a national or "
    "international data archive. These studies will thus follow the recommendations of the German "
    "Research Foundation (DFG) and the German Society for Psychology (DGPs) for quality "
    "assurance in research."
    "\n"
    )
    return policy_md


if __name__ == '__main__':
    from pathlib import Path
    from src.i18n import change_language_to, list_languages
    from src.utility import create_markdown_file
    
    languages = list_languages()
    for lang in languages:
        change_language_to(lang)
        this_file = Path(__file__)
        destination = this_file.with_name(f"{this_file.stem}_{lang}").with_suffix('.md')
        create_markdown_file(destination, get_policy())
