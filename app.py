from flask import Flask, render_template, request, jsonify
from sms_api import SendSms
import threading
import time

app = Flask(__name__)

# Döngüyü durdurabilmek için bir Event bayrağı
stop_event = threading.Event()
active_thread = None

def sms_worker(tel_no, kere, aralik):
    stop_event.clear()
    sms = SendSms(tel_no, "")
    adet = 0
    
    while not stop_event.is_set():
        if kere is not None and adet >= kere:
            break
            
        for attribute in dir(SendSms):
            if stop_event.is_set():
                break
            attribute_value = getattr(SendSms, attribute)
            if callable(attribute_value) and not attribute.startswith('__'):
                if kere is not None and adet >= kere:
                    break
                try:
                    # Metodu çağırıyoruz
                    getattr(sms, attribute)()
                    adet += 1
                    time.sleep(aralik)
                except Exception as e:
                    print(f"Hata oluştu: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global active_thread
    data = request.json
    tel_no = data.get('tel_no')
    kere = data.get('kere') # int veya None
    aralik = int(data.get('aralik', 1))
    
    if not tel_no or len(tel_no) != 10:
        return jsonify({"status": "error", "message": "Geçersiz numara!"}), 400
        
    if kere:
        kere = int(kere)
    else:
        kere = None

    if active_thread and active_thread.is_alive():
        return jsonify({"status": "error", "message": "Zaten çalışan bir işlem var!"}), 400

    active_thread = threading.Thread(target=sms_worker, args=(tel_no, kere, aralik))
    active_thread.daemon = True
    active_thread.start()
    
    return jsonify({"status": "success", "message": "Gönderim başlatıldı."})

@app.route('/stop', methods=['POST'])
def stop():
    stop_event.set()
    return jsonify({"status": "success", "message": "Durdurma sinyali gönderildi."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
