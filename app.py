# -*- coding: utf-8 -*-
"""
    typademic
    ~~~~~
    Academic publishing.
    :copyright: (c) 2018 by Moritz Mähr.
    :license: MIT, see LICENSE.md for more details.
"""
import os
import uuid

from flask import Flask, session, render_template, request, send_file, redirect, url_for, send_from_directory
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError
from sh import pandoc

basedir = os.path.abspath(os.path.dirname(__file__))
google_analytics = os.getenv('GOOGLE_ANALYTICS', 'UA-XXXXXXXXX-X')

app = Flask(__name__)

app.config.update(
    # Secret key used to generate CSRF token should not be set at random while in production. It breaks sessions.
    SECRET_KEY=os.getenv('SECRET_KEY', uuid.uuid4().hex),
    UPLOADED_PATH=os.path.join(basedir, 'uploads'),
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.md, .png, .jpg, .jpeg, .bib, .bibtex, .biblatex, .csl, .yaml, .yml, .json, .tex',
    DROPZONE_MAX_FILE_SIZE=10,
    DROPZONE_MAX_FILES=30,
    DROPZONE_ENABLE_CSRF=True,
    DROPZONE_DEFAULT_MESSAGE='<i class="fas fa-file-upload fa-2x"></i> Upload your files (Text, Images, Bibliography, Style etc.)'
)

dropzone = Dropzone(app)
csrf = CSRFProtect(app)


def clean_old_files():
    # TODO implement cleaning "worker"
    return None


def uploaded_files():
    try:
        return os.listdir(os.path.join(app.config['UPLOADED_PATH'], session['uid']))
    except Exception as e:
        return []


@app.route('/', methods=['POST', 'GET'])
def upload():
    clean_old_files()
    error = ''
    if 'uid' not in session:
        uid = uuid.uuid4().hex
        session['uid'] = uid
        session_upload_path = os.path.join(app.config['UPLOADED_PATH'], uid)
        os.mkdir(session_upload_path)

    if request.method == 'POST':
        f = request.files.get('file')
        f.save(os.path.join(app.config['UPLOADED_PATH'], session['uid'], f.filename))
    files = uploaded_files()

    return render_template('index.html', google_analytics=google_analytics, files=files, error=error)


@app.route('/clear', methods=['GET'])
def clear():
    try:
        for root, dirs, files in os.walk(os.path.join(app.config['UPLOADED_PATH'], session['uid']), topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.remove(os.path.join(root, name))
        # for f in os.path.join(app.config['UPLOADED_PATH'], session['uid']):
        #     os.remove(f)
        return redirect(url_for('upload'))
    except Exception as e:
        return render_template('index.html', google_analytics=google_analytics, files=uploaded_files(), error=str(e))


@app.route('/docx', methods=['GET'])
def docx():
    files = uploaded_files()
    md_files = ''
    try:
        for file in files:
            # Serve from cache
            if file.endswith('typademic.docx'):
                return send_file(os.path.join(app.config['UPLOADED_PATH'], session['uid'], 'typademic.docx'),
                                 attachment_filename='typademic.docx')
            if file.endswith('.md'):
                md_files = md_files + ' ' + file
        cwd = os.path.join(app.config['UPLOADED_PATH'], session['uid'])
        if md_files == '':
            return render_template('index.html', google_analytics=google_analytics, files=files, error='No Markdown file was uploaded. Please reset and try again.')
        pandoc(md_files.strip(),
               '--output',
               'typademic.docx',
               '--from',
               'markdown+ascii_identifiers+tex_math_single_backslash+raw_tex+table_captions+yaml_metadata_block+autolink_bare_uris',
               '--latex-engine=xelatex',
               '--filter',
               'pandoc-citeproc',
               '--standalone',
               _cwd=cwd)
        return send_file(os.path.join(app.config['UPLOADED_PATH'], session['uid'], 'typademic.docx'),
                         attachment_filename='typademic.docx')
    except Exception as e:
        return render_template('index.html', google_analytics=google_analytics, files=files, error=str(e))


@app.route('/pdf', methods=['GET'])
def pdf():
    files = uploaded_files()
    md_files = ''
    try:
        for file in files:
            # Serve from cache
            if file.endswith('typademic.pdf'):
                return send_file(os.path.join(app.config['UPLOADED_PATH'], session['uid'], 'typademic.pdf'),
                                 attachment_filename='typademic.pdf')
            if file.endswith('.md'):
                md_files = md_files + ' ' + file
        cwd = os.path.join(app.config['UPLOADED_PATH'], session['uid'])
        if md_files == '':
            return render_template('index.html', google_analytics=google_analytics, files=files, error='No Markdown file was uploaded. Please reset and try again.')
        pandoc(md_files.strip(),
               '--output',
               'typademic.pdf',
               '--from',
               'markdown+ascii_identifiers+tex_math_single_backslash+raw_tex+table_captions+yaml_metadata_block+autolink_bare_uris',
               '--latex-engine=xelatex',
               '--filter',
               'pandoc-citeproc',
               '--standalone',
               _cwd=cwd)
        return send_file(os.path.join(app.config['UPLOADED_PATH'], session['uid'], 'typademic.pdf'),
                         attachment_filename='typademic.pdf')
    except Exception as e:
        return render_template('index.html', google_analytics=google_analytics, files=files, error=str(e))


# handle CSRF error
@app.errorhandler(CSRFError)
def csrf_error(e):
    return e.description, 400


if __name__ == '__main__':
    app.run(debug=False, host=os.getenv('HOST', '0.0.0.0'), port=5000)
