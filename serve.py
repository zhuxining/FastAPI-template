from granian import Granian

if __name__ == "__main__":
	app = Granian(
		"app.main:app",
		port=8000,
		interface="asgi",  # type: ignore
		loop="uvloop",  # type: ignore
		process_name="granian_app",
		log_level="info",  # type: ignore
	)
	app.serve()
