import random
from flask import Flask, jsonify, render_template, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.utils import redirect

app = Flask(__name__)

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///all_cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(5000), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


db.create_all()


@app.route("/")
def home():
    return render_template("main.html")


@app.route("/cafes")
def cafes():
    all_cafes = db.session.query(Cafe).all()
    return render_template('cafes.html', cafes=all_cafes)


@app.route("/edit-price", methods=["GET", "POST"])
def edit_price():
    if request.method == "POST":
        cafe_id = request.form["id"]
        cafe_to_update = Cafe.query.get(cafe_id)
        currency = request.form["select"]
        amount = request.form["coffee_price"]
        cafe_to_update.coffee_price = currency + amount
        db.session.commit()
        return redirect(url_for('home'))
    cafe_id = request.args.get('id')
    cafe_selected = Cafe.query.get(cafe_id)
    return render_template("edit_price.html", cafe=cafe_selected)


@app.route("/report-closed", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        api_key = request.form['api_key']
        if api_key == "TopSecretAPIKey":
            id_of_cafe_to_delete = request.form['delete_cafe_id']
            cafe_to_delete = Cafe.query.get(id_of_cafe_to_delete)
            if cafe_to_delete:
                db.session.delete(cafe_to_delete)
                db.session.commit()
            else:
                return render_template('404_page.html')
            return redirect(url_for('cafes'))
        flash('Please enter a valid API Key.')
    return render_template('delete_cafe.html')


@app.route("/search-cafe", methods=["GET", "POST"])
def search_cafe():
    query_location = request.form.get("location")
    cafe = db.session.query(Cafe).filter_by(location=query_location).all()
    if cafe:
        return render_template('search.html', cafes=cafe)
    else:
        return render_template('404_page.html')


@app.route("/add-cafe", methods=["GET", "POST"])
def add_new_cafe():
    if request.method == "POST":
        currency = request.form.get("currency")
        coffee_cost = request.form.get("coffee_price")
        price = currency + coffee_cost
        new_cafe = Cafe(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            img_url=request.form.get("img_url"),
            location=request.form.get("loc"),
            has_sockets=str2bool(request.form.get("sockets")),
            has_toilet=str2bool(request.form.get("toilet")),
            has_wifi=str2bool(request.form.get("wifi")),
            can_take_calls=str2bool(request.form.get("calls")),
            seats=request.form.get("seats"),
            coffee_price=price,
        )
        db.session.add(new_cafe)
        db.session.commit()
        p = request.form.get("wifi")
        print(p)
        return redirect(url_for('cafes'))
    return render_template('add-new-cafe.html')


@app.route("/random")
def get_random_cafe():
    random_cafes = db.session.query(Cafe).all()
    random_cafe = random.choice(random_cafes)
    return jsonify(cafe=random_cafe.to_dict())


@app.route("/all")
def get_all_cafes():
    cafes = db.session.query(Cafe).all()
    return jsonify(cafes=[cafe.to_dict() for cafe in cafes])


@app.route("/search")
def get_cafe_at_location():
    query_location = request.args.get("loc")
    cafe = db.session.query(Cafe).filter_by(location=query_location).first()
    if cafe:
        return jsonify(cafe=cafe.to_dict())
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})


@app.route('/add', methods=['POST'])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=str2bool(request.form.get("sockets")),
        has_toilet=str2bool(request.form.get("toilet")),
        has_wifi=str2bool(request.form.get("wifi")),
        can_take_calls=str2bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def patch_new_price(cafe_id):
    new_price = request.args.get("new_price")
    cafe = db.session.query(Cafe).get(cafe_id)
    if cafe:
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."}), 200
    else:
        # 404 = Resource not found
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404


@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = request.args.get("api-key")
    if api_key == "TopSecretAPIKey":
        cafe = db.session.query(Cafe).get(cafe_id)
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403


if __name__ == '__main__':
    app.run(debug=True)
