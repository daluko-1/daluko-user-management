from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"  # ⚠️ replace with env var for production

# ---- Login Manager ----
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---- In-Memory Database (replace with real DB in production) ----
users_db = {
    1: {"id": 1, "name": "Daniel Aluko", "email": "danielaluko22@gmail.com",
        "password": generate_password_hash("test123"), "role": "Admin"},
    2: {"id": 2, "name": "John Doe", "email": "john@example.com",
        "password": generate_password_hash("customer123"), "role": "Customer"}
}
next_id = 3


# ---- User Model ----
class User(UserMixin):
    def __init__(self, id, name, email, password, role):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    user_data = users_db.get(int(user_id))
    if user_data:
        return User(**user_data)
    return None


# ---- Routes ----
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = next((u for u in users_db.values() if u["email"] == email), None)
        if user and check_password_hash(user["password"], password):
            login_user(User(**user))
            flash("Login successful!", "success")

            # Role-based redirect
            if user["role"] == "Admin":
                return redirect(url_for("home"))
            else:
                return redirect(url_for("profile"))
        else:
            flash("Invalid email or password", "danger")
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/home")
@login_required
def home():
    # Admin dashboard
    if current_user.role == "Admin":
        return render_template("home.html")
    return redirect(url_for("profile"))


@app.route("/profile")
@login_required
def profile():
    # Customer profile page
    return render_template("profile.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


# ---- Admin APIs ----
@app.route("/users", methods=["GET"])
@login_required
def get_users():
    if current_user.role != "Admin":
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(list(users_db.values()))


@app.route("/user", methods=["POST"])
@login_required
def add_user():
    global next_id
    if current_user.role != "Admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    new_user = {
        "id": next_id,
        "name": data["name"],
        "email": data["email"],
        "password": generate_password_hash(data["password"]),
        "role": data["role"]
    }
    users_db[next_id] = new_user
    next_id += 1
    return jsonify(new_user), 201


@app.route("/user/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    if current_user.role != "Admin":
        return jsonify({"error": "Unauthorized"}), 403
    if user_id in users_db:
        del users_db[user_id]
        return jsonify({"message": "User deleted"}), 200
    return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)

