from __future__ import annotations

import truststore


_SYSTEM_TRUST_STORE_CONFIGURED = False


def configure_system_trust_store() -> None:
    """Make HTTPS clients honor the operating system's trusted CA store."""
    global _SYSTEM_TRUST_STORE_CONFIGURED
    if _SYSTEM_TRUST_STORE_CONFIGURED:
        return

    truststore.inject_into_ssl()
    _SYSTEM_TRUST_STORE_CONFIGURED = True
