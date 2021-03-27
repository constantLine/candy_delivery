from werkzeug.wrappers import BaseResponse as Response
from app import app

from app import routes, models


@app.errorhandler(400)
def say_error(err):
    return Response(response="HTTP 400 Bad Request", status=400, mimetype="application/json")