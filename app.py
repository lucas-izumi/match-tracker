from flask import Flask, render_template, redirect, url_for, request
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, case

from config import Config
from models import db, User, Hero, Match


# =========================================================
# CRIAÇÃO E CONFIGURAÇÃO DO APP
# =========================================================
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# =========================================================
# INICIALIZAÇÃO DO BANCO (Flask 3.x)
# =========================================================
with app.app_context():
    db.create_all()

    # Usuário padrão
    if not User.query.first():
        user = User(
            username="admin",
            password_hash=generate_password_hash("admin")
        )
        db.session.add(user)

    # Heróis padrão
    if not Hero.query.first():
        heroes = [
            Hero(name="Oscilio", is_default=True),
            Hero(name="Katsu"),
            Hero(name="Arakni 5L!p3d 7hRu 7h3 cR4X"),
            Hero(name="Kayo Underhanded Cheat"),
            Hero(name="Lyath Goldmane"),
            Hero(name="Pleiades"),
            Hero(name="Tuffnut"),
            Hero(name="Arakni Huntsman"),
            Hero(name="Arakni Marionette"),
            Hero(name="Betsy"),
            Hero(name="Boltyn"),
            Hero(name="Bravo"),
            Hero(name="Cindra"),
            Hero(name="Dash IO"),
            Hero(name="Dorinthea"),
            Hero(name="Fai"),
            Hero(name="Fang"),
            Hero(name="Florian"),
            Hero(name="Gravy Bones"),
            Hero(name="Ira"),
            Hero(name="Jarl"),
            Hero(name="Kassai"),
            Hero(name="Kayo Armed and Dangerous"),
            Hero(name="Levia"),
            Hero(name="Marlynn"),
            Hero(name="Maxx"),
            Hero(name="Olympia"),
            Hero(name="Rhinar"),
            Hero(name="Puffin"),
            Hero(name="Riptide"),
            Hero(name="Teklovossen"),
            Hero(name="Uzuri"),
            Hero(name="Valda"),
            Hero(name="Verdance"),
            Hero(name="Victor"),
            Hero(name="Vynnset")
        ]
        db.session.add_all(heroes)

    db.session.commit()


# =========================================================
# LOGIN MANAGER
# =========================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================================================
# ROTAS DE AUTENTICAÇÃO
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(
            user.password_hash,
            request.form["password"]
        ):
            login_user(user)
            return redirect(url_for("matches"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# =========================================================
# ROTAS PRINCIPAIS
# =========================================================
@app.route("/")
@login_required
def matches():
    matches = Match.query.filter_by(
        user_id=current_user.id
    ).order_by(Match.created_at.desc()).all()

    return render_template("matches.html", matches=matches)


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_match():
    heroes = Hero.query.all()
    default_hero = Hero.query.filter_by(is_default=True).first()

    if request.method == "POST":
        match = Match(
            hero_id=request.form["hero"],
            opponent_hero_id=request.form["opponent"],
            who_started=request.form["who_started"],
            winner=request.form["winner"],
            sideboard=request.form.get("sideboard"),
            comments=request.form.get("comments"),
            user_id=current_user.id
        )

        db.session.add(match)
        db.session.commit()
        return redirect(url_for("matches"))

    return render_template(
        "new_match.html",
        heroes=heroes,
        default_hero=default_hero
    )


# =========================================================
# ESTATÍSTICAS E GRÁFICOS
# =========================================================
@app.route("/stats")
@login_required
def stats():
    total_matches = Match.query.filter_by(
        user_id=current_user.id
    ).count()

    wins = Match.query.filter_by(
        user_id=current_user.id,
        winner="me"
    ).count()

    losses = total_matches - wins
    win_rate = round((wins / total_matches) * 100, 2) if total_matches else 0

    # Win rate por herói (EU)
    hero_stats = (
        db.session.query(
            Hero.name,
            func.count(Match.id).label("total"),
            func.sum(case((Match.winner == "me", 1), else_=0)).label("wins")
        )
        .join(Match, Match.hero_id == Hero.id)
        .filter(Match.user_id == current_user.id)
        .group_by(Hero.name)
        .all()
    )

    # Win rate por herói OPONENTE
    opponent_stats = (
        db.session.query(
            Hero.name,
            func.count(Match.id).label("total"),
            func.sum(case((Match.winner == "me", 1), else_=0)).label("wins")
        )
        .join(Match, Match.opponent_hero_id == Hero.id)
        .filter(Match.user_id == current_user.id)
        .group_by(Hero.name)
        .all()
    )

    return render_template(
        "stats.html",
        total_matches=total_matches,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        hero_stats=hero_stats,
        opponent_stats=opponent_stats
    )


# =========================================================
# START DO SERVIDOR
# =========================================================
if __name__ == "__main__":
    app.run()
