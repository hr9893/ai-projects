from enum import Enum


class Role(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    BILLING_EXECUTIVE = "billing_executive"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class Collection(str, Enum):
    GENERAL = "general"
    CLINICAL = "clinical"
    NURSING = "nursing"
    BILLING = "billing"
    EQUIPMENT = "equipment"


ROLE_COLLECTION_MAP: dict[Role, list[Collection]] = {
    Role.DOCTOR: [Collection.CLINICAL, Collection.GENERAL, Collection.NURSING],
    Role.NURSE: [Collection.CLINICAL, Collection.GENERAL],
    Role.BILLING_EXECUTIVE: [Collection.BILLING, Collection.GENERAL],
    Role.TECHNICIAN: [Collection.EQUIPMENT, Collection.GENERAL],
    Role.ADMIN: [list(Collection)],
}

SQL_RAG_ALLOWED_ROLES = {Role.BILLING_EXECUTIVE, Role.ADMIN}

DEMO_USERS: dict[str, tuple[str, Role]] = {
    "dr.mehta": ("doctor", Role.DOCTOR),
    "nurse.priya": ("nurse", Role.NURSE),
    "billing.ravi": ("billing_executive", Role.BILLING_EXECUTIVE),
    "tech.anand": ("technician", Role.TECHNICIAN),
    "admin.sys": ("admin", Role.ADMIN),
}
