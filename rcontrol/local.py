import subprocess

from rcontrol.streamreader import StreamsReader
from rcontrol.core import CommandTask, BaseSession


class ProcessReader(StreamsReader):
    """
    Specialized reader for subprocess.Popen instances.
    """
    def _create_readers(self, queue, proc):
        stdout_reader = None
        if proc.stdout:
            stdout_reader = self._create_stream_reader(proc.stdout,
                                                       queue,
                                                       self.stdout_callback)
        stderr_reader = None
        if proc.stderr and proc.stderr != proc.stdout:
            stderr_reader = self._create_stream_reader(proc.stderr,
                                                       queue,
                                                       self.stderr_callback)
        return stdout_reader, stderr_reader


class LocalExec(CommandTask):
    """
    Execute a local command.

    The execution starts as soon as the object is created.

    Basically extend a :class:`CommandTask` to pass in a specialized
    stream reader, :class:`ProcessReader`.

    :param session: instance of the :class:`LocalSession` responsible of
        this command execution
    :param command: the command to execute (a string)
    :param kwargs: list of argument passed to the base class constructor
    """
    def __init__(self, session, command, **kwargs):
        CommandTask.__init__(self, session, ProcessReader, command, **kwargs)
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT if self._combine_stderr else subprocess.PIPE
        self._proc = subprocess.Popen(command, shell=True, stdout=stdout,
                                      stderr=stderr)
        self._reader.start(self._proc)

    def _on_finished(self):
        if not self.timed_out():
            self._set_exit_code(self._proc.wait())
        CommandTask._on_finished(self)


class LocalSession(BaseSession):
    """
    A session on the local machine.
    """
    def open(self, filename, mode='r', bufsize=-1):
        return open(filename, mode=mode)

    def execute(self, command, **kwargs):
        return LocalExec(self, command, **kwargs)
