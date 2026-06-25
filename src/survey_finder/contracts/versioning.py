from enum import Enum

class ContractVersion(str, Enum):
    V1 = "v1"

CURRENT_CONTRACT_VERSION = ContractVersion.V1
