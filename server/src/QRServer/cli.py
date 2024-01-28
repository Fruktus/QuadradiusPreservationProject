import traceback
from cmd import Cmd

from QRServer import config

prompt = '> '


# noinspection PyMethodMayBeStatic
class QRCmd(Cmd):
    def __init__(self, server_thread) -> None:
        super().__init__()
        self.prompt = prompt
        self.server_thread = server_thread

    def cmdloop_with_interrupt(self):
        while True:
            try:
                self.cmdloop()
                return
            except KeyboardInterrupt:
                print('^C')

    def emptyline(self):
        pass

    def do_config(self, args: str):
        self.server_thread.run_within_event_loop(self._do_config(args))

    async def _do_config(self, args: str):
        try:
            args = args.split(None, 2)
            if len(args) == 1 and args[0] == 'list':
                config.print_help()
            elif len(args) == 2 and args[0] == 'get':
                key = config.get_key(args[1])
                print(config.get(key.name), end='')

                if key.dirty:
                    print(' (requires restart to apply)')
                else:
                    print()
            elif len(args) == 3 and args[0] == 'set':
                config.set(args[1], args[2])
                print(config.get(args[1]))
            else:
                self._invalid_syntax('config')
        except Exception as e:
            if config.log_verbose.get():
                traceback.print_exc()
            else:
                print(e)

    def complete_config(self, text: str, line: str, begidx, endidx):
        return self.server_thread.run_within_event_loop(self._complete_config(text, line, begidx, endidx))

    async def _complete_config(self, text: str, line: str, begidx, endidx):
        args_before = line[:begidx].strip().split()[1:]

        if len(args_before) == 0:
            return self._filter_prefix(text, ['get', 'set', 'list'])

        if len(args_before) == 1:
            config_keys = map(lambda key: key.name, config.all_keys())
            if args_before[0] in ['get', 'set']:
                return self._filter_prefix(text, config_keys)

        return []

    def help_config(self):
        print('Set or get config values')
        print('  config list')
        print('  config get <name>')
        print('  config set <name> <value>')

    # noinspection PyPep8Naming
    def do_EOF(self, args):
        """Quit the application"""
        raise EOFError

    def do_quit(self, args):
        """Quit the application"""
        raise EOFError

    def _filter_prefix(self, prefix, args):
        return [x for x in args if x.startswith(prefix)]

    def _invalid_syntax(self, command):
        print(f"Error: invalid syntax, type 'help {command}'")
