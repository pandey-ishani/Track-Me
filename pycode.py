import os
import random
import math
from flask import Flask, url_for, render_template, request, redirect, session
from flask import request, flash, abort ,g
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import sqlalchemy
from flask_login import login_user , logout_user , current_user , login_required, LoginManager
from flask_login import UserMixin
from flask_session import Session
from jinja2 import nodes
from jinja2.ext import Extension
from matplotlib import pyplot as plt
import matplotlib
from matplotlib import style


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "logindatabase.db"))
dbgraph_file=  "sqlite:///{}".format(os.path.join(project_dir, "graphdatabase.db"))


app = Flask(__name__)
SQLALCHEMY_TRACK_MODIFICATIONS = True

app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_DATABASE_URI"] = dbgraph_file

app.config['TESTING'] = False
app.secret_key = '\xdf\xcd1\x17\x18w2:\xb77,j5\xc8*\xaeb\xe1/U.F\x17\xde'
dblogin = SQLAlchemy(app)
dbgraph= SQLAlchemy(app)

app.jinja_env.add_extension('jinja2.ext.do')
login = LoginManager()
login.init_app(app)
login.login_view = 'login'

@login.user_loader
def load_user(user_id):
	return User.query.get(user_id)



class User(dblogin.Model):
	id= dblogin.Column(dblogin.Integer, unique=True)
	username = dblogin.Column(dblogin.String(80),primary_key=True)
	password = dblogin.Column(dblogin.String(80), unique=True)
	activity=  dblogin.Column(dblogin.String(80))

	def __init__(self, id, username, password,activity):
		self.username = username
		self.password = password
		self.activity= activity

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False
 	def get_id(self):
		return unicode(self.id)

	def __repr__(self):
		return '<User %r>' %(self.username)


class Work(dbgraph.Model):
	
	name=dbgraph.Column(dbgraph.String(80),primary_key=True)
	day = dbgraph.Column(dbgraph.Integer, nullable=False,primary_key=True)
	hour = dbgraph.Column(dbgraph.Integer, nullable=False)

	def __repr__(self,name,day,hour):
		self.name=name
		self.day=day
		self.hour=hour


labels = []

values = []
colors = [
    "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
    "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
    "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]
lastday=0



@app.route('/', methods=['GET', 'POST'])
def front():
	if 'logged_in' not in session:
		session['logged_in']=False
	return render_template('trackme.html')



@app.route('/home', methods=['GET', 'POST'])
def home():
	user_id = session.get('id')
	if session['logged_in'] is False:
		
		return render_template('index.html')
	else:
		nme = session['this']
		user = User.query.filter_by(username=nme).first()
		print(nme)
		act= user.activity
		print(act)
		lastday=0
		del labels[:]
		del values[:]

		return redirect(url_for('graph',uname=nme,activity=act))
	return render_template('index.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
	if request.form:
		try:
			
			exists = User.query.filter_by(username=request.form.get('username')).scalar()
			new_user = User(id=1,username=request.form.get("username"), password=request.form.get("password"),activity=request.form.get("activity"))

			if exists is not None:
				flash("Username already taken! Can't register")
			else:
				dblogin.session.add(new_user)
				dblogin.session.commit()
				flash("Registered Successfully")
				return render_template('login.html')
		except Exception as e:
			print("Failed to add")
			print(e)
			flash("password already taken! Can't register")
			dblogin.session.rollback();
	return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
	user_id = session.get('id')
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	if request.method == 'GET':
		return render_template("login.html")
	nme=User(id=1,username=request.form.get('username'), password=request.form.get("password"),activity="xyz")
	user = User.query.filter_by(username=request.form.get('username'),password=request.form.get('password')).first()
	session['this'] = ''
	if user is None:
		flash('Invalid username or password')
		session['logged_in']=False
		return redirect(url_for('login'))
	else:
		login_user(user)
		session['logged_in'] = True
		del labels[:]
		del values[:]
		session['this'] = request.form.get('username')
		return redirect(url_for('home'))
	return render_template('login.html', title='Sign In')




@app.route("/<uname>", methods=["GET", "POST"])
def graph(uname):
	x=0
	y=0
	amount = None
	activity = None
	app.config["SQLALCHEMY_DATABASE_URI"] = dbgraph_file
	user= User.query.filter_by(username=uname).first()
	if user is not  None:
		activity=user.activity
		name=user.username
	
	obj=Work.query.filter_by(name=uname).all()
	lastday=0
	if obj is not None:
		for i in obj:
			lastday=i.day
	
	if request.method == 'POST':
		try:

			work = Work(name=uname,day=request.form.get('day'),hour=request.form.get('hour'))	
			x=work.day
			y=work.hour
			lastday=int(x)
			dbgraph.session.add(work)
			del labels[:]
			del values[:]
			
			dbgraph.session.commit()
		except Exception as e:
			dbgraph.session.rollback()
			print("Failed to add")
			print(e)
	
	amount = Work.query.all()
	return render_template("home.html",lday=lastday,amount=amount,labels=labels,values=values,nme=uname,activity=activity)


@app.route("/update/<name>", methods=["POST"])
def update(name):
    try:
        dayp = request.form.get("dayp")
        
        newhour = request.form.get("newhour")
        oldhour = request.form.get("oldhour")
        work = Work.query.filter_by(day=dayp,name=name).first()

        v1= oldhour
        v2= newhour
        work.hour=newhour
        
        dbgraph.session.commit()

        index=labels.index(int(dayp))
        values[index]=v2
        
    except Exception as e:
        print("Couldn't update")
        print(e)
    return redirect("/home")



@app.route("/delete/<name>", methods=["POST"])
def delete(name):
    day = request.form.get("day")
    work = Work.query.filter_by(day=day,name=name).first()
    index=labels.index(int(day))
    del labels[index]
    del values[index]
    dbgraph.session.delete(work)
    dbgraph.session.commit()
    return redirect("/home")




@app.route('/line/<activity>')
def line(activity):

	xlabel=[]
	yvalue=[]
	g=0
	if len(labels)!=0:
		g=max(labels)+1
	for i in range(1,g):
		if i in labels:
			pos=labels.index(i)
			xlabel.append(i)
			yvalue.append(values[pos])
		else:
			xlabel.append(i)
			yvalue.append(0)

	return render_template('line.html', title=activity, max=20, labels=xlabel, values=yvalue)


@app.route('/matgraph/<activity>')
def plot(activity):
	xlabel=[]
	yvalue=[]
	g=0
	if len(labels)!=0:
		g=max(labels)+1
	for i in range(1,g):
		if i in labels:
			pos=labels.index(i)
			xlabel.append(i)
			yvalue.append(values[pos])
		else:
			xlabel.append(i)
			yvalue.append(0)

	return render_template('plot.html',labels=xlabel,values=yvalue,plt=plt,act=activity,style=style)


@app.route('/record/<name>/<activity>')
def record(name,activity):
	amount = Work.query.all()
	return render_template('record.html',nme=name,activity=activity,amount=amount)

@app.route('/stats/<activity>', methods=['GET', 'POST'])
def stats(activity):
	cur=1
	maxi=0
	#streak
	duplicate=[]
	for i in labels:
		index=labels.index(i)

		if values[index]!=0:
			duplicate.append(i)

	duplicate.sort()
	if len(duplicate)!=0:

		for i in xrange(1,len(duplicate)):
			if duplicate[i]==duplicate[i-1]+1:
				cur=cur+1
			else:
				cur=1
			if cur>maxi:
				maxi=cur
    #best
	maxi2=0
	maxi3=0
	sum=0
	avg=0
	poordays=0
	poor=0
	if len(values)!=0:
		for i in xrange(0,len(values)):
			if values[i]>maxi2:
				maxi2=values[i]
    #average
	
		for i in xrange(0,len(labels)):
			if labels[i]>maxi3:
				maxi3=labels[i]  
			         
		for i in xrange(0,len(values)):
			sum=sum+values[i]
		if maxi3 != 0:	
			avg=sum/float(maxi3)
		else:
			avg=0

    #below average performance
	
		for i in xrange(0,len(values)):
			if values[i]<avg:
				poordays=poordays+1

		poor=poordays/float(maxi3)		
		
		avg=round(avg,2)
		poor=round(poor,2)
		
	return render_template('stats.html',streak=maxi,average=avg,badpercent=poor,best=maxi2,activity=activity)




@app.route("/logout")
def logout():
	session['logged_in'] = False
	lastday=0
	return redirect(url_for('home'))


if __name__ == "__main__":
	jinja_env = Environment(extensions=['jinja2.ext.do'])
	sess.init_app(app)
	app.run(debug=True)
	

   