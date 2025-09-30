from flask import Blueprint, render_template, request, jsonify
import os

bp_index = Blueprint('index', __name__)

@bp_index.route('/')
def home():
    print(f"-- in home page route --")
    print(f"DOT_ENV_TEST_ARG: {os.environ.get('DOT_ENV_TEST_ARG')}")
    return render_template('index.html')


@bp_index.route("/test", methods=["GET","POST"])
def test():
    print(f"-- in test page route --")
    data = request.get_json() or {}
    print(f"data: {data}")

    return jsonify(data)