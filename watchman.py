import subprocess, dotbot


def run_command(command, capture_output=False):
    if isinstance(command, list):
        command = " ".join(command)
    elif not isinstance(command, str):
        command = str(command)
    return subprocess.run(
        [command], shell=True, check=True, text=True, capture_output=capture_output
    )


def get_watchman_exec():
    command = []
    command.append("echo")
    command.append("$(which watchman)")
    result = run_command(command, True)
    if result.returncode != 0:
        raise Exception(
            f"failed find watchman, `{' '.join(command)}` returned [{result.returncode}] {result.stderr}"
        )
    return result.stdout.strip()


def get_watchman_version(exec=None):
    command = []
    command.append(exec or "watchman")
    command.append("--version")
    result = run_command(command, True)
    if result.returncode != 0:
        raise Exception(
            f"failed to get watchman version, `{' '.join(command)}` returned [{result.returncode}] {result.stderr}"
        )
    return result.stdout.strip()


class DotbotPlugin(dotbot.Plugin):
    def __init__(self, ctx):
        super().__init__(ctx)
        try:
            self._watchman_exec = get_watchman_exec()
        except Exception as ex:
            self._log.error(f"failed to find watchman executable: {ex}")
            return False
        try:
            self._watchman_version = get_watchman_version(self._watchman_exec)
        except Exception as ex:
            self._log.error(
                f"failed to get watchman version from `{self._watchman_exec}`: {ex}"
            )
        self._log.debug(
            f"found watchman v{self._watchman_version} at {self._watchman_exec}"
        )

    def can_handle(self, directive):
        valid = directive == "watchman"
        if not valid:
            self._log.debug(f"The plugin doesn't support the `{directive}` directive")
        return valid

    def _create_watch(self, dir):
        command = []
        command.append(self._watchman_exec)
        command.append("watch")
        command.append(dir)
        command.append("&>/dev/null")
        try:
            self._log.info(f"creating watch for {dir}")
            self._log.debug(f"using command {' '.join(command)}")
            run_command(command)
            return True
        except Exception as ex:
            self._log.error(f"failed to create watch for `{dir}`: {ex}")
            return False

    def _create_trigger(self, dir, name, pattern, cmd):
        command = []
        command.append(self._watchman_exec)
        command.append("--")
        command.append("trigger")
        command.append(dir)
        command.append(name)
        command.append(f"'{pattern}'")
        command.append("--")
        if isinstance(cmd, list):
            command = command + cmd
        else:
            command.append(cmd)
        command.append("&>/dev/null")
        try:
            self._log.info(f"creating trigger for {dir}....")
            self._log.debug(f"using command: {' '.join(command)}")
            run_command(command)
            return True
        except Exception as ex:
            self._log.error(
                f"failed to create trigger {name} for {cmd} in {dir}/{pattern}: {ex}"
            )
            return False

    def handle(self, directive, data):
        if not self.can_handle(directive):
            return False
        for name, watch_config in data.items():
            self._create_watch(name)
            for trigger, trigger_config in watch_config.items():
                self._create_trigger(
                    name, trigger, trigger_config["pattern"], trigger_config["command"]
                )
        self._log.info(f"finished configuring watchman")
        return True
