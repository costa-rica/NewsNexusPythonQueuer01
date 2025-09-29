from flask import Blueprint, render_template, request, jsonify

bp_index = Blueprint('index', __name__)

@bp_index.route('/')
def home():
    return render_template('index.html')


@bp_index.route("/test", methods=["GET","POST"])
def test():
    print(f"-- in test page route --")
    data = request.get_json() or {}
    print(f"data: {data}")

    return jsonify(data)