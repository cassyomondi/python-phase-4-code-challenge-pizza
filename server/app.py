#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Restaurant, RestaurantPizza, Pizza
from sqlalchemy.exc import IntegrityError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# --------- Resources ---------

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [r.to_dict(only=("id", "name", "address")) for r in restaurants], 200


class RestaurantByID(Resource):
    def get(self, id):
        r = Restaurant.query.get(id)
        if not r:
            return {"error": "Restaurant not found"}, 404
        return r.to_dict(
            only=("id", "name", "address", "restaurant_pizzas"),
            rules={"-restaurant_pizzas.restaurant": ...}
        ), 200

    def delete(self, id):
        r = Restaurant.query.get(id)
        if not r:
            return {"error": "Restaurant not found"}, 404

        db.session.delete(r)
        db.session.commit()
        return "", 204


class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [p.to_dict(only=("id", "name", "ingredients")) for p in pizzas], 200


class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return {"errors": ["validation errors"]}, 400

        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        try:
            new_rp = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )
            db.session.add(new_rp)
            db.session.commit()

        except (ValueError, IntegrityError):
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400   # <- changed here

        return new_rp.to_dict(
            only=("id", "price", "pizza_id", "restaurant_id", "pizza", "restaurant"),
            rules={
                "-pizza.restaurant_pizzas": ...,
                "-restaurant.restaurant_pizzas": ...
            }
        ), 201



# --------- Routes ---------
api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantByID, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
