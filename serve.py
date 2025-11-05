from granian import Granian

if __name__ == "__main__":
	app = Granian(
		"app.main:app",
		port=8000,
		interface="asgi",  # type: ignore
		workers=1,
		loop="uvloop",  # type: ignore
		respawn_failed_workers=True,
		process_name="fastapi_granian_app",
		log_enabled=True,
		log_level="info",  # type: ignore
	)
	app.serve()
