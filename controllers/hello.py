class HelloController:
    def get_hello_world_data(self):
        return {
            "message": "Permintaan berhasil diproses",
            "data": {
                "greeting": "Hello World from FastAPI"
            },
            "errors": None
        }
