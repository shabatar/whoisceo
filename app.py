from time import strftime
from flask import Flask, render_template, flash, request
from wtforms import Form, validators, StringField
from search import check_ceo as check_ceo


class ReusableForm(Form):
    company = StringField('Company:',
                          validators=[validators.required()])


def get_time():
    time = strftime("%Y-%m-%dT%H:%M")
    return time


def flash_list(list):
    for elem in list:
        flash(str(elem))


def log_company(input):
    data = open('file.log', 'a')
    timestamp = get_time()
    data.write('DateStamp={}, Company={} \n'.format(timestamp, input))
    data.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'


@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)

    if request.method == 'POST':
        company = request.form['company']

    if form.validate():
        try:
            log_company(company)
            ceo = check_ceo(company.upper()) + ['Kata']
        except Exception as e:
            # flash('Sorry, company or CEO not found :(')
            flash(str(e))
            return render_template('index.html', form=form)
        flash_list(ceo)
    else:
        flash('Error because no data entered')

    return render_template('index.html', form=form)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
