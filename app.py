import os
import uuid
from flask import Flask, url_for, request, flash, redirect, Response, jsonify, render_template
from StoppableThread import StoppableThread
from multiprocessing import Pool


app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'py'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Somehow this function must be defined before defining the pool  (´･_･`)
def execute_file(file_id):
  # print("Running on process: %d\n\n" % os.getpid())
  command = 'python3 ./uploads/'+ file_id + '.py > ./outputs/' + file_id + '.txt'
  # print("Executing command: ", command)
  os.system(command)


threads = {}
THRESHOLD = 2
pool = Pool(processes=THRESHOLD)

def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def main_page():
  error = request.args.get('error')


  return render_template('upload.html', error=error)


@app.route('/upload', methods=['POST'])
def upload_file():
  # check if the post request has the file part
  if 'file' not in request.files:
      return redirect('/?error=NO_FILE_ERROR')
  file = request.files['file']
  if not file or file.filename == '': 
    return redirect('/?error=NO_FILE_ERROR')
  if not allowed_file(file.filename):
    return redirect('/?error=INCORRECT_FILE_TYPE_ERROR')
  if not can_add_more_file():
    return redirect('/?error=NO_AVAILABLE_WORKER')

  file_id = uuid.uuid4().hex
  file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_id+'.py'))

  new_thread = pool.apply_async(execute_file, args=(file_id,))

  threads[file_id] = new_thread

  return redirect('/status/'+ file_id)


@app.route('/status/<id>', methods=["GET"])
def get_status(id):
  if id in threads:
    print('Thread %s is ready?:' %(id), threads[id].ready())
    if threads[id].ready():
      print("Result: ", threads[id].get())
      print('Thread %s is successful?:' %(id), threads[id].successful())
      del threads[id]
      return redirect('/result/'+id)
  else: 
    file_path = './outputs/' + id + '.txt'
    if os.path.exists(file_path):
      return redirect('/result/' + id)
    else: 
      return "There is no running file with that id", 404

  

  return render_template('status.html', id=id)

@app.route('/result/<id>', methods=['GET'])
def get_result(id):
  file_path = './outputs/' + id + '.txt'
  if os.path.exists(file_path):
    with open(file_path, 'r') as f:
      content = f.readlines()
    return render_template('result.html', content=content, id=id)
  return "Cannot find the result", 404

@app.route('/running', methods=['GET'])
def get_running_threads():
  return jsonify(list(threads.keys())), 200

def can_add_more_file():
  alive_count = 0
  for thread in threads.values():
    if not thread.ready():
      alive_count += 1
    if alive_count >= THRESHOLD:
      return False
  return True