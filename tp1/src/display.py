import curses
import time
import json

MIN_INTERVALS = {
    "resumen": 0.5,
    "memoria": 1.0,
    "fds": 2.0,
    "threads": 0.5,
    "senales": 5.0,
    "scheduling": 5.0,
    "sistema": 1.0
}

class TUI:
    def __init__(self, snapshot_dict, intervals_dict, running_flag, sig_handler):
        self.snapshot = snapshot_dict
        self.intervals = intervals_dict
        self.running_flag = running_flag
        self.sig_handler = sig_handler
        
        self.vistas = [
            ("1", "r", "resumen", "Resumen"),
            ("2", "m", "memoria", "Memoria"),
            ("3", "f", "fds", "File Descriptors"),
            ("4", "t", "threads", "Threads"),
            ("5", "s", "senales", "Señales"),
            ("6", "p", "scheduling", "Scheduling"),
            ("7", "g", "sistema", "Sistema Global")
        ]
        self.vista_actual_idx = 0
        self.selected_row = 0
        self.pinned_pid = None
        self.filter_cmd = ""
        self.filter_user = ""
        self.sort_mode = "CPU%"  # Opciones rotativas: "CPU%", "RSS", "PID"
        self.verbose = False
        self.show_help = False
        self.input_mode = None  # None, "cmd", "user"
        self.input_buffer = ""

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(100)

        while self.running_flag.value:
            # Atender eventos/señales recibidas por el Self-Pipe
            sig_byte = self.sig_handler.read_signal_byte()
            if sig_byte in [b'I', b'T']:
                self.running_flag.value = False
                break
            elif sig_byte == b'H':  # SIGHUP: Recargar config
                self.reload_config()
            elif sig_byte == b'1':  # SIGUSR1: Dump JSON
                self.dump_snapshot()
            elif sig_byte == b'2':  # SIGUSR2: Toggle Verbose
                self.verbose = not self.verbose
            elif sig_byte == b'W':  # SIGWINCH: Repintar
                curses.resizeterm(*stdscr.getmaxyx())

            try:
                ch = stdscr.getch()
            except Exception:
                ch = -1

            if ch != -1:
                self.handle_input(ch)

            self.render(stdscr)
            time.sleep(0.05)

    def reload_config(self):
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                if "intervals" in cfg:
                    for k, v in cfg["intervals"].items():
                        if k in self.intervals:
                            self.intervals[k].value = float(v)
        except Exception:
            pass

    def dump_snapshot(self):
        try:
            ts = int(time.time())
            filename = f"dump_{ts}.json"
            data = {k: dict(v) if isinstance(v, dict) else list(v) for k, v in self.snapshot.items()}
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def handle_input(self, ch):
        # Modo Entrada de Texto para Filtros
        if self.input_mode is not None:
            if ch in [10, 13]:  # Enter
                if self.input_mode == "cmd":
                    self.filter_cmd = self.input_buffer
                elif self.input_mode == "user":
                    self.filter_user = self.input_buffer
                self.input_mode = None
                self.input_buffer = ""
            elif ch in [27]:  # ESC
                self.input_mode = None
                self.input_buffer = ""
            elif ch in [8, 127, curses.KEY_BACKSPACE]:
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= ch <= 126:
                self.input_buffer += chr(ch)
            return

        # Ayuda
        if ch in [ord('h'), ord('?')]:
            self.show_help = not self.show_help
            return

        if ch in [ord('q'), ord('Q')]:
            self.running_flag.value = False
            return

        # Vistas 1-7 o r/m/f/t/s/p/g
        for idx, (num, char, code, label) in enumerate(self.vistas):
            if ch == ord(num) or ch == ord(char):
                self.vista_actual_idx = idx
                break

        # Navegación
        if ch == curses.KEY_UP:
            if self.selected_row > 0:
                self.selected_row -= 1
        elif ch == curses.KEY_DOWN:
            self.selected_row += 1

        # Pin PID
        elif ch in [10, 13]:  # Enter
            resumen_data = self.get_filtered_resumen()
            if resumen_data and 0 <= self.selected_row < len(resumen_data):
                sel_pid = resumen_data[self.selected_row]['pid']
                self.pinned_pid = None if self.pinned_pid == sel_pid else sel_pid

        # Filtros
        elif ch == ord('/'):
            self.input_mode = "cmd"
            self.input_buffer = ""
        elif ch == ord('u'):
            self.input_mode = "user"
            self.input_buffer = ""

        # Toggle Ordenamiento Secuencial (CPU% -> RSS -> PID -> CPU%)
        elif ch in [ord('c'), ord('C')]:
            if self.sort_mode == "CPU%":
                self.sort_mode = "RSS"
            elif self.sort_mode == "RSS":
                self.sort_mode = "PID"
            else:
                self.sort_mode = "CPU%"

        # Intervalos (+ / -)
        elif ch in [ord('+'), ord('=')]:
            key = self.vistas[self.vista_actual_idx][2]
            if key in self.intervals:
                self.intervals[key].value = round(self.intervals[key].value + 0.5, 1)
        elif ch in [ord('-'), ord('_')]:
            key = self.vistas[self.vista_actual_idx][2]
            min_val = MIN_INTERVALS.get(key, 0.5)
            if key in self.intervals and self.intervals[key].value > min_val:
                self.intervals[key].value = round(max(min_val, self.intervals[key].value - 0.5), 1)

    def get_filtered_resumen(self):
        data = self.snapshot.get("resumen", [])
        if not data:
            return []
        
        # Filtros
        filtrados = []
        for p in data:
            if self.filter_cmd and self.filter_cmd.lower() not in p['comm'].lower():
                continue
            if self.filter_user and self.filter_user not in str(p['uid']):
                continue
            filtrados.append(p)

        # Ordenamiento
        if self.sort_mode == "CPU%":
            def parse_cpu(proc_item):
                try:
                    return float(proc_item.get('cpu', proc_item.get('cpu_usage', 0.0)))
                except Exception:
                    return 0.0
            filtrados.sort(key=parse_cpu, reverse=True)
        elif self.sort_mode == "RSS":
            def parse_rss(val):
                try:
                    return int(val.split()[0])
                except Exception:
                    return 0
            filtrados.sort(key=lambda x: parse_rss(x.get('vm_rss', '0 kB')), reverse=True)
        else:  # "PID"
            filtrados.sort(key=lambda x: x['pid'])

        return filtrados

    def render(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        if self.show_help:
            self.render_help(stdscr, max_y, max_x)
            stdscr.refresh()
            return

        num, char, key_code, label = self.vistas[self.vista_actual_idx]
        int_val = self.intervals[key_code].value if key_code in self.intervals else 0.0

        # Bar Superior
        header = f" MONITOR | Vista: [{num}/{char}:{label}] | Orden: [{self.sort_mode}] | Refresco: {int_val}s (+/-) | Pin PID: {self.pinned_pid or 'Ninguno'} | [h/?] Ayuda | [q] Salir"
        try:
            stdscr.addstr(0, 0, header[:max_x-1], curses.A_REVERSE)
        except curses.error:
            pass

        # Mostrar Prompt si está escribiendo un filtro
        if self.input_mode:
            prompt = f" Filtrar por {self.input_mode.upper()}: {self.input_buffer}_"
            try:
                stdscr.addstr(1, 0, prompt[:max_x-1], curses.A_BOLD)
            except curses.error:
                pass

        # DIVISIÓN DE PANTALLA (Superior: Resumen, Inferior: Detalle de Vista Activa)
        top_height = max(5, max_y // 2 - 1)
        bottom_start = top_height + 2

        # ---------------- PARTE SUPERIOR: LISTA DE PROCESOS ----------------
        try:
            sub_hdr = f"{'PID':<7} {'PPID':<7} {'USER':<8} {'STAT':<5} {'THREADS':<8} {'RSS':<10} {'CPU%':<7} {'COMM':<20}"
            stdscr.addstr(2, 2, sub_hdr[:max_x-1], curses.A_UNDERLINE)
        except curses.error:
            pass

        resumen_procs = self.get_filtered_resumen()
        visible_top = max(1, top_height - 3)

        for idx, proc in enumerate(resumen_procs[self.selected_row : self.selected_row + visible_top]):
            line_idx = self.selected_row + idx
            is_selected = (line_idx == self.selected_row)
            is_pinned = (proc['pid'] == self.pinned_pid)
            
            # Formatear el porcentaje de CPU
            cpu_val = proc.get('cpu', proc.get('cpu_usage', 0.0))
            cpu_str = f"{cpu_val:.1f}%"

            prefix = "📌" if is_pinned else (">" if is_selected else " ")
            linea = f"{prefix} {proc['pid']:<5} {proc['ppid']:<7} {proc['uid']:<8} {proc['state']:<5} {proc['threads']:<8} {proc['vm_rss']:<10} {cpu_str:<7} {proc['comm']:<20}"
            
            attr = curses.A_BOLD if is_selected else curses.A_NORMAL
            try:
                stdscr.addstr(3 + idx, 0, linea[:max_x-1], attr)
            except curses.error:
                pass

        # Separador Horizontal de Layout
        try:
            stdscr.addstr(top_height + 1, 0, "─" * (max_x - 1))
        except curses.error:
            pass

        # ---------------- PARTE INFERIOR: PANEL DE DETALLE ----------------
        try:
            det_hdr = f" DETALLE DE VISTA: {label.upper()} (Intervalo: {int_val}s)"
            stdscr.addstr(bottom_start, 2, det_hdr[:max_x-1], curses.A_REVERSE)
        except curses.error:
            pass

        data_detalle = self.snapshot.get(key_code, None)

        if data_detalle is None:
            try:
                stdscr.addstr(bottom_start + 2, 2, "Cargando métricas de /proc...")
            except curses.error:
                pass
        elif key_code == "sistema":
            try:
                stdscr.addstr(bottom_start + 2, 2, f"Uptime: {data_detalle.get('uptime', 0):.2f}s")
                stdscr.addstr(bottom_start + 3, 2, f"Load Avg: {data_detalle.get('loadavg', 'N/A')}")
                stdscr.addstr(bottom_start + 4, 2, f"Total PIDs: {data_detalle.get('totales_pids', 0)}")
                stdscr.addstr(bottom_start + 5, 2, f"Estados: {data_detalle.get('conteo_estados', {})}")
            except curses.error:
                pass
        else:
            # Seleccionar PID del Pin o del cursor
            target_pid = self.pinned_pid
            if not target_pid and resumen_procs and 0 <= self.selected_row < len(resumen_procs):
                target_pid = resumen_procs[self.selected_row]['pid']

            if isinstance(data_detalle, dict) and target_pid in data_detalle:
                info = data_detalle[target_pid]
                try:
                    stdscr.addstr(bottom_start + 2, 2, f"PID Objetivado: {target_pid}")
                    if isinstance(info, dict):
                        for i, (k, v) in enumerate(info.items()):
                            if bottom_start + 3 + i < max_y - 1:
                                stdscr.addstr(bottom_start + 3 + i, 4, f"{k}: {str(v)[:max_x-20]}")
                    else:
                        stdscr.addstr(bottom_start + 3, 4, str(info)[:max_x-10])
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(bottom_start + 2, 2, f"No hay detalle disponible para el PID {target_pid or 'N/A'}")
                except curses.error:
                    pass

        stdscr.refresh()

    def render_help(self, stdscr, max_y, max_x):
        lines = [
            "=== AYUDA - MONITOR DE SISTEMA EN TIEMPO REAL ===",
            "",
            "Vistas (Teclas 1-7 o Letras):",
            "  1 / r : Resumen",
            "  2 / m : Memoria",
            "  3 / f : File Descriptors",
            "  4 / t : Threads",
            "  5 / s : Señales",
            "  6 / p : Scheduling",
            "  7 / g : Sistema Global",
            "",
            "Navegación y Controles:",
            "  ↑ / ↓ : Seleccionar proceso en la lista superior",
            "  Enter : Fijar / Liberar (Pin) el PID seleccionado para el panel inferior",
            "  /     : Filtrar por Nombre de Comando",
            "  u     : Filtrar por Usuario (UID)",
            "  c     : Alternar Ordenamiento (CPU% -> RSS -> PID)",
            "  + / - : Incrementar / Disminuir intervalo de refresco de la vista activa",
            "  h / ? : Mostrar / Ocultar esta pantalla de Ayuda",
            "  q     : Salir limpiamente",
            "",
            "Presiona 'h' o '?' para volver a la interfaz principal."
        ]
        for idx, line in enumerate(lines):
            if idx < max_y - 1:
                try:
                    stdscr.addstr(idx + 1, 2, line[:max_x-4])
                except curses.error:
                    pass
