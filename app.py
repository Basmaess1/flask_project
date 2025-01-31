from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import csv
from datetime import datetime
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for flash messages

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# CSV file paths
PARTICIPANTS_CSV = 'data/participants.csv'
SESSIONS_CSV = 'data/sessions.csv'
PAYMENTS_CSV = 'data/payments.csv'

# Initialize CSV files if they don't exist
def init_csv_files():
    if not os.path.exists(PARTICIPANTS_CSV):
        with open(PARTICIPANTS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'email', 'session', 'registration_date'])
    
    if not os.path.exists(SESSIONS_CSV):
        with open(SESSIONS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'date', 'capacity', 'price'])
            # Add some sample sessions with prices
            writer.writerows([
                ['1', 'Web Development Basics', '2024-04-01', '30', '99.99'],
                ['2', 'Python for Beginners', '2024-04-02', '25', '79.99'],
                ['3', 'Data Science Introduction', '2024-04-03', '20', '149.99']
            ])
    
    if not os.path.exists(PAYMENTS_CSV):
        with open(PAYMENTS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'participant_id', 'amount', 'payment_date', 'status'])

init_csv_files()

def get_sessions():
    sessions = []
    with open(SESSIONS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        sessions = list(reader)
    return sessions

def get_session_name(session_id):
    sessions = get_sessions()
    for session in sessions:
        if session['id'] == session_id:
            return session['name']
    return ''

def get_session_price(session_id):
    sessions = get_sessions()
    for session in sessions:
        if session['id'] == session_id:
            return float(session['price'])
    return 0.0

def add_participant(name, email, session):
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

def update_participant(participant_id, name, email, session):
    participants = get_participants()
    updated_participants = []
    found = False
    
    for participant in participants:
        if participant['id'] == str(participant_id):
            participant['name'] = name
            participant['email'] = email
            participant['session'] = session
            found = True
        updated_participants.append(participant)
    
    if found:
        with open(PARTICIPANTS_CSV, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'session', 'registration_date'])
            writer.writeheader()
            writer.writerows(updated_participants)
        return True
    return False

def delete_participant(participant_id):
    participants = get_participants()
    remaining_participants = [p for p in participants if p['id'] != str(participant_id)]
    
    with open(PARTICIPANTS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'email', 'session', 'registration_date'])
        writer.writeheader()
        writer.writerows(remaining_participants)
    
    # Also delete associated payment
    payments = get_payments()
    remaining_payments = [p for p in payments if p['participant_id'] != str(participant_id)]
    
    with open(PAYMENTS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'participant_id', 'amount', 'payment_date', 'status'])
        writer.writeheader()
        writer.writerows(remaining_payments)

def add_payment(participant_id, amount):
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

def get_participants():
    participants = []
    with open(PARTICIPANTS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        participants = list(reader)
    return participants

def get_payments():
    payments = []
    if os.path.exists(PAYMENTS_CSV):
        with open(PAYMENTS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            payments = list(reader)
    return payments

def get_participant(participant_id):
    participants = get_participants()
    for participant in participants:
        if participant['id'] == str(participant_id):
            return participant
    return None

def get_participant_payment(participant_id):
    payments = get_payments()
    for payment in payments:
        if payment['participant_id'] == str(participant_id):
            return payment
    return None

def generate_certificate(name, session_name, date):
    # Create a new image with a white background
    width = 1000
    height = 700
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw border
    draw.rectangle([(40, 40), (width-40, height-40)], outline='#4F46E5', width=3)
    draw.rectangle([(50, 50), (width-50, height-50)], outline='#4F46E5', width=1)
    
    # Add text
    # Note: In a production environment, you should have proper font files
    # For this example, we'll use basic text
    draw.text((width/2, 150), 'Certificate of Completion', fill='#1F2937', anchor='mm', font=ImageFont.load_default())
    draw.text((width/2, 250), 'This certifies that', fill='#4B5563', anchor='mm', font=ImageFont.load_default())
    draw.text((width/2, 300), name, fill='#1F2937', anchor='mm', font=ImageFont.load_default())
    draw.text((width/2, 350), 'has successfully completed', fill='#4B5563', anchor='mm', font=ImageFont.load_default())
    draw.text((width/2, 400), session_name, fill='#1F2937', anchor='mm', font=ImageFont.load_default())
    draw.text((width/2, 500), f'Date: {date}', fill='#4B5563', anchor='mm', font=ImageFont.load_default())
    
    # Save to BytesIO object
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/')
def index():
    sessions = get_sessions()
    return render_template('index.html', sessions=sessions)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    session = request.form.get('session')
    
    if name and email and session:
        participant_id = add_participant(name, email, session)
        session_price = get_session_price(session)
        add_payment(participant_id, session_price)
        return redirect(url_for('success', participant_id=participant_id))
    
    return redirect(url_for('index'))

@app.route('/success/<int:participant_id>')
def success(participant_id):
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
    all_participants = get_participants()
    # Add payment information to each participant
    for participant in all_participants:
        payment = get_participant_payment(participant['id'])
        participant['payment'] = payment
        participant['session_name'] = get_session_name(participant['session'])
    return render_template('participants.html', participants=all_participants, sessions=get_sessions())

@app.route('/edit/<int:participant_id>', methods=['GET', 'POST'])
def edit_participant(participant_id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        session = request.form.get('session')
        
        if name and email and session:
            if update_participant(participant_id, name, email, session):
                flash('Participant updated successfully!', 'success')
                return redirect(url_for('participants'))
            else:
                flash('Participant not found!', 'error')
        else:
            flash('All fields are required!', 'error')
    
    participant = get_participant(participant_id)
    if participant:
        return render_template('edit.html', participant=participant, sessions=get_sessions())
    return redirect(url_for('participants'))

@app.route('/delete/<int:participant_id>')
def delete(participant_id):
    delete_participant(participant_id)
    flash('Participant deleted successfully!', 'success')
    return redirect(url_for('participants'))

@app.route('/certificate/<int:participant_id>')
def certificate(participant_id):
    participant = get_participant(participant_id)
    payment = get_participant_payment(participant_id)
    
    if participant and payment and payment['status'] == 'completed':
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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)