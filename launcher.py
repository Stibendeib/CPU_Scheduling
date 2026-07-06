import socket
import threading

import webview

from app import app


def find_available_port(start_port=5000, end_port=5099):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available local port found between 5000 and 5099.")


def run_server(port):
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    port = find_available_port()
    url = f"http://127.0.0.1:{port}/"
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    webview.create_window(
        "CPU Scheduling Calculator",
        url,
        width=1180,
        height=780,
        min_size=(900, 620),
        text_select=True,
    )
    webview.start(debug=False)
