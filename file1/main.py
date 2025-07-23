from flask import Flask, json, redirect, render_template, flash, request, session, url_for
from flask.globals import request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, logout_user, login_user, LoginManager, current_user
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = "nishu"

# Load configuration from config.json
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

# Configure Flask-Mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/covid'
db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    srfid = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(50))
    dob = db.Column(db.String(1000))


class Hospitaluser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    email = db.Column(db.String(50))
    password = db.Column(db.String(1000))


class Hospitaldata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20), unique=True)
    hname = db.Column(db.String(100))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)


class Trig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)
    querys = db.Column(db.String(50))
    date = db.Column(db.String(50))


class Bookingpatient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    srfid = db.Column(db.String(20), unique=True)
    bedtype = db.Column(db.String(100))
    hcode = db.Column(db.String(20))
    spo2 = db.Column(db.Integer)
    pname = db.Column(db.String(100))
    pphone = db.Column(db.String(100))
    paddress = db.Column(db.String(100))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/trigers")
def trigers():
    query = Trig.query.all()
    return render_template("trigers.html", query=query)


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=="POST":
        srfid=request.form.get('srf')
        email=request.form.get('email')
        dob=request.form.get('DOB')
        encpassword=generate_password_hash(dob)
        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or srif is already taken","warning")
            return render_template("usersignup.html")
        new_user = User(srfid=srfid, email=email, dob=encpassword)
        db.session.add(new_user)
        db.session.commit()
                
        flash("SignUp Success Please Login","success")
        return render_template("userlogin.html")

    return render_template("usersignup.html")

#login
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        srfid=request.form.get('srf')
        dob=request.form.get('DOB')
        user=User.query.filter_by(srfid=srfid).first()
        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login Success","info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")


    return render_template("userlogin.html")


@app.route('/hospitallogin', methods=['POST', 'GET'])
def hospitallogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Hospitaluser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success", "info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials", "danger")
            return render_template("hospitallogin.html")
    return render_template("hospitallogin.html")


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params['user'] and password == params['password']):
            session['user'] = username
            flash("login success", "info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials", "danger")
    return render_template("admin.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
    return redirect(url_for('login'))


@app.route('/addHospitalUser', methods=['POST', 'GET'])
def hospitalUser():
    if('user' in session and session['user'] == params['user']):
        if request.method == "POST":
            hcode = request.form.get('hcode')
            email = request.form.get('email')
            password = request.form.get('password')
            encpassword = generate_password_hash(password)
            hcode = hcode.upper()
            emailUser = Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email or srif is already taken", "warning")
            new_hospital_user = Hospitaluser(
                hcode=hcode, email=email, password=encpassword)
            db.session.add(new_hospital_user)
            db.session.commit()

            # Sending mail
            mail.send_message('COVID CARE CENTER', sender=params['gmail-user'], recipients=[email], body=f"Welcome thanks for choosing us\nYour Login Credentials Are:\n Email Address: {email}\nPassword: {password}\n\nHospital Code {hcode}\n\n Do not share your password\n\n\nThank You...")

            flash("Data Sent and Inserted Successfully", "warning")
            return render_template("addHosUser.html")
    else:
        flash("Login and try Again", "warning")
        return render_template("addHosUser.html")


@app.route("/test")
def test():
    try:
        a = Test.query.all()
        print(a)
        return f'MY DATABASE IS CONNECTED'
    except Exception as e:
        print(e)
        return f'MY DATABASE IS NOT CONNECTED {e}'


@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")
    return redirect('/admin')


@app.route("/addhospitalinfo",methods=['POST','GET'])
def addhospitalinfo():
    email=current_user.email
    posts=Hospitaluser.query.filter_by(email=email).first()
    code=posts.hcode
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()

    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubed')
        ibed=request.form.get('icubed')
        vbed=request.form.get('vbed')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already Present you can update it..","primary")
            return render_template("hospitaldata.html")
        if huser:
                new_hospital_data = Hospitaldata(hcode=hcode, hname=hname, normalbed=nbed,
                                                  hicubed=hbed, icubed=ibed, vbed=vbed)
                db.session.add(new_hospital_data)
                db.session.commit()
                flash("Data Is Added", "primary")
        else:
            flash("Hospital Code not Exist","warning")
    
    return render_template("hospitaldata.html",postsdata=postsdata)

@app.route("/existing-pdetails", methods=['GET'])  # Change the endpoint name
@login_required
def existing_pdetails():
    # Your existing function implementation here

    if isinstance(current_user, User):  # Check if the current user is of type User
        code = current_user.srfid
        data = Bookingpatient.query.filter_by(srfid=code).first()
        return render_template("detials.html", data=data)
    else:
        flash("User type is not supported", "error")
        return redirect(url_for('login'))  # Or redirect to another page





@app.route("/hedit/<string:id>", methods=['POST', 'GET'])
@login_required
def hedit(id):
    posts = Hospitaldata.query.filter_by(id=id).first()
    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        db.session.execute(f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        db.session.commit()
        flash("Slot Updated", "info")
        return redirect("/addhospitalinfo")

    return render_template("hedit.html", posts=posts)


@app.route("/hdelete/<string:id>", methods=['POST', 'GET'])
@login_required
def hdelete(id):
    query = text(f"DELETE FROM hospitaldata WHERE id = :id")
    db.session.execute(query, {"id": id})
    db.session.commit()
    flash("Date Deleted", "danger")
    return redirect("/addhospitalinfo")



@app.route("/pdetails", methods=['GET'])
@login_required
def pdetails():
    code = current_user.srfid
    data = Bookingpatient.query.filter_by(srfid=code).first()
    return render_template("detials.html", data=data)


@app.route("/slotbooking", methods=['POST', 'GET'])
@login_required
def slotbooking():
    if request.method == "POST":
        srfid = request.form.get('srfid')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')

        # Update operation on the appropriate bed type column
        query = text(f"UPDATE hospitaldata SET `{bedtype.lower()}` = `{bedtype.lower()}` - 1 WHERE hcode = :hcode")
        db.session.execute(query, {"hcode": hcode})

        # Create Bookingpatient instance and add to session
        booking_patient = Bookingpatient(srfid=srfid, bedtype=bedtype, hcode=hcode, spo2=spo2, pname=pname, pphone=pphone, paddress=paddress)
        db.session.add(booking_patient)
        db.session.commit()
        flash("Slot is Booked kindly Visit Hospital for Further Procedure", "success")
    
    query = Hospitaldata.query.all()
    return render_template("booking.html", query=query)


if __name__ == "__main__":
    app.run(debug=True)
