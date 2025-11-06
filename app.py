from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import pandas as pd
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import io
from typing import Optional, List, Dict

from utils.pdf_processor import PDFProcessor
from utils.clustering import CustomerClustering
from utils.analysis import SalesAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'data/uploaded'
app.config['PROCESSED_FOLDER'] = 'data/processed'
app.config['DB_PATH'] = 'data/data_history.db'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'csv'}

# Global variables
data_history: List[Dict] = []
current_dataset_index = -1


# ================== Database ==================
def init_db():
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    upload_time TEXT,
                    data_path TEXT
                )''')
    conn.commit()
    conn.close()


def save_to_db(filename, upload_time, data_path):
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()
    c.execute("INSERT INTO datasets (filename, upload_time, data_path) VALUES (?, ?, ?)",
              (filename, upload_time, data_path))
    conn.commit()
    conn.close()


def load_from_db():
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()
    c.execute("SELECT filename, upload_time, data_path FROM datasets")
    rows = c.fetchall()
    conn.close()
    return rows


def clear_db():
    conn = sqlite3.connect(app.config['DB_PATH'])
    c = conn.cursor()
    c.execute("DELETE FROM datasets")
    conn.commit()
    conn.close()


# ================== Helper Functions ==================
def allowed_file(filename: Optional[str]) -> bool:
    return bool(filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


def get_current_data():
    global data_history, current_dataset_index
    if 0 <= current_dataset_index < len(data_history):
        return data_history[current_dataset_index]
    return None


def load_all_data():
    """Muat dataset dari SQLite dan langsung jalankan ulang analisis ML"""
    global data_history, current_dataset_index
    rows = load_from_db()
    if not rows:
        print("[INFO] Tidak ada data di database.")
        return

    analyzer = SalesAnalyzer()
    cluster = CustomerClustering()

    for filename, upload_time, data_path in rows:
        if os.path.exists(data_path):
            try:
                df = pd.read_csv(data_path)
                analysis_results = analyzer.analyze_sales(df)
                clustering_results = cluster.perform_analysis(df)

                data_history.append({
                    'data': df,
                    'filename': filename,
                    'upload_time': datetime.strptime(upload_time, "%Y-%m-%d %H:%M:%S"),
                    'analysis_results': analysis_results,
                    'clustering_results': clustering_results
                })
            except Exception as e:
                print(f"[WARNING] Gagal memproses ulang dataset {filename}: {e}")

    if data_history:
        current_dataset_index = len(data_history) - 1
        print(f"[INFO] {len(data_history)} dataset berhasil dimuat ulang dan dianalisis.")
    else:
        print("[INFO] Tidak ada dataset valid ditemukan.")


# ================== Routes ==================
@app.route('/')
def index():
    return redirect(url_for('upload_file'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global data_history, current_dataset_index

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename:
            flash('Tidak ada file yang dipilih.', 'error')
            return redirect(request.url)

        if allowed_file(file.filename):
            filename = secure_filename(file.filename or "")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Proses file
                if filename.lower().endswith('.pdf'):
                    processor = PDFProcessor()
                    csv_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    csv_path = os.path.join(app.config['PROCESSED_FOLDER'], csv_filename)
                    df = processor.pdf_to_csv(filepath, csv_path)
                    if df.empty:
                        flash('Tidak ada data berhasil diekstrak dari PDF.', 'warning')
                        return redirect(request.url)
                    flash(f'Berhasil mengekstrak {len(df)} produk dari PDF', 'success')
                else:
                    df = pd.read_csv(filepath)
                    csv_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{filename}")
                    df.to_csv(csv_path, index=False)
                    flash(f'Berhasil memuat {len(df)} data dari CSV', 'success')

                # Simpan dataset ke memori & DB
                dataset_info = {
                    'data': df,
                    'filename': filename,
                    'upload_time': datetime.now(),
                    'clustering_results': None,
                    'analysis_results': None
                }
                data_history.append(dataset_info)
                current_dataset_index = len(data_history) - 1

                save_to_db(filename, dataset_info['upload_time'].strftime("%Y-%m-%d %H:%M:%S"), csv_path)

                # Jalankan analisis
                analyzer = SalesAnalyzer()
                analysis_results = analyzer.analyze_sales(df)
                clustering = CustomerClustering()
                clustering_results = clustering.perform_analysis(df)
                data_history[current_dataset_index]['analysis_results'] = analysis_results
                data_history[current_dataset_index]['clustering_results'] = clustering_results

                flash('Analisis data berhasil diselesaikan!', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                flash(f'Error memproses file: {str(e)}', 'error')
                return redirect(request.url)

        else:
            flash('Format file tidak didukung. Harus PDF atau CSV.', 'error')

    return render_template('upload.html')


@app.route('/dashboard')
def dashboard():
    current_data = get_current_data()
    if current_data is None:
        flash('Belum ada data diupload.', 'warning')
        return redirect(url_for('upload_file'))

    data_history_with_index = [{'index': i, 'data': d} for i, d in enumerate(data_history)]

    # Ambil analisis menu favorit
    favorite_menus = current_data['analysis_results'].get('favorite_menus', {}) if current_data['analysis_results'] else {}

    return render_template(
        'dashboard.html',
        data=current_data['data'],
        clustering_results=current_data['clustering_results'],
        analysis_results=current_data['analysis_results'],
        favorite_menus=favorite_menus,  # TAMBAHAN BARU
        data_history=data_history,
        data_history_with_index=data_history_with_index,
        current_dataset_index=current_dataset_index,
        total_products=len(current_data['data'])
    )


@app.route('/select_dataset/<int:dataset_index>')
def select_dataset(dataset_index):
    global current_dataset_index
    if 0 <= dataset_index < len(data_history):
        current_dataset_index = dataset_index
        flash(f"Berpindah ke dataset: {data_history[dataset_index]['filename']}", 'info')
    return redirect(url_for('dashboard'))


@app.route('/combined_data')
def combined_data():
    global data_history, current_dataset_index
    if len(data_history) < 2:
        flash("Minimal dua dataset diperlukan untuk digabung.", "warning")
        return redirect(url_for('dashboard'))

    combined_df = pd.concat([d['data'] for d in data_history], ignore_index=True)
    flash(f'Berhasil menggabungkan {len(data_history)} dataset ({len(combined_df)} baris total)', 'success')

    analyzer = SalesAnalyzer()
    analysis_results = analyzer.analyze_sales(combined_df)
    clustering = CustomerClustering()
    clustering_results = clustering.perform_analysis(combined_df)

    dataset_info = {
        'data': combined_df,
        'filename': f'Gabungan_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'upload_time': datetime.now(),
        'analysis_results': analysis_results,
        'clustering_results': clustering_results
    }

    data_history.append(dataset_info)
    current_dataset_index = len(data_history) - 1

    csv_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{dataset_info['filename']}.csv")
    combined_df.to_csv(csv_path, index=False)
    save_to_db(dataset_info['filename'], dataset_info['upload_time'].strftime("%Y-%m-%d %H:%M:%S"), csv_path)

    return redirect(url_for('dashboard'))


@app.route('/export-results')
def export_results():
    current_data = get_current_data()
    if current_data is None:
        flash('Belum ada data yang diupload.', 'error')
        return redirect(url_for('dashboard'))

    export_df = current_data['data'].copy()
    output = io.StringIO()
    export_df.to_csv(output, index=False)
    output.seek(0)

    filename = f'analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@app.route('/clear-all-data', methods=['POST'])
def clear_all_data():
    global data_history, current_dataset_index
    data_history.clear()
    current_dataset_index = -1
    clear_db()
    flash('Semua data berhasil dihapus.', 'success')
    return redirect(url_for('upload_file'))


@app.route('/clear-current-data', methods=['POST'])
def clear_current_data():
    global data_history, current_dataset_index
    if 0 <= current_dataset_index < len(data_history):
        removed = data_history.pop(current_dataset_index)
        flash(f"Data '{removed['filename']}' berhasil dihapus.", 'success')
        current_dataset_index -= 1
        if current_dataset_index < 0 and data_history:
            current_dataset_index = 0
    else:
        flash('Tidak ada dataset aktif untuk dihapus.', 'warning')
    return redirect(url_for('dashboard'))


# ================== Main ==================
if __name__ == '__main__':
    init_db()
    load_all_data()
    app.run(debug=True, port=5000, use_reloader=False)