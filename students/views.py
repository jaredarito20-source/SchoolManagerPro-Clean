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


def is_admin(user):
    return (
        user.is_superuser or
        user.groups.filter(name="Administrators").exists()
    )


def is_teacher(user):
    return user.groups.filter(name="Teachers").exists()


def is_bursar(user):
    return user.groups.filter(name="Bursars").exists()


def is_secretary(user):
    return user.groups.filter(name="Secretaries").exists()













# ==========================
# TIMETABLE
# ==========================





