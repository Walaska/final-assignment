import os
import pymongo
from flask import Flask, request, jsonify, send_file
from gridfs import GridFS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

client = pymongo.MongoClient(os.getenv('MONGO_DB_URI'))
db = client['file_sharing_db']
files_col = db['files']
fs = GridFS(db)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_file = {
            'filename': filename,
            'filepath': filepath,
            'uploader': request.form.get('uploader')
        }
        result = files_col.insert_one(new_file)
        fs.put(file, filename=filename)
        return jsonify({'message': 'File uploaded successfully', 'file_id': str(result.inserted_id)}), 201
    else:
        return jsonify({'message': 'Invalid file type'}), 400


@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    file = files_col.find_one({'_id': pymongo.ObjectId(file_id)})
    if not file:
        return jsonify({'message': 'File not found'}), 404

    return send_file(file['filepath'], attachment_filename=file['filename'])


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8001)
