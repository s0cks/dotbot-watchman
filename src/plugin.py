import subprocess, dotbot


class DotbotPlugin(dotbot.Plugin):
    def can_handle(self, directive):
        valid = directive == "plugin"
        if not valid:
            self._log.debug(f"The plugin doesn't support the `{directive}` directive")
        return valid

    def handle(self, directive, data):
        if not self.can_handle(directive):
            return False
        pass  # TODO(@s0cks): implement
