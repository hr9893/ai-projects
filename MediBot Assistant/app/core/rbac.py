from app.core.constant import Role, ROLE_COLLECTION_MAP
from qdrant_client.http import models as qmodels


def allowed_collection_for_role(role: Role) -> list[str]:
    return [role.value for roles in ROLE_COLLECTION_MAP(role)]


def build_access_filter(role: Role) -> qmodels.Filter:
    return qmodels.Filter(
        must=[
            qmodels.FieldCondition(
                key="access_roles",
                match=qmodels.MatchAny(any=[role.value]),
            )
        ]
    )
