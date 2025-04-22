from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import qrcode
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

patients = []
medicines = [
    {"id": "11", "name": "พาราเซตามอล"},
    {"id": "12", "name": "ยาแก้ไอ"},
    {"id": "13", "name": "ยาฆ่าเชื้อ"},
]

if not os.path.exists("static/qr_codes"):
    os.makedirs("static/qr_codes")

@app.route('/')
def home():
    return "ระบบจ่ายยาออนไลน์ - ไปที่ <a href='/patient' style='color:#4CAF50;'>/patient</a> หรือ <a href='/doctor' style='color:#4CAF50;'>/doctor</a>"

@app.route('/patient')
def patient_page():
    return render_template('patient.html')

@app.route('/doctor')
def doctor_page():
    return render_template('doctor.html')

@app.route('/submit_patient', methods=['POST'])
def submit_patient():
    data = request.json
    data['status'] = 'waiting'
    data['qr_code'] = ''
    patients.append(data)
    socketio.emit('new_patient', data)
    return jsonify({"success": True})

@app.route('/get_patients')
def get_patients():
    return jsonify(patients)

@app.route('/get_medicines')
def get_medicines():
    return jsonify(medicines)

@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    data = request.json
    new_name = data.get('medicine')
    new_id = data.get('id')  # รับ ID จากผู้ใช้

    # ตรวจสอบว่าชื่อยาและ ID ไม่ซ้ำ
    if new_name and new_id:
        if any(m['name'] == new_name for m in medicines):
            return jsonify({"success": False, "message": "ชื่อยาซ้ำ"})
        if any(m['id'] == new_id for m in medicines):
            return jsonify({"success": False, "message": "ID ซ้ำ"})

        # เพิ่มยาใหม่
        medicines.append({"id": new_id, "name": new_name})
        return jsonify({"success": True, "medicines": medicines})

    return jsonify({"success": False, "message": "กรุณากรอกชื่อยาและ ID"})

@app.route('/delete_medicine', methods=['POST'])
def delete_medicine():
    data = request.json
    med_id = data.get('id')  # รับ ID จากผู้ใช้

    if not med_id:
        return jsonify({"success": False, "message": "กรุณาระบุ ID ของยา"})

    global medicines
    initial_length = len(medicines)
    medicines = [m for m in medicines if m['id'] != med_id]

    if len(medicines) < initial_length:
        return jsonify({"success": True, "message": "ลบยาสำเร็จ"})
    else:
        return jsonify({"success": False, "message": "ไม่พบยาที่ต้องการลบ"})

@app.route('/prescribe', methods=['POST'])
def prescribe():
    data = request.json
    for p in patients:
        if p['name'] == data['name'] and p['status'] == 'waiting':
            medicine = next((m for m in medicines if m['name'] == data['medicine']), None)
            if medicine:
                p['medicine'] = medicine['name']
                p['status'] = 'done'
                qr_data = medicine['id']  # ✅ ใช้เฉพาะ ID ยา
                filename = f"{p['name']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                path = os.path.join("static/qr_codes", filename)
                img = qrcode.make(qr_data)
                img.save(path)
                p['qr_code'] = filename
                socketio.emit('updated_patient', p)
            break
    return jsonify({"success": True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
