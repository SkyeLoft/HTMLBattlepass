from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ieuriuywgs9orihzwiesytrgher0uth0feir'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'images'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    battle_pass_level = db.Column(db.Integer, default=0)
    experience_points = db.Column(db.Integer, default=0)
    viewed_images = db.Column(db.Text, default='')  # Add this line
    tokens = db.Column(db.Integer, default=0)

    def add_viewed_image(self, image_id):
        viewed = set(filter(None, self.viewed_images.split(',')))
        viewed.add(str(image_id))
        self.viewed_images = ','.join(viewed)
        
    def has_viewed_image(self, image_id):
        viewed = set(filter(None, self.viewed_images.split(',')))
        return str(image_id) in viewed

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    season = db.Column(db.String(80), nullable=False)
    required_level = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    current_season = get_current_season()
    images_root = 'images'
    
    print(f"Looking for images in: {images_root}")
    print(f"Directory exists: {os.path.exists(images_root)}")
    
    # Only get images from season folders (not battlepass)
    available_images = []
    if os.path.exists(images_root):
        for folder in os.listdir(images_root):
            folder_path = os.path.join(images_root, folder)
            print(f"Checking folder: {folder}")
            if os.path.isdir(folder_path) and folder.lower().startswith('season') and not folder.lower().endswith('battlepass'):
                print(f"Found valid season folder: {folder}")
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        print(f"Found image: {filename}")
                        # Try to find image in database
                        image = Image.query.filter_by(
                            filename=filename,
                            season=folder
                        ).first()
                        
                        # If image not in database, add it
                        if not image:
                            print(f"Adding new image to database: {filename}")
                            image = Image(
                                filename=filename,
                                season=folder,
                                required_level=0  # No level requirement for regular season images
                            )
                            db.session.add(image)
                            db.session.commit()
                        
                        available_images.append(image)
    
    print(f"Total available images: {len(available_images)}")

    # Check if there are any available images
    if not available_images:
        flash('No images available')
        return render_template('index.html', 
                             image=None,
                             user=current_user,
                             season=current_season)

    random_image = random.choice(available_images)
    current_user.add_viewed_image(random_image.id)
    db.session.commit()
    
    return render_template('index.html', 
                         image=random_image,
                         user=current_user,
                         season=random_image.season)

    
    random_image = random.choice(available_images)
    
    return render_template('index.html', 
                         image=random_image,
                         user=current_user,
                         season=random_image.season)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Update the battlepass route to show all items with lock status
@app.route('/battlepass')
@login_required
def battlepass():
    print(f"User level: {current_user.battle_pass_level}")
    
    current_season = get_current_season()
    images_root = 'images'
    
    # Calculate user's progress
    viewed_count = len(set(filter(None, current_user.viewed_images.split(','))))
    
    # Get all battlepass images
    battlepass_images = []
    battlepass_folder = f"{current_season}_battlepass"
    folder_path = os.path.join(images_root, battlepass_folder)
    
    if os.path.exists(folder_path):
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image = Image.query.filter_by(
                    filename=filename,
                    season=battlepass_folder
                ).first()
                
                if not image:
                    image = Image(
                        filename=filename,
                        season=battlepass_folder,
                        required_level=len(battlepass_images) + 1
                    )
                    db.session.add(image)
                    db.session.commit()
                
                battlepass_images.append(image)
    
    return render_template('battlepass.html', 
                         battlepass_images=battlepass_images,
                         user=current_user,
                         viewed_count=viewed_count,
                         season=current_season)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return "Access denied", 403
    
    images_root = 'images'
    
    # Get seasons from folder structure
    seasons = []
    if os.path.exists(images_root):
        seasons = [d for d in os.listdir(images_root) 
                  if os.path.isdir(os.path.join(images_root, d))]
    seasons.sort()  # Sort seasons alphabetically
    
    # Get all images from database
    all_images = Image.query.all()
    print(f"Total images in database: {len(all_images)}")
    
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image file')
            return redirect(request.url)
            
        file = request.files['image']
        season = request.form.get('season')
        required_level = int(request.form.get('required_level', 0))
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file:
            # Create season folder if it doesn't exist
            season_folder = os.path.join(images_root, season)
            if not os.path.exists(season_folder):
                os.makedirs(season_folder)
                print(f"Created folder: {season_folder}")
                
            filename = file.filename
            file_path = os.path.join(season_folder, filename)
            file.save(file_path)
            
            # Debug information
            print(f"Saved file to: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            
            # Check if image already exists in database
            existing_image = Image.query.filter_by(
                filename=filename,
                season=season
            ).first()
            
            if existing_image:
                existing_image.required_level = required_level
                print(f"Updated existing image: {filename}")
                flash('Image updated successfully')
            else:
                new_image = Image(
                    filename=filename,
                    season=season,
                    required_level=required_level
                )
                db.session.add(new_image)
                print(f"Added new image to database: {filename}")
            
            db.session.commit()
            flash(f'Image uploaded successfully to {season}')
            
    return render_template('admin.html', 
                         seasons=seasons,
                         all_images=all_images)

@app.route('/gain_experience')
@login_required
def gain_experience():
    current_user.experience_points += 10
    if current_user.experience_points >= 100:
        current_user.battle_pass_level += 1
        current_user.experience_points = 0
    db.session.commit()
    return redirect(url_for('index'))

def create_default_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('meowwww'),  # Change this password!
            is_admin=True,
            battle_pass_level=999  # Give admin max level
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created!")
        print("Username: admin")
        print("Password: adminpass")

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)

def get_current_season():
    current_season = Season.query.filter_by(is_current=True).first()
    return current_season.name if current_season else "season1"

@app.route('/unlock_image/<int:image_id>')
@login_required
def unlock_image(image_id):
    if current_user.tokens >= 10:
        current_user.tokens -= 10
        current_user.add_viewed_image(image_id)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Not enough tokens'})

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()  # Create default admin user

    app.run(debug=True, host='0.0.0.0')
