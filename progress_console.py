# Minimal placeholder for GUI console routing (expand later with threading/callbacks)
def pipe_line_to_console(line: str, console_print):
    if line is not None:
        console_print(line)
