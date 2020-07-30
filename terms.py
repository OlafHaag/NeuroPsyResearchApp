"""
This file contains the source text for the terms & conditions of using the app.
It's written in markdown so it can easily be written to file.
When displayed in the app it gets converted to BBCode for compatibility with kivy labels.
Having only 1 source for the policy reduces maintenance and ensures consistency.
"""

from src.i18n import _


# Wrap terms in getter so that translation kicks in when necessary.
def get_terms():
    terms_md = _(
    "# Terms of Use\n"
    "## Definitions\n"
    "\"You\", \"Your\" and \"User\" refer to you, the person using the Service of {author}, "
    "including the software of the Service downloaded on Your personal device.  \n"
    "\"We\", \"Us\" and \"Our\" refer to the official web-site of the Service and the software of the Service, "
    "as well as the authors.  \n"
    "\"Service\" means the software {appname}."
    "\n\n"
    "## Acceptance of Terms of Use\n"
    "By downloading or using the app, these Terms as well as our privacy policy and all applicable laws will "
    "automatically apply to you - you should make sure therefore that you read them carefully before using the app.  \n"
    "You must be 13 years of age or older and the minimum age of digital consent in your country to use this "
    "Service. If you are the age of majority in your jurisdiction or over, you consent that you have read, understood, "
    "and accept to be bound by the Terms, and if you are between 13 (or the minimum age of digital consent, as "
    "applicable) and the age of majority in your jurisdiction, you confirm that your legal guardian has reviewed and "
    "agrees to these Terms. If you do not agree to these terms and all applicable additional terms, "
    "then you have no right to access or use any of the Service."
    "\n\n"
    "## Disclaimers and Warranties\n"
    "You are granted a nonexclusive, worldwide, and perpetual license to perform, display, "
    "and use the Product on the Device.  \n"
    "{author} built the {appname} app as an Open Source app. This Service is provided by {author} "
    "at no cost and is intended for use as is.  \n"
    "The {appname} app stores and processes de-identified data that you have provided to us, "
    "in order to provide the Service. As it is with internet based services, a 100% anonymity "
    "cannot be guaranteed. It's your responsibility to keep your phone and access to the app "
    "secure. We therefore recommend that you do not jailbreak or root your phone, which is the "
    "process of removing software restrictions and limitations imposed by the official "
    "operating system of your device. It could make your phone vulnerable to "
    "malware/viruses/malicious programs, compromise your phone's security features and it "
    "could mean that the {appname} app won't work properly or at all."
    "\n\n"
    "You should be aware that there are certain things that {author} will not take "
    "responsibility for. Certain functions of the app will require the app to have an "
    "active internet connection. The connection can be Wi-Fi, or provided by your mobile "
    "network provider, but {author} cannot take responsibility for the app not working at "
    "full functionality if you don't have access to Wi-Fi, and you don't have any of your data "
    "allowance left."
    "\n\n"
    "If you're using the app outside of an area with Wi-Fi, you should remember that your "
    "terms of the agreement with your mobile network provider will still apply. As a result, "
    "you may be charged by your mobile provider for the cost of data for the duration of the "
    "connection while accessing the app, or other third party charges. In using the app, you're "
    "accepting responsibility for any such charges, including roaming data charges if you use "
    "the app outside of your home territory (i.e. region or country) without turning off data "
    "roaming. If you are not the bill payer for the device on which you're using the app, "
    "please be aware that we assume that you have received permission from the bill payer "
    "for using the app."
    "\n\n"
    "Along the same lines, {author} cannot always take responsibility for the way you use the "
    "app i.e. You need to make sure that your device stays charged - if it runs out of battery "
    "and you can't turn it on to avail the Service, {author} cannot accept responsibility."
    "\n\n"
    "With respect to {author}'s responsibility for your use of the app, when you're using the "
    "app, it's important to bear in mind that although we endeavour to ensure that it is "
    "updated and correct at all times, we do rely on third parties to provide information to us "
    "so that we can make it available to you. {author} accepts no liability for any loss, "
    "direct or indirect, you experience as a result of relying wholly on this functionality of "
    "the app."
    "\n\n"
    "## Links to Other Sites\n"
    "This Service may contain links to other sites. If you click on a third-party link, you will "
    "be directed to that site. Note that these external sites may not be operated by {author}. Therefore, "
    "{author} strongly advises you to review the Privacy Policy of these websites. {author} has no control over "
    "and assume no responsibility for the content, privacy policies, or practices of any third-party "
    "sites or services."
    "\n\n"
    "## Intellectual Property Rights\n"
    "The source code to this Service is provided separately under the open MIT license at: \n"
    "[{source}]({source}).\n"
    "The app itself, and all the trade marks, copyright, database rights and other intellectual "
    "property rights related to it, still belong to {author}."
    "\n\n"
    "## Updates And Availability\n"
    "{author} is committed to ensuring that the app is as useful and efficient as possible. "
    "For that reason, we reserve the right to make changes to the app. "
    "The app is currently available on Android - the requirements for system (and for any additional systems we "
    "decide to extend the availability of the app to) may change, and you'll need to download the updates if you "
    "want to keep using the app. If you do not accept updates to the application, your right to use and access the "
    "Services will immediately cease. {author} does not promise that the app will always be updated "
    "so that it is relevant to you and/or works with the Android version that you have installed on your device."
    "\n\n"
    "## Termination\n"
    "{author} may wish to stop providing the app and may terminate or suspend any and all Services immediately,"
    " without prior notice or liability, for any reason whatsoever. "
    "Unless we tell you otherwise, upon any termination, (a) the rights and licenses granted to you in these Terms "
    "will end; (b) you must stop using the app, and (if needed) delete it from your device."
    "You may terminate this Agreement yourself by ceasing to use the Services and removing the application from your "
    "devices. "
    "All provisions of the Terms which by their nature should survive termination shall survive termination, "
    "including, without limitation, ownership and rights provisions and warranties, warranty disclaimers, indemnity "
    "and limitations of liability."
    "\n\n"
    "## Changes to This Terms of Use\n"
    "We may revise the Terms of Use from time to time. These changes will not be retroactive. The user should look at "
    "the Agreement regularly. {author} will also update the “Last updated” date at the bottom of this Agreement. "
    "By continuing to use the Service or retaining access to the Service after the revisions are in effect, "
    "the user agrees to be bound by the revised Agreement. If the modified Agreement is not acceptable to the user, "
    "user’s only recourse is to cease using the Service."
    "\n\n"
    "## Contact Us\n"
    "If you have any questions or suggestions about these Terms of Use, do not hesitate to contact us at "
    "[{contact}](mailto:{contact})."
    "\n\n"
    "**Last Updated:** July 29th 2020"
    )
    return terms_md


if __name__ == '__main__':
    from pathlib import Path
    from src.i18n import change_language_to, list_languages
    from src.utility import create_markdown_file

    languages = list_languages()
    for lang in languages:
        change_language_to(lang)
        this_file = Path(__file__)
        destination = this_file.with_name(f"{this_file.stem}_{lang}").with_suffix('.md')
        create_markdown_file(destination, get_terms())
