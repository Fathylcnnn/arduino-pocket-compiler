import os
import tempfile
import subprocess
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# arduino-cli'nin bu dizinde kurulu olduğu varsayılıyor (Dockerfile'da kurulur)
ARDUINO_CLI = "arduino-cli"

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "Arduino Pocket IDE Derleyici Sunucusu çalışıyor", "version": "1.0.0"})

@app.route('/compile', methods=['POST'])
def compile_sketch():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"success": False, "log": "Hata: Gecersiz JSON istegi"}), 400

        board = req_data.get("board")
        sketch_code = req_data.get("sketch")

        if not board or not sketch_code:
            return jsonify({"success": False, "log": "Hata: 'board' ve 'sketch' parametreleri zorunludur."}), 400

        print(f"[COMPILE] Kart: {board}, Kod boyutu: {len(sketch_code)} karakter")

        with tempfile.TemporaryDirectory() as tmpdir:
            sketch_dir = os.path.join(tmpdir, "Sketch")
            os.makedirs(sketch_dir, exist_ok=True)
            sketch_file = os.path.join(sketch_dir, "Sketch.ino")

            with open(sketch_file, "w", encoding="utf-8") as f:
                f.write(sketch_code)

            output_dir = os.path.join(tmpdir, "build")
            os.makedirs(output_dir, exist_ok=True)

            cmd = [
                ARDUINO_CLI, "compile",
                "--fqbn", board,
                sketch_dir,
                "--output-dir", output_dir,
                "--warnings", "none"
            ]

            print(f"[COMPILE] Komut: {' '.join(cmd)}")

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120  # 2 dakika timeout
            )

            log = process.stdout or ""
            success = (process.returncode == 0)

            print(f"[COMPILE] Sonuc: {'BASARILI' if success else 'BASARISIZ'}, returncode={process.returncode}")

            if success:
                # Öncelikli dosya sırası: .bin (ESP8266/ESP32) > .hex (AVR)
                output_file = None
                preferred_exts = [".bin", ".hex"]

                all_files = os.listdir(output_dir)
                print(f"[COMPILE] Cikti dosyalari: {all_files}")

                for ext in preferred_exts:
                    for fname in all_files:
                        # Bootloader ile birleştirilmiş dosyaları atla
                        if fname.endswith(ext) and "with_bootloader" not in fname:
                            output_file = os.path.join(output_dir, fname)
                            break
                    if output_file:
                        break

                if output_file and os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"[COMPILE] Dosya: {os.path.basename(output_file)}, Boyut: {file_size} byte")
                    with open(output_file, "rb") as f:
                        file_data = f.read()
                    data_base64 = base64.b64encode(file_data).decode("utf-8")
                    return jsonify({
                        "success": True,
                        "data": data_base64,
                        "log": log
                    })
                else:
                    return jsonify({
                        "success": False,
                        "log": log + "\nHata: Derleme basarili oldu fakat cikti dosyasi (.hex/.bin) bulunamadi.\nMevcut dosyalar: " + str(all_files)
                    })
            else:
                return jsonify({
                    "success": False,
                    "log": log
                })

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "log": "Hata: Derleme 120 saniye icerisinde tamamlanamadi (timeout)."}), 500
    except Exception as e:
        import traceback
        print(f"[HATA] {traceback.format_exc()}")
        return jsonify({"success": False, "log": f"Sunucu ic hatasi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Arduino Pocket IDE Derleme Sunucusu baslatiliyor (port={port})...")
    app.run(host='0.0.0.0', port=port, debug=False)
