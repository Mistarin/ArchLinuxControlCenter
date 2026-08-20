"""
Security Service: Safe command builder for Auditd rules, permissions and ACLs.
"""

import shlex

class SecurityService:
    def get_audit_watch_command(self, target: str) -> str:
        safe_target = shlex.quote(target.strip())
        return f"sudo auditctl -w {safe_target} -p rwxa -k cachy_watch && sudo auditctl -l && echo 'Audit watch rule active for {safe_target}'"

    def get_audit_search_command(self, target: str) -> str:
        safe_target = shlex.quote(target.strip())
        return f"sudo ausearch -f {safe_target} -i --line-buffered 2>/dev/null | tail -n 60 || sudo journalctl -g {safe_target} -n 60"

    def get_file_stat_command(self, target: str) -> str:
        safe_target = shlex.quote(target.strip())
        return f"stat {safe_target} && echo '' && ls -ld {safe_target}"

    def get_file_acl_command(self, target: str) -> str:
        safe_target = shlex.quote(target.strip())
        return f"getfacl {safe_target}"
