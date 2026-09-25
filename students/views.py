from .view_modules.academic import *
from .view_modules.examination import *
from .view_modules.finance import *
from .view_modules.discipline import *
from .view_modules.medical import *
from .view_modules.hostel import *
from .view_modules.transport import *
from .view_modules.library import *
from .view_modules.inventory import *
from .view_modules.payroll import *
from .view_modules.administration import *
from .view_modules.authentication import *
from .view_modules.parent import *

from .view_modules.academic import add_student

from .view_modules.timetable import *

from .view_modules.school import (
    add_school_profile,
    school_credentials,
    school_list,
    reset_school_password,

)

from .view_modules.administration import (
    user_list,
    add_user,
    edit_user,
    delete_user,
    reset_user_password,
)
from .view_modules.sms import *
from .view_modules.mpesa import mpesa_callback
from students.view_modules.cbc_assessment import (
    cbc_my_classes,
    cbc_learning_areas,
    cbc_assessment_book,
    cbc_assessment_book_print,
    cbc_subject_score_sheet,
    cbc_student_result,
)

from .view_modules.cbc_assessment import (
    cbc_upper_secondary_strand_classes,
    cbc_upper_secondary_strands,
    cbc_upper_secondary_strand_assessment,
)







# ==========================
# TIMETABLE
# ==========================





