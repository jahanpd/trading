from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateTimeField, StringField,\
    FloatField
from wtforms.validators import DataRequired, InputRequired, ValidationError
import yfinance as yf

def check_ticker(form, field):
    try:
        test = yf.Ticker(field.data)
        d = test.info
    except Exception as e:
        raise ValidationError('ticker does not return result from yfinance')


class OpenPosition(FlaskForm):
    assett = SelectField(
        'Assett',
        validators=[InputRequired()],
        choices=[
            (1, 'Equity'),
            (2, 'Currency'),
            (3, 'ETF'),
        ],
        default=1
        )
    
    ticker = StringField(
        'Ticker (yahoo finance)',
        validators=[InputRequired(), check_ticker],
        default='AAPL'
    )

    quantity = FloatField(
        'Quantity',
        validators=[InputRequired()],
        default='1'
    )

    datetime_added = DateTimeField(
        'DateTime (format=%Y-%m-%d %H:%M:%S)',
        validators=[InputRequired()]
        )
    submit = SubmitField('Open')