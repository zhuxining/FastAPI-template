import granian

if __name__ == "__main__":
    granian.Granian(
        "app.main:app",
        interface="asgi",
        port=8000,
        log_level="info",
        log_access=True,
        reload=True,
    ).serve()
