from time import strftime

from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, validators

from ui.search import check_ceo_in_file as check_ceo

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'

class ReusableForm(Form):
    company = TextField('Company:', validators=[validators.required()])

def get_time():
    time = strftime("%Y-%m-%dT%H:%M")
    return time

def write_log(input):
    data = open('file.log', 'a')
    timestamp = get_time()
    data.write('DateStamp={}, Company={} \n'.format(timestamp, input))
    data.close()

@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)

    if request.method == 'POST':
        company = request.form['company']

    if form.validate():
        ceo = []
        try:
            write_log(company)
            ceo = check_ceo(company.upper())
        except:
            flash('Sorry, company or CEO not found :(')
            return render_template('index.html', form=form)
        flash('\n' + '\n'.join(list(ceo)))
    else:
        flash('Error because no data entered')

    return render_template('index.html', form=form)

if __name__ == "__main__":
    app.run()
