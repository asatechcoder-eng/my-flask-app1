from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
import time
import random
import math
import io
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# ------------------------------
# GLOBAL CONTEXT
# ------------------------------
@app.context_processor
def inject_now():
    """Inject current datetime object for {{ now.year }} usage"""
    return {'now': datetime.utcnow()}


# ------------------------------
# CONFIG
# ------------------------------
COLUMNS = [
    "UID", "Timestamp", "Center Name", "Child Name", "Adjustment Amount",
    "Note/Description", "Pulling Instruction", "Pulling Category", "Start Date",
    "End Date", "Adjustment is Recurring", "Child Status", "Family Status", "Billing Cycle"
]


# ------------------------------
# HELPERS
# ------------------------------
def gen_uid(full_df):
    """Generate a unique 4-digit UID."""
    existing = set()
    if 'UID' in full_df.columns:
        existing = set(full_df['UID'].astype(str).tolist())
    while True:
        uid = str(random.randint(1, 1000000))
        if uid not in existing:
            return uid


def as_str(x):
    if pd.isna(x) or (isinstance(x, float) and math.isnan(x)):
        return ""
    return str(x)


def load_data():
    """Load or create data.csv"""
    if not os.path.exists('data.csv'):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv('data.csv', index=False)
    return pd.read_csv('data.csv', dtype=str).fillna("")


def load_center_children_details():
    """Load center_students.csv to map centers and children"""
    if not os.path.exists('center_students.csv'):
        return {}, {}

    df = pd.read_csv('center_students.csv', dtype=str).fillna("")
    details = {}
    center_children = {}
    for _, row in df.iterrows():
        center = as_str(row.get('Center', ""))
        child = as_str(row.get('Child', ""))
        if not center or not child:
            continue
        key = f"{center}|||{child}"
        details[key] = {
            "Child Status": as_str(row.get('Child Status', "")),
            "Family Status": as_str(row.get('Family Status', "")),
            "Billing Cycle": as_str(row.get('Billing Cycle', ""))
        }
        center_children.setdefault(center, []).append(child)
    return center_children, details


# ------------------------------
# ROUTES
# ------------------------------
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    password = request.form['password']

    if not os.path.exists('center_admins.csv'):
        return "Admin file missing."

    df = pd.read_csv('center_admins.csv', dtype=str).fillna("")
    row = df[(df['Username'] == user_id) & (df['Password'] == password)]

    if not row.empty:
        session['user_id'] = user_id
        center_name = row.iloc[0]['Center Name']
        session['center'] = center_name
        session['is_admin'] = (center_name.strip().upper() == "ALL")
        return redirect('/data')

    return 'Invalid credentials. <a href="/">Try again</a>'


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    msg = ''
    centers = []
    username = password = None
    try:
        df = pd.read_csv('center_admins.csv', dtype=str).fillna("")
        centers = sorted(df['Center Name'].unique())
        if request.method == 'POST':
            center = request.form.get('center')
            row = df[df['Center Name'] == center]
            if not row.empty:
                username = row.iloc[0]['Username']
                password = row.iloc[0]['Password']
            else:
                msg = 'Center not found.'
    except Exception:
        msg = 'Error loading centers.'
    return render_template('forgot_password.html',
                           centers=centers,
                           password=password,
                           username=username,
                           msg=msg)


@app.route('/data', methods=['GET', 'POST'])
def data_table():
    if 'user_id' not in session or 'center' not in session:
        return redirect('/')

    center = session['center']
    msg = ''
    full_df = load_data()
    center_children, details = load_center_children_details()

    # --- Default filter ---
    selected_center = None

    # If admin filters by center
    if session.get('is_admin') and request.method == 'POST' and 'selected_center' in request.form:
        selected_center = request.form.get('selected_center').strip()
        if selected_center:
            df = full_df[full_df['Center Name'] == selected_center].reset_index(drop=True)
        else:
            df = full_df.copy()  # show all
    elif session.get('is_admin'):
        df = full_df.copy()
    else:
        df = full_df[full_df['Center Name'] == center].reset_index(drop=True)

    mode = None
    edit_idx = None
    row_data = {}

    def fill_auto_fields(rd):
        key = f"{rd.get('Center Name','')}|||{rd.get('Child Name','')}"
        if key in details:
            rd.update(details[key])
        else:
            rd.update({"Child Status": "", "Family Status": "", "Billing Cycle": ""})
        return rd

    if request.method == 'POST' and not ('selected_center' in request.form):
        # Add Row
        if 'add_row_mode' in request.form:
            mode = 'add'
            row_data = {col: '' for col in COLUMNS}
            row_data['UID'] = gen_uid(full_df)
            row_data['Timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            row_data['Center Name'] = selected_center or center
            if (selected_center or center) in center_children:
                row_data['Child Name'] = center_children[selected_center or center][0]
            row_data = fill_auto_fields(row_data)

        # Edit
        elif 'edit_row_idx' in request.form:
            edit_idx = int(request.form['edit_row_idx'])
            if 0 <= edit_idx < len(df):
                row_data = df.iloc[edit_idx].to_dict()
                mode = 'edit'
            else:
                msg = 'Row not found.'

        # Delete
        elif 'delete_row_idx' in request.form:
            idx = int(request.form['delete_row_idx'])
            if 0 <= idx < len(df):
                df = df.drop(idx).reset_index(drop=True)
                if session.get('is_admin'):
                    if selected_center:
                        # Replace only that center’s data
                        other_df = full_df[full_df['Center Name'] != selected_center]
                        full_df = pd.concat([other_df, df], ignore_index=True)
                        full_df.to_csv('data.csv', index=False)
                    else:
                        df.to_csv('data.csv', index=False)
                else:
                    full_df = pd.concat([full_df[full_df['Center Name'] != center], df], ignore_index=True)
                    full_df.to_csv('data.csv', index=False)
                msg = 'Row deleted successfully.'
            else:
                msg = 'Row not found.'

        # Save Add
        elif 'save_add' in request.form:
            new_row = {col: request.form.get(col, "") for col in COLUMNS}
            new_row['UID'] = gen_uid(full_df)
            new_row['Timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            new_row = fill_auto_fields(new_row)
            full_df = pd.concat([full_df, pd.DataFrame([new_row])], ignore_index=True)
            full_df.to_csv('data.csv', index=False)
            msg = 'Row added successfully.'
            df = full_df if session.get('is_admin') else full_df[full_df['Center Name'] == center]

        # Save Edit
        elif 'save_edit' in request.form:
            idx = int(request.form['row_idx'])
            if 0 <= idx < len(df):
                for col in COLUMNS:
                    if col in ['UID', 'Timestamp']:
                        continue
                    df.at[idx, col] = request.form.get(col, "")
                df.at[idx, 'Timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                df = df.reset_index(drop=True)
                if session.get('is_admin'):
                    if selected_center:
                        other_df = full_df[full_df['Center Name'] != selected_center]
                        full_df = pd.concat([other_df, df], ignore_index=True)
                    else:
                        full_df = df.copy()
                    full_df.to_csv('data.csv', index=False)
                else:
                    full_df = pd.concat([full_df[full_df['Center Name'] != center], df], ignore_index=True)
                    full_df.to_csv('data.csv', index=False)
                msg = 'Row edited successfully.'
            else:
                msg = 'Row not found.'

        elif 'cancel_action' in request.form:
            mode = None

    return render_template(
        'datatable.html',
        data=df,
        columns=COLUMNS,
        msg=msg,
        mode=mode,
        edit_idx=edit_idx,
        row_data=row_data,
        centers=sorted(full_df['Center Name'].unique()),
        center_children=center_children,
        child_details=details,
        center_of_admin=selected_center or center
    )

@app.route('/download_excel')
def download_excel():
    if 'user_id' not in session or 'center' not in session:
        return redirect('/')

    center = session['center']
    df = load_data()

    if session.get('is_admin'):
        df_export = df.copy()
        filename = f"AllCenters_data_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
    else:
        df_export = df[df['Center Name'] == center]
        filename = f"{center}_data_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"

    if df_export.empty:
        return "No data available."

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Data')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


if __name__ == '__main__':
    app.run(debug=True)
