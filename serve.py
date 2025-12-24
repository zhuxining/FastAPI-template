from granian import Granian

if __name__ == "__main__":
    app = Granian(
        "app.main:app",
        port=8000,
        interface="asgi",
        workers=1,
        loop="uvloop",
        respawn_failed_workers=True,
        process_name="fastapi_granian_app",
        log_enabled=True,
        log_level="info",
    )
    app.serve()
