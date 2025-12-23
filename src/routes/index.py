from flask import Blueprint, render_template, request, jsonify
import os
from loguru import logger

bp_index = Blueprint('index', __name__)

@bp_index.route('/')
def home():
    logger.debug("Accessed home page route")
    logger.debug(f"DOT_ENV_TEST_ARG: {os.environ.get('DOT_ENV_TEST_ARG')}")
    return render_template('index.html')


@bp_index.route("/test", methods=["GET","POST"])
def test():
    logger.debug("Accessed test page route")
    data = request.get_json() or {}
    logger.debug(f"Test endpoint received data: {data}")

    return jsonify(data)