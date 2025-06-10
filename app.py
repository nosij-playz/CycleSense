from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.secret_key = '5t5t5t'  # Change this to a secure value
app.config['SQLALCHEMY_DATABASE_URI'] = 'Your mysql db link here'
db = SQLAlchemy(app)
class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # This references user.id
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phno = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer, nullable=True)
class SelfCare(db.Model):
    __tablename__ = 'selfcare'
    sy_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    note = db.Column(db.String(100), nullable=True)
    symptoms = db.Column(db.String(255), nullable=True)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    # Relationship to UserProfile
    profiles = db.relationship('UserProfile', backref='user', lazy=True, cascade="all, delete-orphan")
class Period(db.Model):
    __tablename__ = 'period'
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    symptoms = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def calculate_period_gap(start_date_1, start_date_2):
    start_date_1 = datetime.datetime.strptime(start_date_1, "%Y-%m-%d")
    start_date_2 = datetime.datetime.strptime(start_date_2, "%Y-%m-%d")
    period_gap = start_date_2 - start_date_1
    return period_gap.days
@app.route('/')
def index():
    if 'username' in session:
        periods = Period.query.filter_by(user_id=session['user_id']).all()
        user_profile = UserProfile.query.filter_by(login_id=session['user_id']).first()  # Fetch user profile

        avg_period_gap = None
        if len(periods) > 1:
            period_gaps = []
            for i in range(1, len(periods)):
                gap = calculate_period_gap(periods[i-1].start_date, periods[i].start_date)
                period_gaps.append(gap)
            avg_period_gap = sum(period_gaps) / len(period_gaps)

        return render_template('home.html', periods=periods, avg_period_gap=avg_period_gap, user_profile=user_profile)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/select_symptoms', methods=['GET', 'POST'])
def select_symptoms():
    note = None  # Initialize note variable
    # Fetch all symptoms from the selfcare table
    symptoms = SelfCare.query.with_entities(SelfCare.symptoms).distinct().all()
    # Convert the list of tuples to a flat list
    symptoms_list = [symptom[0] for symptom in symptoms]

    if request.method == 'POST':
        selected_symptom = request.form['symptoms']
        # Fetch the note corresponding to the selected symptom
        note_entry = SelfCare.query.filter_by(symptoms=selected_symptom).first()
        note = note_entry.note if note_entry else "No note available for this symptom."

    return render_template('select_symptoms.html', symptoms=symptoms_list, note=note)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can log in now.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_period', methods=['POST'])
def add_period():
    if 'username' in session:
        start_date = request.form['start_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        symptoms = request.form['symptoms']

        period = Period(start_date=start_date, start_time=start_time, end_time=end_time, symptoms=symptoms, user_id=session['user_id'])
        db.session.add(period)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all tables
    app.run(debug=True)
