from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os, base64
import random
import datetime
app = Flask(__name__)
upload_folder = "/static/profile/"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "b'\xaa\xdd\xf0\xf6O\xa5\xc3\xf1c?8sK(h#'"
app.config['UPLOAD_FOLDER'] = upload_folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
db = SQLAlchemy(app)


class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, unique=True, nullable=False)
	username = db.Column(db.String(80), unique=True, nullable=False)
	password = db.Column(db.String(120), unique=True, nullable=False)
	about = db.Column(db.Text, nullable=False)
	profile_pic= db.Column(db.LargeBinary)
	following = db.Column(db.Text)
	followers = db.Column(db.Text)

class Blog(db.Model):
	__tablename__ = 'blogs'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	title = db.Column(db.Text)
	subtitle = db.Column(db.Text)
	image = db.Column(db.Text)
	datetime = db.Column(db.String)
	content = db.Column(db.Text)
	views = db.Column(db.Integer)
	comments = db.Column(db.Text)
	claps = db.Column(db.Integer)
	url = db.Column(db.Text)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
	blogl = Blog.query.order_by(Blog.id.desc()).all()
	userd = User.query
	if 'user_id' in session:
		return render_template('Blog/index.html', blogl = blogl, userd=userd, UPLOAD_FOLDER = str(userd.filter_by(id=session['user_id']).first().profile_pic, 'utf-8'))
	else:
		return render_template('Blog/index.html', blogl = blogl, userd=userd)
	# return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
	if 'user_id' in session:
		return redirect('/dashboard')
	if request.method == 'POST':
		user = request.form.get('user')
		passw = request.form.get('pass')
		if User.query.filter_by(username=user).first() is None:
			flash("Username Not Found", "error")
			return redirect('/login')
		userd = User.query.filter_by(username=user).first()
		if userd.password != passw:
			flash("Wrong Password", "error")
			return redirect('/login')
		session['user_id'] = userd.id
		print(userd.id)
		return redirect('/dashboard')
	else:
		return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
	if 'user_id' in session:
		return redirect('/dashboard')
	if request.method == 'POST':
		user = request.form.get('user')
		passw = request.form.get('pass')
		passw1 = request.form.get('pass1')
		name = request.form.get('name')
		if not user.isalnum():
			flash('Please Choose only Alphanumeric Username.' 'error')
			return redirect('/register')
		if passw != passw1:
			flash("Password Confirmation Wrong", "error")
			return redirect('/register')
		if User.query.filter_by(username=user).first() is not None:
			flash("Username already registerd", "error")
			return redirect('/register')
		with open("./static/profile/img.jpeg", "rb") as original_file:
		    encoded_string = base64.b64encode(original_file.read())
		userq = User(name = name,username=user, password=passw, about="I am a Blogger on Cyber Blog" , profile_pic=encoded_string, following="", followers="")
		db.session.add(userq)
		db.session.commit()
		userd = User.query.filter_by(username=user).first()
		'''os.mkdir(os.getcwd()+app.config['UPLOAD_FOLDER']+str(userd.id)+'/')
		default_pro_pic = '.' + url_for('static', filename='profile/img.jpeg')
		shutil.copy(default_pro_pic, '.'+url_for('static', filename=f"profile/{str(userd.id)}/"))'''
		flash("Registerd Successfully, Login Now", "success")
		return redirect('/login')
	else:
		return render_template('register.html')

@app.route('/dashboard')
def dashboard():
	if 'user_id' not in session:
		flash("Please Login", "error")
		return redirect('/login')
	userd = User.query.filter_by(id=session['user_id']).first()
	try:
		pext = userd.profile_pic
	except:
		flash("Please Login", "error")
		return redirect('/login')
	return render_template('dashboard.html', userd=userd, UPLOAD_FOLDER=str(userd.profile_pic, 'utf-8'), name=userd.name.split(' ')[0])

@app.route('/upload', methods = ['POST'])
def upload_file():
	if 'user_id' in session:
		file = request.files['image']
		if file and allowed_file(file.filename):
			file.save(os.path.join('.' + app.config['UPLOAD_FOLDER'], str(session['user_id'])+'.png'))
			userd = User.query.filter_by(id=session['user_id']).first()
			with open('.' + app.config['UPLOAD_FOLDER']+str(session['user_id'])+ '.png', 'rb') as profpicf:
				encoded_string = base64.b64encode(profpicf.read())
			os.remove('.' + url_for('static', filename=f"profile/{userd.id}.png"))
			#filename = secure_filename('img.png')
			#cext = random.choice(['png', 'jpg', 'jpeg'])
			#cname = random.choice(['profpic.', 'prof.', 'pic.', 'pict.'])
			# file.save(os.path.join('.' + app.config['UPLOAD_FOLDER']+str(session['user_id']) + '/',cname + cext))
			userd.profile_pic = encoded_string
			db.session.commit()	
			flash('Profile Photo Uploaded Successfully', 'success')
			return redirect(request.form.get('url'))
		else:
			flash('Only Upload Image Files', 'error')
			return redirect(request.form.get('url'))
	else:
		return "503", 503

@app.route('/logout')
def logout():
	if 'user_id' in session:
		session.pop('user_id', None)
		flash('Logout Successfully', 'success')
		return redirect('/login')
	else:
		return "503", 503

@app.route('/@<username>')
def blog_post(username):
	userd = User.query.filter_by(username=username).first()
	usera = User.query
	if userd is None:
		return render_template('Blog/404.html', work="username")
	else:
		UPLOAD_FOLDER1 = str(userd.profile_pic, 'utf-8')
		blogl = Blog.query.filter_by(user_id=userd.id).all()
	if 'user_id' in session:
		user1 = User.query.filter_by(id=session['user_id']).first()
		UPLOAD_FOLDER = str(user1.profile_pic, 'utf-8')
		following = user1.following.split(';')
		follow = False
		follow1 = []
		for follo in following:
			if follo == '':
				break
			if int(follo) == userd.id:
				follow1.append(True)
			else:
				follow1.append(False)
		for follo1 in follow1:
			if follo1 == True:
				follow = True
				break
		return render_template('Blog/about.html', userd=userd, blogl=blogl, UPLOAD_FOLDER=UPLOAD_FOLDER, UPLOAD_FOLDER1 = UPLOAD_FOLDER1, follow=str(follow), following=userd.following.split(';'),followers=userd.followers.split(';'), usera=usera)
	return render_template('Blog/about.html', userd=userd, blogl=blogl,  UPLOAD_FOLDER1 = UPLOAD_FOLDER1)

@app.route('/new', methods=['POST', 'GET'])
def blog_new():
	if request.method == "GET":
		if 'user_id' not in session:
			flash('Please Login to Create Blogs', 'error')
			return redirect('/login')
		userd = User.query.filter_by(id=session['user_id']).first()
		return render_template('Blog/new_blog.html', userd=userd, UPLOAD_FOLDER=str(userd.profile_pic, 'utf-8'))
	else:
		if 'user_id' in session:
			title=request.form.get('title')
			subtitle=request.form.get('subtitle')
			image = request.form.get('imgu')
			content = request.form.get('content')
			url = request.form.get('url')
			user_id = session['user_id']
			date_time = datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')
			blogd = Blog.query.filter_by(url=url).first()
			if blogd is not None:
				flash("Url Already Exists", 'error')
				userd=User.query.filter_by(id=session['user_id']).first()
				return render_template('Blog/update.html', userd=userd, UPLOAD_FOLDER=str(userd.profile_pic, 'utf-8'), ptitle="New Blog" , pstitle="Create a New Blog", title=title, subtitle=subtitle, image=image, content=content, url=url, to='/new')
			not_all = "!@#$%^&*()~`|\  /?'" + '"' + ':;<>,.+=[]{}'
			for notall in not_all:
				if notall in url:
					flash('Url Not Valid.',  'error')
					userd=User.query.filter_by(id=session['user_id']).first()
					return render_template('Blog/update.html', userd=userd, UPLOAD_FOLDER=str(userd.profile_pic, 'utf-8'), ptitle="New Blog", pstitle="Create a New Blog", title=title, subtitle=subtitle, image=image, content=content, url=url, to='/new')
			query = Blog(user_id=user_id, title=title, subtitle=subtitle, image=image, datetime=date_time, content=content, url=url, views=0, claps=0, comments="")
			db.session.add(query)
			db.session.commit()
			return redirect(f'/@{User.query.filter_by(id=session["user_id"]).first().username}/{url}')
		else:
			return "503", 503

@app.route('/@<username>/<blog_url>')
def abcd(username, blog_url):
	userd = User.query.filter_by(username=username).first()
	if userd is None:
		return render_template('Blog/404.html', work="username")
	else:
		UPLOAD_FOLDER1 = str(userd.profile_pic, 'utf-8')
	blogd = Blog.query.filter_by(url=blog_url).first()
	if blogd is None:
		return render_template('Blog/404.html', work="blog")
	else:
		comments = blogd.comments.split('--!@#$--')
		blogd.views = blogd.views + 1
		db.session.commit()
	if 'user_id' in session:
		user1 = User.query.filter_by(id=session['user_id']).first()
		UPLOAD_FOLDER = str(user1.profile_pic, 'utf-8')
		following = user1.following.split(';')
		follow = False
		follow1 = []
		for follo in following:
			if follo == '':
				break
			if int(follo) == userd.id:
				follow1.append(True)
			else:
				follow1.append(False)
		for follo1 in follow1:
			if follo1 == True:
				follow = True
				break
		return render_template('Blog/post.html', userd=userd, blogd=blogd, UPLOAD_FOLDER=UPLOAD_FOLDER, UPLOAD_FOLDER1 = UPLOAD_FOLDER1, follow=str(follow), comments=comments, user1=user1)
	else:
		return render_template('Blog/post.html', userd=userd, blogd=blogd,UPLOAD_FOLDER1 = UPLOAD_FOLDER1, comments=comments)

@app.route('/change_status', methods=['POST'])
def change_about():
	if 'user_id' in session:
		userd = User.query.filter_by(id=session['user_id']).first()
		about = request.form.get('about')
		userd.about = about
		db.session.commit()
		flash('About Changed Successfully', 'success')
		return redirect(request.form.get('url'))
	else:
		"503", 503

@app.route('/follow', methods=['POST'])
def follow():
	if 'user_id' in session:
		to = request.form.get('user_id')
		f = request.form.get('from_id')
		if int(f) != session['user_id']:
			return "503", 503
		user2 = User.query.filter_by(id=f).first()
		user1 = User.query.filter_by(id=to).first()
		user1.followers = user1.followers+f+';'
		db.session.commit()
		user2.following = user2.following+to+';'
		db.session.commit()
		return "Following Successfully"
	else:
		return "503", 503

@app.route('/clap', methods=['POST'])
def clap():
	blog_id = request.form.get('blog_id')
	blogd = Blog.query.filter_by(id=blog_id).first()
	if blogd is None:
		return "503", 503
	blogd.claps = blogd.claps + 1
	db.session.commit()
	return "Clapped Successfully"

@app.route('/comment', methods=['POST'])
def comment():
	name=request.form.get('name')
	bid=request.form.get('blog_id')
	comment=request.form.get('comment')
	blogd = Blog.query.filter_by(id=bid).first()
	blogd.comments = blogd.comments + name+'--!@#$--'+comment+'--!@#$--'
	db.session.commit()
	return "Commented Successfully"

@app.route('/update/<blog_id>', methods=['GET', 'POST'])
def update(blog_id):
	if request.method == 'GET':
		if 'user_id' in session:
			blogd = Blog.query.filter_by(id=blog_id).first()
			if blogd is None:
				return render_template('Blog/404.html', work="blog")
			if blogd.user_id != session['user_id']:
				return "503", 503
			title,subtitle,image,content,url = blogd.title, blogd.subtitle, blogd.image, blogd.content, blogd.url
			userd=User.query.filter_by(id=session['user_id']).first()
			return render_template('Blog/update.html', userd=userd, UPLOAD_FOLDER=str(userd.profile_pic, 'utf-8'), ptitle="Edit Blog", pstitle="Edit Your Blog", title=title, subtitle=subtitle, image=image, content=content, url=url, to=f'/update/{blogd.id}')
		else:
			return "503", 503
	else:
		if 'user_id' in session:
			title=request.form.get('title')
			subtitle=request.form.get('subtitle')
			image = request.form.get('imgu')
			content = request.form.get('content')
			url = request.form.get('url')
			blogd = Blog.query.filter_by(id=blog_id).first()
			if blogd is None:
				return render_template('Blog/404.html', work="blog")
			if blogd.user_id != session['user_id']:
				return "503", 503
			blogd.title=title
			blogd.subtitle = subtitle
			blogd.image = image
			blogd.content = content
			blogd.url = url
			db.session.commit()
			return redirect('/')

@app.route('/stats/<blog_id>')
def stats(blog_id):
	if 'user_id' in session:
			blogd = Blog.query.filter_by(id=blog_id).first()
			if blogd is None:
				return render_template('Blog/404.html', work="blog")
			if blogd.user_id != session['user_id']:
				return "503", 503
			return f'Your Blog Stats: <br> Views: {blogd.views} <br> Claps: {blogd.claps}'
	else:
		return "503", 503


if __name__ == '__main__':
	app.run(debug=True,port=8000)