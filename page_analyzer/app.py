from flask import (
    Flask,
    render_template,
    # request,
    # redirect,
    # url_for,
    # flash,
    # get_flashed_messages,
    # make_response,
    # session,
)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'


@app.route('/')
def index():
    errors = {}
    login = ''
    return render_template(
        'index.html',
        errors=errors,
        login=login
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
