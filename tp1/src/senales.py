import os
import signal
import select

class SignalHandlerSelfPipe:
    """Manejador de señales async-signal-safe mediante Self-Pipe Trick."""
    def __init__(self):
        self.r_fd, self.w_fd = os.pipe()
        os.set_blocking(self.r_fd, False)
        os.set_blocking(self.w_fd, False)
        self.old_handlers = {}

    def _signal_handler(self, sig, frame):
        try:
            if sig == signal.SIGINT:
                os.write(self.w_fd, b'I')
            elif sig == signal.SIGTERM:
                os.write(self.w_fd, b'T')
            elif sig == signal.SIGHUP:
                os.write(self.w_fd, b'H')
            elif sig == signal.SIGUSR1:
                os.write(self.w_fd, b'1')
            elif sig == signal.SIGUSR2:
                os.write(self.w_fd, b'2')
            elif hasattr(signal, 'SIGWINCH') and sig == signal.SIGWINCH:
                os.write(self.w_fd, b'W')
        except OSError:
            pass

    def register_signal(self, signum):
        old = signal.signal(signum, self._signal_handler)
        self.old_handlers[signum] = old

    def read_signal_byte(self):
        r, _, _ = select.select([self.r_fd], [], [], 0)
        if self.r_fd in r:
            try:
                data = os.read(self.r_fd, 1024)
                return data[-1:] if data else None
            except OSError:
                return None
        return None

    def get_signal(self):
        """Lee el byte del pipe y devuelve el objeto signal.SIG* correspondiente."""
        b = self.read_signal_byte()
        if not b:
            return None
        
        mapping = {
            b'I': signal.SIGINT,
            b'T': signal.SIGTERM,
            b'H': signal.SIGHUP,
            b'1': signal.SIGUSR1,
            b'2': signal.SIGUSR2,
        }
        if hasattr(signal, 'SIGWINCH'):
            mapping[b'W'] = signal.SIGWINCH
            
        return mapping.get(b)

    def close(self):
        for sig, old in self.old_handlers.items():
            signal.signal(sig, old)
        try:
            os.close(self.r_fd)
            os.close(self.w_fd)
        except OSError:
            pass