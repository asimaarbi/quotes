from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

from flask_admin.contrib.sqla import ModelView
import flask_admin as admin
from flask_admin import expose
from flask_admin.base import AdminIndexView
from flask_admin.menu import MenuLink

from flask_restful import Resource, Api, reqparse
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
ma = Marshmallow()

api = Api(app)


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=True)
    author = db.Column(db.String(50), nullable=True)
    english = db.Column(db.String(1000), nullable=True)
    portuguese = db.Column(db.String(1000), nullable=True)
    spanish = db.Column(db.String(1000), nullable=True)
    color = db.Column(db.String(20), nullable=True)


class QuoteSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Quote


class QuoteResource(Resource):
    def post(self):
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('date', type=str, help='Enter date in format(d-m-y)', required=True)
        parser.add_argument('author', type=str, help='Enter author', required=True)
        parser.add_argument('english', type=str, help='Enter quote in english', required=True)
        parser.add_argument('portoguese', type=str, help='Enter quote in portoguese', required=True)
        parser.add_argument('spanish', type=str, help='Enter quote in spanish', required=True)
        parser.add_argument('color', type=str, help='Enter color in #', required=True)
        args = parser.parse_args(strict=True)

        custom_args = {}
        for k, v in args.items():
            if v:
                custom_args.update({k: v})

        quote = Quote(**custom_args)

        db.session.add(quote)
        db.session.commit()

        schema = QuoteSchema()
        return schema.jsonify(quote)


class AuthourQouteResource(Resource):
    def get(self, author):
        quote = Quote.query.filter_by(author=author).all()
        if not quote:
            return {'message': 'No qoute found'}, 404

        schema = QuoteSchema(many=True)
        return schema.jsonify(quote)


class GetQuoteResource(Resource):
    def get(self):
        schema = QuoteSchema(many=True)
        return schema.dump(Quote.query.all())


@app.route('/create', methods=['POST'])
def create():
    dated = request.form['date']
    author = request.form['author']
    english = request.form['english']
    spanish = request.form['spanish']
    portuguese = request.form['portuguese']
    color = request.form['color']
    quote = Quote()
    quote.date = dated
    quote.author = author
    quote.english = english
    quote.spanish = spanish
    quote.portuguese = portuguese
    quote.color = color
    db.session.add(quote)
    db.session.commit()
    return redirect('/quote')


@app.route('/', methods=['GET', 'POST'])
def home():
    return redirect('/admin')


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'barrozricardo@gmail.com' and request.form['password'] == 'Rumi%94Ei':
        session['logged_in'] = True
        return redirect('/admin')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return render_template('login.html')


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not session.get('logged_in'):
            return render_template('login.html')
        # date = datetime.today().strftime('%d-%m-%Y')
        # quote = Quote.query.filter_by(date=date).first()
        # return self.render('admin/index.html')
        return redirect('/quote')


class QuoteModelView(ModelView):
    can_edit = True
    can_create = True


admin = admin.Admin(app, name=' ', index_view=MyAdminIndexView(name=' '), url='/admin')
admin.add_view(QuoteModelView(Quote, db.session, name='Quotes', url='/quote'))
admin.add_link(MenuLink(name='Logout', category='', url="/logout"))
api.add_resource(AuthourQouteResource, '/api/author_quotes/<author>')
api.add_resource(GetQuoteResource, '/api/quotes/')

if __name__ == '__main__':
    db.init_app(app)
    ma.init_app(app)
    db.create_all(app=app)
    app.run(host='0.0.0.0', port=7000, debug=True)
