"""
core package - System level operations (Admin, Firewall, Network)
"""
from src.core.admin import is_admin, request_admin
from src.core.firewall import (
    create_block_rule,
    remove_block_rules,
    is_rule_active,
    clean_all_nexuslock_rules,
    clean_all_netherwatch_rules,
    run_netsh,
)
from src.core.network import measure_ping, flush_dns, refresh_deadlock_sdr

__all__ = [
    "is_admin",
    "request_admin",
    "create_block_rule",
    "remove_block_rules",
    "is_rule_active",
    "clean_all_nexuslock_rules",
    "clean_all_netherwatch_rules",
    "run_netsh",
    "measure_ping",
    "flush_dns",
    "refresh_deadlock_sdr",
]
