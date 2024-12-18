from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime
from werkzeug.utils import secure_filename

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
    viewed_images = db.Column(db.Text, default='')
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

# Add this debug decorator
def debug_route(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"\n=== Route Debug: {f.__name__} ===")
        result = f(*args, **kwargs)
        if hasattr(result, 'get_data'):
            # For template responses, check context
            context = result._get_context()
            print(f"Template context:")
            print(f"- active_events: {context.get('active_events')}")
            print(f"- current_season: {context.get('current_season')}")
        print("===========================\n")
        return result
    return decorated_function

@app.route('/')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    current_season = get_current_season()
    active_events = get_active_events()
    
    images_root = 'images'
    
    # Get images from enabled seasons and events
    available_images = []
    if os.path.exists(images_root):
        # Get enabled seasons
        enabled_seasons = Season.query.filter_by(is_enabled=True).all()
        enabled_season_names = [season.name for season in enabled_seasons]
        
        # Get enabled events
        enabled_events = Event.query.filter_by(is_enabled=True).all()
        enabled_event_names = [event.name for event in enabled_events]
        
        # Combine enabled folders
        enabled_folders = enabled_season_names + enabled_event_names
        
        print(f"Enabled folders: {enabled_folders}")  # Debug print
        
        for folder in os.listdir(images_root):
            folder_path = os.path.join(images_root, folder)
            if (os.path.isdir(folder_path) and 
                folder in enabled_folders and 
                not folder.lower().endswith('battlepass')):
                try:
                    files = os.listdir(folder_path)
                    print(f"Checking folder {folder}, found {len(files)} files")  # Debug print
                    
                    for filename in files:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            image = Image.query.filter_by(
                                filename=filename,
                                season=folder
                            ).first()
                            
                            if not image:
                                image = Image(
                                    filename=filename,
                                    season=folder,
                                    required_level=0
                                )
                                db.session.add(image)
                                db.session.commit()
                            
                            available_images.append(image)
                            print(f"Added image: {filename}")  # Debug print
                            
                except Exception as e:
                    print(f"Error processing folder {folder}: {str(e)}")
    
    if not available_images:
        flash('No images available')
        return render_template('index.html', 
                             image=None,
                             user=current_user,
                             current_season=current_season,
                             active_events=active_events,
                             season=current_season.name if current_season else None)

    random_image = random.choice(available_images)
    
    # Add tokens if this image hasn't been viewed before
    if not current_user.has_viewed_image(random_image.id):
        current_user.tokens += 1
        print(f"Added token for viewing new image. Current tokens: {current_user.tokens}")
    
    current_user.add_viewed_image(random_image.id)
    db.session.commit()
    
    print(f"Serving random image: {random_image.filename} from {random_image.season}")  # Debug print
    
    return render_template('index.html', 
                         image=random_image,
                         user=current_user,
                         current_season=current_season,
                         active_events=active_events,
                         season=current_season.name if current_season else None)

    
    random_image = random.choice(available_images)
    
    return render_template('index.html', 
                         image=random_image,
                         user=current_user,
                         current_season=current_season.name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    current_season = get_current_season()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html', season=current_season.name)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    current_season = get_current_season()
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
    return render_template('register.html', season=current_season.name)

# Update the battlepass route to show all items with lock status
@app.route('/battlepass')
@login_required
def battlepass():
    current_season = get_current_season()
    active_events = get_active_events()
    
    images_root = 'images'
    
    # Add debug prints
    print(f"Current season: {current_season.name}")
    print(f"Looking for battlepass images in: {images_root}/{current_season.name}_battlepass")
    
    battlepass_images = []
    battlepass_folder = f"{current_season.name}_battlepass"
    folder_path = os.path.join(images_root, battlepass_folder)
    
    if not os.path.exists(folder_path):
        flash(f'No battlepass available for {current_season.name}')
        print(f"Battlepass folder not found: {folder_path}")
        return render_template('battlepass.html', 
                             battlepass_images=[],
                             user=current_user,
                             current_season=current_season,
                             active_events=active_events,
                             season=current_season.name if current_season else None)
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            print(f"Processing image: {filename}")
            image = Image.query.filter_by(
                filename=filename,
                season=battlepass_folder
            ).first()
            
            if not image:
                image = Image(
                    filename=filename,
                    season=battlepass_folder,
                    required_level=0  # We can keep this as 0 since we're not using levels
                )
                db.session.add(image)
                db.session.commit()
            
            battlepass_images.append(image)
    
    print(f"Total battlepass images found: {len(battlepass_images)}")
    
    return render_template('battlepass.html', 
                         battlepass_images=battlepass_images,
                         user=current_user,
                         current_season=current_season,
                         active_events=active_events,
                         season=current_season.name if current_season else None)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        return "Access denied", 403
    
    current_season = get_current_season()
    images_root = 'images'
    
    # Get all seasons and events
    all_seasons = Season.query.order_by(Season.name).all()
    all_events = Event.query.order_by(Event.name).all()
    
    # Combine seasons and events for the image upload dropdown
    folder_choices = [season.name for season in all_seasons]
    folder_choices.extend([event.name for event in all_events])
    
    if request.method == 'POST':
        if 'add_event' in request.form:
            event_name = request.form.get('event_name')
            start_date = datetime.strptime(request.form.get('event_start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('event_end_date'), '%Y-%m-%d') if request.form.get('event_end_date') else None
            
            try:
                # Create the event folder
                event_folder = os.path.join(images_root, event_name)
                os.makedirs(event_folder, exist_ok=True)
                
                # Create the event in database
                new_event = Event(
                    name=event_name,
                    start_date=start_date,
                    end_date=end_date,
                    is_enabled=True
                )
                db.session.add(new_event)
                db.session.commit()
                flash(f'Event {event_name} added successfully')
                
            except Exception as e:
                flash(f'Error creating event: {str(e)}')
                print(f"Error creating event: {str(e)}")
            
            return redirect(url_for('admin'))
            
        elif 'delete_event' in request.form:
            event_id = request.form.get('event_id')
            event = Event.query.get(event_id)
            if event:
                try:
                    # Delete the event folder
                    event_folder = os.path.join(images_root, event.name)
                    if os.path.exists(event_folder):
                        import shutil
                        shutil.rmtree(event_folder)
                    
                    # Delete from database
                    db.session.delete(event)
                    db.session.commit()
                    flash(f'Event {event.name} deleted successfully')
                    
                except Exception as e:
                    flash(f'Error deleting event: {str(e)}')
                    print(f"Error deleting event: {str(e)}")
                
                return redirect(url_for('admin'))
                
        elif 'toggle_event' in request.form:
            event_id = request.form.get('event_id')
            event = Event.query.get(event_id)
            if event:
                event.is_enabled = not event.is_enabled
                db.session.commit()
                status = "enabled" if event.is_enabled else "disabled"
                flash(f'Event {event.name} {status}')
                return redirect(url_for('admin'))
        
        if 'set_current_season' in request.form:
            season_id = request.form.get('season_id')
            print(f"Setting current season ID: {season_id}")  # Debug print
            
            # First, unset all current seasons
            Season.query.update({Season.is_current: False})
            db.session.commit()
            
            # Then set the new current season
            season = Season.query.get(season_id)
            if season:
                print(f"Found season: {season.name}")  # Debug print
                season.is_current = True
                season.is_enabled = True  # Automatically enable current season
                db.session.commit()
                flash(f'Current season set to {season.name}')
            else:
                print("Season not found!")  # Debug print
                flash('Error: Season not found')
            
            return redirect(url_for('admin'))
            
        if 'upload_images' in request.form:
            season_name = request.form.get('season')
            uploaded_files = request.files.getlist('images[]')
            
            if uploaded_files and season_name:
                success_count = 0
                error_count = 0
                
                for file in uploaded_files:
                    if file and allowed_file(file.filename):
                        try:
                            filename = secure_filename(file.filename)
                            season_folder = os.path.join(images_root, season_name)
                            
                            # Create season folder if it doesn't exist
                            if not os.path.exists(season_folder):
                                os.makedirs(season_folder)
                            
                            # Save the file
                            file_path = os.path.join(season_folder, filename)
                            file.save(file_path)
                            
                            # Add to database if not exists
                            image = Image.query.filter_by(
                                filename=filename,
                                season=season_name
                            ).first()
                            
                            if not image:
                                image = Image(
                                    filename=filename,
                                    season=season_name,
                                    required_level=0
                                )
                                db.session.add(image)
                            
                            success_count += 1
                            
                        except Exception as e:
                            print(f"Error uploading {filename}: {str(e)}")
                            error_count += 1
                
                db.session.commit()
                
                if success_count > 0:
                    flash(f'Successfully uploaded {success_count} images to {season_name}')
                if error_count > 0:
                    flash(f'Failed to upload {error_count} images')
                
                return redirect(url_for('admin'))
            
        elif 'add_season' in request.form:
            season_name = request.form.get('season_name')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
            
            try:
                # Create the season folders
                season_folder = os.path.join(images_root, season_name)
                battlepass_folder = os.path.join(images_root, f"{season_name}_battlepass")
                
                os.makedirs(season_folder, exist_ok=True)
                os.makedirs(battlepass_folder, exist_ok=True)
                
                # Create the season in the database
                new_season = Season(
                    name=season_name,
                    start_date=start_date,
                    end_date=end_date,
                    is_enabled=True
                )
                db.session.add(new_season)
                db.session.commit()
                flash(f'Season {season_name} added successfully with folders created')
                
            except Exception as e:
                flash(f'Error creating season: {str(e)}')
                print(f"Error creating season folders: {str(e)}")
            
            return redirect(url_for('admin'))
                
        elif 'delete_season' in request.form:
            season_id = request.form.get('season_id')
            season = Season.query.get(season_id)
            if season:
                if season.is_current:
                    flash('Cannot delete current season')
                    return redirect(url_for('admin'))
                
                try:
                    # Delete the season folders
                    season_folder = os.path.join(images_root, season.name)
                    battlepass_folder = os.path.join(images_root, f"{season.name}_battlepass")
                    
                    if os.path.exists(season_folder):
                        import shutil
                        shutil.rmtree(season_folder)
                    
                    if os.path.exists(battlepass_folder):
                        import shutil
                        shutil.rmtree(battlepass_folder)
                    
                    # Delete the season from database
                    db.session.delete(season)
                    db.session.commit()
                    flash(f'Season {season.name} deleted successfully')
                    
                except Exception as e:
                    flash(f'Error deleting season: {str(e)}')
                    print(f"Error deleting season: {str(e)}")
                
                return redirect(url_for('admin'))
        
        elif 'toggle_season' in request.form:
            season_id = request.form.get('season_id')
            season = Season.query.get(season_id)
            if season:
                season.is_enabled = not season.is_enabled
                db.session.commit()
                status = "enabled" if season.is_enabled else "disabled"
                flash(f'Season {season.name} {status}')
                return redirect(url_for('admin'))
    
    # Get fresh data after any changes
    all_seasons = Season.query.order_by(Season.name).all()
    current_season = Season.query.filter_by(is_current=True).first()
    
    print(f"Current season: {current_season.name if current_season else 'None'}")  # Debug print
    print(f"All seasons: {[s.name for s in all_seasons]}")  # Debug print
    
    return render_template('admin.html', 
                         folder_seasons=folder_choices,
                         all_images=Image.query.all(),
                         all_seasons=all_seasons,
                         all_events=all_events,
                         current_season=current_season,
                         season=current_season.name if current_season else None)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            password_hash=generate_password_hash('meowwww'),
            is_admin=True,
            tokens=999
        )
        db.session.add(admin)
        db.session.commit()
        print("\n=== Admin Credentials ===")
        print("Username: admin")
        print("Password: meowwww")
        print("=======================\n")

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    is_enabled = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)

def get_current_season():
    current_season = Season.query.filter_by(is_current=True).first()
    if not current_season:
        # Delete any existing seasons to avoid conflicts
        Season.query.delete()
        db.session.commit()
        
        # Create Season 2 as the only season
        default_season = Season(
            name="season2",
            start_date=datetime.now(),
            is_current=True,
            is_enabled=True
        )
        db.session.add(default_season)
        db.session.commit()
        return default_season
    
    return current_season

@app.route('/unlock_image/<int:image_id>')
@login_required
def unlock_image(image_id):
    if current_user.tokens >= 1:
        current_user.tokens -= 1
        current_user.add_viewed_image(image_id)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Not enough tokens'})

@app.route('/images/<path:filename>')
def serve_image(filename):
    print(f"\n=== Image Request Debug ===")
    print(f"Requested filename: {filename}")
    
    try:
        # Split the path into folder and filename
        parts = filename.split('/')
        if len(parts) != 2:
            print(f"Error: Invalid path format - {filename}")
            return "Invalid path", 400
            
        folder, image_name = parts
        print(f"Folder: {folder}")
        print(f"Image name: {image_name}")
        
        # Build and check the file path
        file_path = os.path.join('images', folder, image_name)
        print(f"Full file path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        print(f"Is file: {os.path.isfile(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"Error: File not found - {file_path}")
            return "File not found", 404
            
        # Check directory permissions
        directory = os.path.join('images', folder)
        print(f"Serving from directory: {directory}")
        print(f"Directory exists: {os.path.exists(directory)}")
        print(f"Directory readable: {os.access(directory, os.R_OK)}")
        
        # Try to serve the file
        print("Attempting to serve file...")
        response = send_from_directory(directory, image_name)
        print("File served successfully")
        print("=========================\n")
        return response
        
    except Exception as e:
        print(f"Error serving image: {str(e)}")
        print("=========================\n")
        return f"Error serving image: {str(e)}", 500

def recreate_db():
    """Function to recreate the database with the new schema"""
    print("\n=== Recreating Database ===")
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    
    # Create default seasons for existing folders
    images_root = 'images'
    if os.path.exists(images_root):
        for folder in os.listdir(images_root):
            if (os.path.isdir(os.path.join(images_root, folder)) and 
                folder.lower().startswith('season') and 
                not folder.lower().endswith('battlepass')):
                season = Season(
                    name=folder,
                    start_date=datetime.now(),
                    is_current=(folder == 'season2'),  # Make season2 current by default
                    is_enabled=True
                )
                db.session.add(season)
                print(f"Created season: {folder}")
    
    db.session.commit()
    print("Database recreation completed!")
    print("===========================\n")

# Initialize the database
with app.app_context():
    try:
        # Try to access the new column to test if it exists
        Season.query.filter_by(is_enabled=True).first()
    except Exception as e:
        print("Database needs to be recreated...")
        recreate_db()
        create_default_admin()

def get_active_events():
    """Get currently active events"""
    current_time = datetime.now()
    return Event.query.filter(
        Event.is_enabled == True,
        Event.start_date <= current_time,
        (Event.end_date >= current_time) | (Event.end_date == None)
    ).all()

@app.route('/collection')
@login_required
def collection():
    current_season = get_current_season()
    active_events = get_active_events()
    
    # Get all images the user has viewed
    viewed_images = []
    
    if current_user.viewed_images:  # Check if there are any viewed images
        viewed_image_ids = set(filter(None, current_user.viewed_images.split(',')))
        
        for image_id in viewed_image_ids:
            try:
                image = Image.query.get(int(image_id))
                if image:
                    viewed_images.append(image)
            except (ValueError, TypeError):
                continue  # Skip invalid IDs
    
    # Sort images by season/event
    viewed_images.sort(key=lambda x: x.season)
    
    print(f"Found {len(viewed_images)} viewed images")  # Debug print
    
    # Always return the template, even if no images found
    return render_template('collection.html',
                         viewed_images=viewed_images,
                         user=current_user,
                         current_season=current_season,
                         active_events=active_events)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
