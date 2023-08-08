from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    title = "hello world"
    data = range(10)
    return render_template('login.html', title1=title, data=data)


if __name__ == '__main__':
    app.run()
