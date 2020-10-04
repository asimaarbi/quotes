from flask import Flask, redirect, render_template, request, session
from flask_admin.form import DateTimeField
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
        parser.add_argument('date', type=str, help='username of the User', required=True)
        parser.add_argument('author', type=str, help='Fisrt name of the User', required=True)
        parser.add_argument('english', type=str, help='Last name of the User', required=True)
        parser.add_argument('portoguese', type=str, help='Email of the User', required=True)
        parser.add_argument('spanish', type=str, help='Password of the User', required=True)
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


def load_user(session):
    if session['logged_in'] == session:
        return True


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'admin' and request.form['password'] == 'password':
        session['logged_in'] = True
        return redirect('/quote')
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
        quote = Quote.query.filter_by(date='2020-10-03').first()
        return self.render('admin/index.html', name=quote)


class QuoteModelView(ModelView):
    can_edit = True
    can_create = True
    form_overrides = dict(date=DateTimeField)

    def create_model(self, form):
        model = super().create_model(form)
        date = str(form.data['date']).split(' ')
        model.date = date[0]
        db.session.add(model)
        db.session.commit()
        return model


admin = admin.Admin(app, name='Qoutes', index_view=MyAdminIndexView(name='Home'), url='/admin')
admin.add_view(QuoteModelView(Quote, db.session, url='/quote'))
admin.add_link(MenuLink(name='Logout', category='', url="/logout"))
api.add_resource(AuthourQouteResource, '/api/author_quotes/<author>')
api.add_resource(GetQuoteResource, '/api/quotes/')

if __name__ == '__main__':
    db.init_app(app)
    ma.init_app(app)
    db.create_all(app=app)
    app.run(host='0.0.0.0', port=7000, debug=True)
