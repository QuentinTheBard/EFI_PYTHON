from functools import wraps
from datetime import datetime, timedelta
import hashlib
import jwt
from datetime import datetime

from flask import Flask, jsonify, make_response, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from marshmallow import fields


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/matias'
app.config['SECRET_KEY'] = "acalepongoloquequiera"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)


class Country(db.Model):
    __tablename__ = 'country'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __str__(self):
        return self.name

    """ 
    SI NO SE LE ESTABLECE UN INIT 
    CADA VEZ QUE SE GENERE EL OBJETO DEBERAN
    ESTABLECER QUE PARAMETRO ES CADA UNO
    DE LO CONTRARIO EL PRIMER PARAMETRO SERA
    CONSIDERADO COMO ID
    """
    def __init__(self, name):
        self.name = name


class Province(db.Model):
    __tablename__ = 'province'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    idContry = db.Column(db.Integer, ForeignKey('country.id'))


class Location(db.Model):
    __tablename__ = 'location'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    idProvince = db.Column(db.Integer, ForeignKey('province.id'))


class Sex(db.Model):
    __tablename__ = 'sex'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=True)


class DniType(db.Model):
    __tablename__ = 'dniType'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=True)


class Person(db.Model):
    __tablename__ = 'person'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    idTypeDni = db.Column(db.Integer, ForeignKey('dniType.id'))
    dni = db.Column(db.Integer, nullable=True)
    address = db.Column(db.String(100), nullable=True)
    idLocation = db.Column(db.Integer, ForeignKey('location.id'))
    idCountry = db.Column(db.Integer, ForeignKey('country.id'))
    born = db.Column(db.TIMESTAMP, nullable=True)
    idSex = db.Column(db.Integer, ForeignKey('sex.id'))
    phone = db.Column(db.Integer, nullable=False)
    mail = db.Column(db.String(50), nullable=False)
    uploadDate = db.Column(db.TIMESTAMP, nullable=True)
    active = db.Column(db.Boolean, nullable=True, default=True)
    countries = db.relationship('Country')


class UserType(db.Model):
    __tablename__ = 'userType'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=True)


class User(db.Model):
    __tablename__='user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True, unique=True)
    password = db.Column(db.String(100), nullable=True)
    idUserType = db.Column(db.Integer, ForeignKey('userType.id'))
    fCarga = db.Column(db.TIMESTAMP, nullable=True)
    idPerson = db.Column(db.Integer, ForeignKey('person.id'))


# Serializadores 
class CountrySchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String()


class CountryWithoutIdSchema(ma.Schema):
    name = fields.String()


class ProvinceSchema(ma.Schema):
    name = fields.String()
    idCountry = fields.Integer()


class PersonSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String()
    idTypeDni = fields.Integer()
    dni = fields.Integer()
    address = fields.String()
    idLocation = fields.Integer()
    idCountry = fields.Integer()
    countries = fields.Nested(CountrySchema, exclude=['id',])
    born = fields.String()
    idSex = fields.Integer()
    phone = fields.Integer()
    mail = fields.String()
    uploadDate = fields.Date()
    active = fields.Boolean()


class UserSchema(ma.Schema):
    id = fields.Integer()
    name = fields.String()
    idUserType = fields.Integer()



# SI NO LE DETERMINO EL METODO; SIEMPRE ES UN GET
@app.route('/countries')
def get_countries():
    country = db.session.query(Country).all()    
    countrie_schema = CountrySchema().dump(country, many=True)
    return jsonify(countrie_schema)


# POST
@app.route('/countries', methods=['POST'])
def add_countrie():
    if request.method == 'POST':
        data = request.json
        name = data['name']
        countries = db.session.query(Country).all()
        for country in countries:
            if name == country.name:
                return jsonify({"Mensaje":"Ya existe un pais con ese nombre"}),404
        new_countrie = Country(name=name)
        db.session.add(new_countrie)
        db.session.commit()
        countrie_schema = CountryWithoutIdSchema().dump(
           new_countrie
        )
        return jsonify(
            {"Mensaje":"El pais se creo correctamente"},
            {"Pais": countrie_schema}
        ), 201


@app.route('/countries_names')
def get_country_names():
    
    countrie_schema = CountryWithoutIdSchema().dump(
        db.session.query(Country).all(), many=True
    )
    return jsonify(countrie_schema)


@app.route('/persons')
def get_persons():
    """
    Paginado recibe 2 parametros principales
    PAGINA (pag) y CANTIDAD (can)
    Y un tercer parametro obligatorio que es 
    error_out que se pude setear como vacio
    """

    try:
        can = int(request.args.get('can'))
        pag = int(request.args.get('pag'))
        persons = Person.query.paginate(pag, can, error_out="No se obtienen valores").items
    except:
        persons = db.session.query(Person).all()
        pag = 1
        can = 'Todos'

    persons_schema = PersonSchema().dump(persons, many=True)
    return jsonify(dict(
        pagina=pag,
        cantidad=can,
        result=persons_schema
        )
    )


@app.route('/users')
def get_users():
    users = db.session.query(User).all()
    if len(users) == 0:
        return jsonify(dict(Mensaje='No existen usuario aun')), 400
    users_schema = UserSchema().dump(users, many=True)
    return jsonify(dict(Usuarios=users_schema)), 200


@app.route('/users', methods=['POST'])
def add_user():
    if request.method == 'POST':
        data = request.json
        name = data['name']
        password = data['password'].encode('utf-8')
        idUserType = data['idUserType']
        idPerson = data['idPerson']

        pass_hash = hashlib.md5(password).hexdigest()

        try:
            new_user = User(
                name=name,
                password=pass_hash,
                idUserType=idUserType,
                idPerson=idPerson,
                fCarga=datetime.now()
            )
            db.session.add(new_user)
            db.session.commit()

            result = UserSchema().dump(new_user)

            if result:
                return jsonify(dict(NuevoUsuario=result))

        except:
            return jsonify(dict(Error="Username en uso")), 201


@app.route('/login', methods=['GET'])
def login():
    auth = request.authorization
    username = auth['username']
    password = auth['password'].encode('utf-8')

    if not auth or not auth.username or not auth.password:
        return make_response(
            {"Error": "No se enviaron todos lo parametros auth"}, 401
        )

    hasheada = hashlib.md5(password).hexdigest()

    user_login = db.session.query(User).filter_by(
        name=username).filter_by(
            password=hasheada
        ).first()

    if user_login:
        token = jwt.encode(
            {
                'usuario': username,
                'id_usuario': user_login.id,
                'exp': datetime.utcnow() + timedelta(minutes=5)
            },
            app.secret_key
        )
        session['api_session_token'] = token

        return jsonify({"Token": token.decode("UTF-8")})

    return make_response(
            {"Error": "Algun dato no coincide"}, 401
        )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({"ERROR":"Token is missing"}),401

        try: 
            datatoken = jwt.decode(token, app.secret_key)
            print(datatoken)
            userLogged = User.query.filter_by(id=datatoken['id_usuario']).first()
        except:
            return jsonify(
                {"ERROR": "Token is invalid or expired"}
            ),401

        return f(userLogged, *args, **kwargs)

    return decorated

@app.route('/provinces')
@token_required
def get_provinces(userLogged):
    if userLogged.idUserType == 2:
        provinces = db.session.query(Province).all()
        provice_shemma = ProvinceSchema().dump(provinces, many=True)
        return jsonify(provice_shemma)
    else:
        return jsonify({"Error":"Ud no tiene permiso"})

@app.route('/provinces', methods=['post'])
def add_province():
    if request.method == 'POST':
        data = request.json
        name = data['name']
        country_id = data['country_id']
        try:
            new_province = Province(idContry=country_id, name=name)
            db.session.add(new_province)
            db.session.commit()
            
            provice_schema = ProvinceSchema().dump(new_province)

            return jsonify(
                {"Mensaje" : "La Provincia se creo correctamente"},
                {"Pais": provice_schema}
            ), 201

        except:
            return jsonify(
                {"Mensaje": "Algo salio mal, valide los datos"},
            ), 404


if __name__ == '__main':
    app.run(debug=True)
