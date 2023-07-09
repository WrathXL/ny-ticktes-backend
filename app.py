from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# App configuration

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)
CORS(app)


# Tables

carts_products = db.Table(
    "carts_products",
    db.Column(
        "cart_id", db.Integer, db.ForeignKey("cart.id"), primary_key=True
    ),
    db.Column(
        "product_id", db.Integer, db.ForeignKey("product.id"), primary_key=True
    ),
)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100))
    slug = db.Column(db.String(20), nullable=False, unique=True)
    url = db.Column(db.String(100))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    products = db.relationship(
        "Product",
        secondary=carts_products,
        lazy="subquery",
        backref=db.backref("products", lazy=True),
    )


# Helpers


def product_to_json(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "slug": product.slug,
        "url": product.url,
    }


# API


@app.route("/products")
def get_products():
    products = Product.query.all()
    return [product_to_json(product) for product in products]


@app.route("/products/<slug>")
def get_product_by_id(slug):
    product = Product.query.filter_by(slug=slug).first()
    return product_to_json(product) if product else {}


@app.route("/products", methods=["POST"])
def create_product():
    print(request.json)
    products = [
        Product(
            name=product["name"],
            price=product["price"],
            description=product["description"],
            slug=product["slug"],
            url=product["url"],
        )
        for product in request.json
    ]
    for product in products:
        db.session.add(product)
    db.session.commit()
    return [product_to_json(product) for product in products]


@app.route("/cart/<int:cart_id>")
def get_cart(cart_id):
    cart = Cart.query.get(cart_id)
    if cart is None:
        return (
            render_template_string(
                "PageNotFound {{ errorCode }}", errorCode="404"
            ),
            404,
        )
    return [product_to_json(product) for product in cart.products]


@app.route("/cart", methods=["POST"])
def create_cart():
    cart = Cart()
    db.session.add(cart)
    db.session.commit()
    return {"id": cart.id}


@app.route("/cart/<int:cart_id>/add/<int:product_id>", methods=["POST"])
def add_product_to_cart(cart_id, product_id):
    cart = Cart.query.get(cart_id)
    product = Product.query.get(product_id)
    cart.products.append(product)
    db.session.commit()
    return [product_to_json(product) for product in cart.products]


@app.route("/cart/<int:cart_id>/remove/<int:product_id>", methods=["DELETE"])
def remove_product_from_cart(cart_id, product_id):
    cart = Cart.query.get(cart_id)
    product = Product.query.get(product_id)
    cart.products.remove(product)
    db.session.commit()
    return [product_to_json(product) for product in cart.products]


if __name__ == "__main__":
    app.run(debug=True)
