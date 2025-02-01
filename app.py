from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import csv
from datetime import datetime
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a secure secret key

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
DATA_DIR = 'data'
PARTICIPANTS_CSV = os.path.join(DATA_DIR, 'participants.csv')
SESSIONS_CSV = os.path.join(DATA_DIR, 'sessions.csv')
PAYMENTS_CSV = os.path.join(DATA_DIR, 'payments.csv')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def init_csv_files():
    """Initialize CSV files with headers and sample data if they don't exist"""
    if not os.path.exists(PARTICIPANTS_CSV):
        with open(PARTICIPANTS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'email', 'session', 'registration_date'])
    
    if not os.path.exists(SESSIONS_CSV):
        with open(SESSIONS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'date', 'capacity', 'price'])
            writer.writerows([
                ['1', 'Web Development Basics', '2025-04-01', '30', '99.99'],
                ['2', 'Python for Beginners', '2025-04-02', '25', '79.99'],
                ['3', 'Data Science Introduction', '2025-04-03', '20', '149.99']
            ])
    
    if not os.path.exists(PAYMENTS_CSV):
        with open(PAYMENTS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'participant_id', 'amount', 'payment_date', 'status'])

init_csv_files()

def get_sessions():
    """Retrieve all sessions from the CSV file"""
    try:
        with open(SESSIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Error reading sessions: {e}")
        return []

def get_session_name(session_id):
    """Get session name by ID"""
    try:
        sessions = get_sessions()
        return next((session['name'] for session in sessions if session['id'] == str(session_id)), '')
    except Exception as e:
        logger.error(f"Error getting session name: {e}")
        return ''

def get_session_price(session_id):
    """Get session price by ID"""
    try:
        sessions = get_sessions()
        session = next((s for s in sessions if s['id'] == str(session_id)), None)
        return float(session['price']) if session else 0.0
    except Exception as e:
        logger.error(f"Error getting session price: {e}")
        return 0.0

def validate_payment(amount, session_id):
    """Validate payment amount against session price"""
    try:
        expected_price = get_session_price(session_id)
        return abs(float(amount) - expected_price) < 0.01
    except Exception as e:
        logger.error(f"Payment validation error: {e}")
        return False

def add_participant(name, email, session):
    """Add a new participant to the CSV file"""
    try:
        participant_id = len(get_participants()) + 1
        with open(PARTICIPANTS_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                participant_id,
                name,
                email,
                session,
                datetime.now().strftime('%Y-%m-%d')
            ])
        return participant_id
    except Exception as e:
        logger.error(f"Error adding participant: {e}")
        raise

def get_participants():
    """Retrieve all participants from the CSV file"""
    try:
        with open(PARTICIPANTS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Error reading participants: {e}")
        return []

def get_participant(participant_id):
    """Get participant by ID"""
    try:
        participants = get_participants()
        return next((p for p in participants if p['id'] == str(participant_id)), None)
    except Exception as e:
        logger.error(f"Error getting participant: {e}")
        return None

def update_participant(participant_id, name, email, session):
    """Update participant information"""
    try:
        participants = get_participants()
        updated = False
        updated_participants = []
        
        for participant in participants:
            if participant['id'] == str(participant_id):
                participant.update({
                    'name': name,
                    'email': email,
                    'session': session
                })
                updated = True
            updated_participants.append(participant)
        
        if updated:
            with open(PARTICIPANTS_CSV, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'session', 'registration_date'])
                writer.writeheader()
                writer.writerows(updated_participants)
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating participant: {e}")
        return False

def delete_participant(participant_id):
    """Delete participant and associated payment"""
    try:
        # Remove participant
        participants = [p for p in get_participants() if p['id'] != str(participant_id)]
        with open(PARTICIPANTS_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'session', 'registration_date'])
            writer.writeheader()
            writer.writerows(participants)
        
        # Remove associated payment
        payments = [p for p in get_payments() if p['participant_id'] != str(participant_id)]
        with open(PAYMENTS_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'participant_id', 'amount', 'payment_date', 'status'])
            writer.writeheader()
            writer.writerows(payments)
        return True
    except Exception as e:
        logger.error(f"Error deleting participant: {e}")
        return False

def add_payment(participant_id, amount):
    """Add a new payment record"""
    try:
        payment_id = len(get_payments()) + 1
        with open(PAYMENTS_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                payment_id,
                participant_id,
                amount,
                datetime.now().strftime('%Y-%m-%d'),
                'completed'
            ])
        return payment_id
    except Exception as e:
        logger.error(f"Error adding payment: {e}")
        raise

def get_payments():
    """Retrieve all payments from the CSV file"""
    try:
        with open(PAYMENTS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logger.error(f"Error reading payments: {e}")
        return []

def get_participant_payment(participant_id):
    """Get payment information for a participant"""
    try:
        payments = get_payments()
        return next((p for p in payments if p['participant_id'] == str(participant_id)), None)
    except Exception as e:
        logger.error(f"Error getting participant payment: {e}")
        return None

def generate_certificate(name, session_name, date):
    """Generate a certificate as a PNG image"""
    try:
        width = 1000
        height = 700
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw border
        draw.rectangle([(40, 40), (width-40, height-40)], outline='#4F46E5', width=3)
        draw.rectangle([(50, 50), (width-50, height-50)], outline='#4F46E5', width=1)
        
        # Try different font paths
        font_paths = [
            'arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            'DejaVuSans.ttf'
        ]
        
        # Find working font
        fonts = {'large': None, 'medium': None, 'small': None}
        for font_path in font_paths:
            try:
                fonts['large'] = ImageFont.truetype(font_path, 48)
                fonts['medium'] = ImageFont.truetype(font_path, 36)
                fonts['small'] = ImageFont.truetype(font_path, 24)
                break
            except Exception:
                continue
        
        # Fallback to default if no fonts work
        if not fonts['large']:
            fonts = {
                'large': ImageFont.load_default(),
                'medium': ImageFont.load_default(),
                'small': ImageFont.load_default()
            }
        
        # Draw certificate text
        text_items = [
            (width/2, 150, 'Certificate of Completion', '#1F2937', fonts['large']),
            (width/2, 250, 'This certifies that', '#4B5563', fonts['small']),
            (width/2, 300, name, '#1F2937', fonts['medium']),
            (width/2, 350, 'has successfully completed', '#4B5563', fonts['small']),
            (width/2, 400, session_name, '#1F2937', fonts['medium']),
            (width/2, 500, f'Date: {date}', '#4B5563', fonts['small'])
        ]
        
        for x, y, text, fill, font in text_items:
            try:
                draw.text((x, y), text, fill=fill, font=font, anchor='mm')
            except Exception:
                # Fallback without anchor if it fails
                text_width = font.getsize(text)[0]
                draw.text((x - text_width/2, y), text, fill=fill, font=font)
        
        # Save to BytesIO
        img_io = BytesIO()
        image.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        return img_io
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        raise

# Routes
@app.route('/')
def index():
    """Home page route"""
    sessions = get_sessions()
    return render_template('index.html', sessions=sessions)

@app.route('/register', methods=['POST'])
def register():
    """Handle registration form submission"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        session = request.form.get('session')
        
        if not all([name, email, session]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('index'))
        
        participant_id = add_participant(name, email, session)
        session_price = get_session_price(session)
        
        # Process payment
        try:
            payment_id = add_payment(participant_id, session_price)
            flash('Registration successful!', 'success')
            return redirect(url_for('success', participant_id=participant_id))
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            flash('Error processing payment. Please try again.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/success/<int:participant_id>')
def success(participant_id):
    """Success page after registration"""
    participant = get_participant(participant_id)
    if participant:
        session_name = get_session_name(participant['session'])
        payment = get_participant_payment(participant_id)
        return render_template('success.html', 
                             participant=participant,
                             session_name=session_name,
                             payment=payment)
    return redirect(url_for('index'))

@app.route('/participants')
def participants():
    """List all participants"""
    try:
        # Read participants data
        with open(PARTICIPANTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_participants = list(reader)

        # Get additional information for each participant
        for participant in all_participants:
            # Get session name
            participant['session_name'] = get_session_name(participant['session'])
            
            # Get payment info
            payment = get_participant_payment(participant['id'])
            participant['payment_status'] = payment['status'] if payment else 'Pending'
            if payment:
                participant['payment_amount'] = payment['amount']
            
        return render_template('participants.html', 
                             participants=all_participants,
                             sessions=get_sessions())
    except Exception as e:
        logger.error(f"Error loading participants: {e}")
        flash('Error loading participants list.', 'error')
        return redirect(url_for('index'))

@app.route('/edit/<int:participant_id>', methods=['GET', 'POST'])
def edit_participant_route(participant_id):
    """Edit participant information"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            session = request.form.get('session')
            
            if not all([name, email, session]):
                flash('All fields are required!', 'error')
                return redirect(url_for('edit_participant_route', participant_id=participant_id))
            
            if update_participant(participant_id, name, email, session):
                flash('Participant updated successfully!', 'success')
                return redirect(url_for('participants'))
            else:
                flash('Participant not found!', 'error')
                return redirect(url_for('participants'))
                
        except Exception as e:
            logger.error(f"Error updating participant: {e}")
            flash('Error updating participant.', 'error')
            return redirect(url_for('participants'))
    
    participant = get_participant(participant_id)
    if participant:
        return render_template('edit.html', 
                             participant=participant,
                             sessions=get_sessions())
    return redirect(url_for('participants'))

@app.route('/delete/<int:participant_id>')
def delete(participant_id):
    """Delete participant"""
    try:
        if delete_participant(participant_id):
            flash('Participant deleted successfully!', 'success')
        else:
            flash('Error deleting participant.', 'error')
    except Exception as e:
        logger.error(f"Error deleting participant: {e}")
        flash('Error deleting participant.', 'error')
    return redirect(url_for('participants'))

@app.route('/certificate/<int:participant_id>')
def certificate(participant_id):
    """Generate and download certificate"""
    try:
        participant = get_participant(participant_id)
        payment = get_participant_payment(participant_id)
        
        if not participant or not payment or payment['status'] != 'completed':
            flash('Certificate not available. Please ensure payment is completed.', 'error')
            return redirect(url_for('participants'))
        
        session_name = get_session_name(participant['session'])
        certificate_img = generate_certificate(
            participant['name'],
            session_name,
            participant['registration_date']
        )
        
        return send_file(
            certificate_img,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"certificate_{participant['name'].lower().replace(' ', '_')}.png"
        )
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        flash('An error occurred while generating the certificate.', 'error')
        return redirect(url_for('participants'))

if __name__ == '__main__':
    app.run(debug=True)