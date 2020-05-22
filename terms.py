"""
This file contains the source text for the terms & conditions of using the app.
It's written in markdown so it can easily be written to file.
When displayed in the app it gets converted to BBCode for compatibility with kivy labels.
Having only 1 source for the policy reduces maintenance and ensures consistency.
"""

from src.i18n import _
from src.utility import create_markdown_file


# Wrap terms in getter so that translation kicks in when necessary.
def get_terms():
    terms_md = _(
    "# Terms & Conditions\n"
    "By downloading or using the app, these terms will automatically apply to you - "
    "you should make sure therefore that you read them carefully before using the app.  \n"
    "By using or accessing the {appname} you agree (i) that you are 13 years of age and the minimum age "
    "of digital consent in your country, (ii) if you are the age of majority in your jurisdiction or "
    "over, that you have read, understood, and accept to be bound by the Terms, and (iii) if you are "
    "between 13 (or the minimum age of digital consent, as applicable) and the age of majority in your "
    "jurisdiction, that your legal guardian has reviewed and agrees to these Terms."
    "\n\n"
    "You are granted a nonexclusive, worldwide, and perpetual license to perform, display, "
    "and use the Product on the Device.  \n"
    "{author} built the {appname} app as an Open Source app. This SERVICE is provided by {author} "
    "at no cost and is intended for use as is.\n"
    "You're not allowed to attempt to extract the source code of the app from its binary distribution "
    "and installation. The source code is provided separately under the open MIT license. "
    "The app itself, and all the trade marks, copyright, database rights and other intellectual "
    "property rights related to it, still belong to {author}."
    "\n\n"
    "{author} is committed to ensuring that the app is as useful and efficient as possible. "
    "For that reason, we reserve the right to make changes to the app."
    "\n\n"
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
    "At some point, we may wish to update the app. The app is currently available on Android - "
    "the requirements for system (and for any additional systems we decide to extend the "
    "availability of the app to) may change, and you'll need to download the updates if you "
    "want to keep using the app. {author} does not promise that the app will always be updated "
    "so that it is relevant to you and/or works with the Android version that you have "
    "installed on your device. However, you promise to always accept updates to the application "
    "when offered to you, We may also wish to stop providing the app, and may terminate use of "
    "it at any time without giving notice of termination to you. Unless we tell you otherwise, "
    "upon any termination, (a) the rights and licenses granted to you in these terms will end; "
    "(b) you must stop using the app, and (if needed) delete it from your device."
    "\n\n"
    "## Links to Other Sites\n"
    "This Service may contain links to other sites. If you click on a third-party link, you will "
    "be directed to that site. Note that these external sites may not be operated by me. Therefore, "
    "I strongly advise you to review the Privacy Policy of these websites. I have no control over "
    "and assume no responsibility for the content, privacy policies, or practices of any third-party "
    "sites or services."
    "\n\n"
    "## Changes to This Terms and Conditions\n"
    "We may update the Terms and Conditions from time to time. "
    "\n\n"
    "## Contact Us\n"
    "If you have any questions or suggestions about these Terms and Conditions, do not hesitate "
    "to contact us at [{contact}](mailto:{contact})."
    "\n\n"
    "This Terms and Conditions page was partly generated by "
    "[App Privacy Policy Generator](https://app-privacy-policy-generator.firebaseapp.com/)."
    )
    return terms_md


if __name__ == '__main__':
    from pathlib import Path
    
    destination = Path(__file__).with_suffix('.md')
    create_markdown_file(destination, get_terms())
