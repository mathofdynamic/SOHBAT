"""Windows UI Automation focus inspection, without reading field contents."""
import logging

import comtypes.client

comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as uia

logger = logging.getLogger(__name__)
_automation = None


def editable_focus() -> bool | None:
    global _automation
    try:
        if _automation is None:
            _automation = comtypes.client.CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation)
        element = _automation.GetFocusedElement()
        if not element or not element.CurrentIsEnabled:
            return False
        if element.CurrentIsPassword:
            return False
        if element.GetCurrentPropertyValue(30043):  # IsValuePatternAvailable
            return not bool(element.GetCurrentPropertyValue(30046))  # ValueIsReadOnly
        if element.CurrentControlType == 50004:  # Edit
            return bool(element.CurrentIsKeyboardFocusable)
        if element.CurrentControlType in (50000, 50002, 50003, 50005, 50007, 50013):
            return False
        return None
    except Exception:
        logger.exception("Accessibility focus inspection unavailable")
        return None
