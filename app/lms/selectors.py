"""
Centralized CSS selectors for the Moodle LMS DOM.
Update this file if the LMS theme changes.
"""

# Login page
LOGIN_FORM = "form#login"
USERNAME_INPUT = "input#username"
PASSWORD_INPUT = "input#password"
LOGIN_TOKEN = "input[name='logintoken']"
LOGIN_BUTTON = "button#loginbtn"
USER_MENU = "a.dropdown-toggle[data-toggle='dropdown']"  # logged-in indicator

# Dashboard / My home
DASHBOARD_TIMELINE = "div[data-region='timeline-view']"
ASSIGNMENT_CARD = (
    "div.card-body"
)
ASSIGNMENT_LINK = "a[href*='/mod/assign/view.php']"
COURSE_LINK = "a[href*='/course/view.php']"

# Course page
COURSE_SECTION = "li.section"
ACTIVITY_INSTANCE = "div.activityinstance"
ACTIVITY_LINK = "a.activity-link"

# Assignment page
ASSIGNMENT_TITLE = "h1"  # or h2 within #region-main
ASSIGNMENT_DESC = "div[data-region='assignment-info']"
ASSIGNMENT_INTRO = "div.no-overflow"
ASSIGNMENT_DATES = "div[data-region='activity-dates']"
SUBMISSION_STATUS = "div[data-region='submission-status']"
SUBMIT_BUTTON = "button#id-submitbutton"
EDIT_SUBMISSION_LINK = "a[href*='&action=editsubmission']"
ADD_SUBMISSION_BTN = "a[href*='&action=editsubmission']"

# Submission page
FILE_PICKER = "div[data-fieldtype='filepicker']"
FILE_SUBMIT_BUTTON = "button#id-submitbutton"
SUBMISSION_AREA = "div[data-region='submission-area']"

# Navigation
LOGGED_IN_USERNAME = "span.usertext"  # shows username when logged in
LOGOUT_LINK = "a[href*='logout.php']"
TOAST_WRAPPER = "div.toast-wrapper"

# Attachment section
ATTACHMENT_LINKS = "a[href*='pluginfile.php']"
