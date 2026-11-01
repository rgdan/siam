import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def worker(mode, port=None):
    import django

    django.setup()
    from django.core.management import call_command

    if mode == "seed":
        call_command("migrate", verbosity=0)
        from api.models import User
        from collection_integrity.services import register_piece

        user = User.objects.create_user(
            email="crash@test.cr", full_name="Crash test", role="museologo"
        )
        register_piece(
            user=user,
            title="committed",
            photos=[{"name": "intact", "content": b"intact"}],
        )
    else:
        from wsgiref.simple_server import make_server

        from django.core.wsgi import get_wsgi_application

        with make_server("127.0.0.1", int(port), get_wsgi_application()) as server:
            server.serve_forever()


def main():
    with tempfile.TemporaryDirectory(prefix="siam-crash-") as temp:
        env = os.environ.copy()
        env.update(
            DJANGO_SETTINGS_MODULE="tests.crash_settings",
            DJANGO_SECRET_KEY="isolated-test-only",
            SIAM_CRASH_DB=str(Path(temp) / "crash.sqlite3"),
            SIAM_CRASH_MARKER=str(Path(temp) / "marker"),
        )
        command = [sys.executable, str(Path(__file__).resolve())]
        subprocess.run(command + ["seed"], env=env, cwd=BACKEND, check=True, timeout=60)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        server = None

        def start():
            child = subprocess.Popen(
                command + ["serve", str(port)],
                env=env,
                cwd=BACKEND,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if child.poll() is not None:
                        raise RuntimeError("Child server exited")
                    try:
                        with urlopen(base + "/status/", timeout=1) as response:
                            return child, json.load(response)
                    except OSError:
                        time.sleep(0.05)
                raise RuntimeError("Server startup timed out")
            except BaseException:
                child.kill()
                child.wait(timeout=10)
                raise

        try:
            server, before = start()

            def interrupted_request():
                try:
                    urlopen(
                        Request(
                            base + "/write/",
                            data=b"{}",
                            headers={"Content-Type": "application/json"},
                        ),
                        timeout=30,
                    ).close()
                except OSError:
                    pass

            request_thread = threading.Thread(target=interrupted_request, daemon=True)
            request_thread.start()
            deadline = time.monotonic() + 15
            while not Path(env["SIAM_CRASH_MARKER"]).exists():
                if time.monotonic() > deadline:
                    raise RuntimeError("Write did not reach uncommitted checkpoint")
                time.sleep(0.05)
            server.kill()
            server.wait(timeout=10)
            request_thread.join(timeout=5)
            server, after = start()
            assert before == after, (before, after)
            assert after == {
                "titles": ["committed"],
                "counts": [1, 1, 1],
                "photos": ["intact"],
            }, after
            print(
                json.dumps(
                    {
                        "test": "SIAM-36 server kill/restart",
                        "result": "PASS",
                        "before": before,
                        "after_restart": after,
                        "interrupted_rows": 0,
                    },
                    indent=2,
                )
            )
        finally:
            if server is not None and server.poll() is None:
                server.kill()
                server.wait(timeout=10)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        worker(*sys.argv[1:])
    else:
        main()
