from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import pandas as pd
import os
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # IMPORTANT: Change this in production!

# Hardcoded user for now
USERS = {
    "salish": "salish@123"
}

# Directory to store generated Excel files
UPLOAD_FOLDER = 'generated_excel_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Placeholder for company logos (base64 encoded as requested)
# In a real app, you'd serve these from a static folder
COMPANY_LOGOS = {
    "IOC": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFwAAABcCAMAAADUMSJqAAAAdVBMVEX///8xOG8cJWa6u8mztsYkLWkfKGcvNm6Rk6urrb4tNG0pMWsnL2qlp7oQHGIAE18VIGUADl75+fo9Q3bh4ujZ2uHr6+90d5idn7RjZ41TWYM1PHHCxNAHF2CGi6ZZXofP0NlESntsb5NJUH58gJ4AAFYACF22DV/IAAAEFElEQVRoge2ZW7uqIBCGBQMMzAhPZZotc63//xO3iKLlMWNf7Gev7ypRXnGaGWCwrLWKdvEXAF/lPlrdZTU6hpARAAiDMDaM33FUkZUI4juT7HMGnpSdzbH3HniRtzfFDo6KiKvxZ1j9PgWG4BcmcQwdIiGiPVJXFzPskNe0RKhLkdR0HhqBO0i6CBDttQDScdDNCNyXLGh3Dan8FOKbYAv5dxIuek1Qvu4oJrusVyThNOk3JVTCTfhLJAOI5v2mXMIzE0lAnKRZrv2mqzGzWKxG9TyvDirCTLCt0n0Jmjqo3NgIPIUyaKDOVWd1nRqBK0cHTRqvEru8okbcvFKqEi47JbdbcqqDHxwNDdyy4iYVUtelTYI0Y/FaF/ycznG+3Ge94ox0aJIVJtmWZV95YxGAqNEpVOFzRUc3I6H5IuXvT8nXnOwGbt4oxuGH/FH2kvbQLEH5yA+b0CLhlCJ8c1rFKjZZoVswopQnW/7fmwocpMUaV2S6RQXUlpn6JSinhd9ni+Na+JYp6W+O3HJq5yBYy21grm5Red7ZALeKjDHMDvtWpaK7ZdtwqG4zb2MSs+PC6a0f7IGfR04RG0oG/1D4/8J/4b/w/wUeLeygPoLvrvPz1UfwAiez91fC72MGiBhAs6WIdfD799j0IXf0sxuGVfAUjlYc6gUVn1nhrIHbR0LASLtap/Dp6tUKuO1VC4KfoV/UdY5K2WT1ahm+rwc4skMt22VJNrUJXIQfVJ1taHTht1se4E3Ql+BOU8OjA48OuV6ekYny1QLc0fVB9OrpDtJwBPlonWYefutGx+8v9zqrICcdTzKz8PiHdqN7WT0GR9ou7tGUM87Cw3Oi6a9Gd2h+ULVJQOBExXDB5qKzS/bs6VF1Gbb/9tcmeDM2QDHz7sPbRWuY8QwzD1fLeVlSsi9j6SVonWl8PT8L37V9s8rTojHDOu1WhY/R5+B2a/CZvd21LXzw8i24Lt7Tmdnsriv8+DEIpEm4iKGOn3nqlKMfo4PkOwVPgY7uhc1X3ibH6kn/ecIahwcXqItIaKE6Ja5dGBPuH0Y2XD24SPOM6eepv7TdDXBHr6IVFXbbYwC/33zef3g83z0p5L1amTx0Ovq3XViFcLdVFCJInfzIEe0/idYcNNxhv4/8XAQzDJJEvZQmue96EL08RLJ1hxghYmAgQon+RYe3GV17QBL5aNh9VshfX6oXF7gM7Ale3iqLnLORb58Q9d4tdIU+JstcKexvOI86Q3eZDFy87YQxKH7Y/OiJe9p+8hrEcKYaRTCMPzosChzM3bHhE+Yx5/NzqLS8QuzS7g2Euphfy/vHZKXwUD7gyZOBy7wTfJR7MweWWiIKq9UDK2QO+xsKT2BqxWRAl/kt2WcKv02da4/pvernH6G1NCzWycwRAAAAAElFTkSuQmCC",
    "BPCL": "https://upload.wikimedia.org/wikipedia/en/thumb/8/8c/Bharat_Petroleum_Logo.svg/1200px-Bharat_Petroleum_Logo.svg.png", # Example URL, replace with actual
    "HPCL": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/Hindustan_Petroleum_Logo.svg/1200px-Hindustan_Petroleum_Logo.svg.png" # Example URL, replace with actual
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('company_selection'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['logged_in']:
            return f(*args, **kwargs)
        else:
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))
    return wrap

@app.route('/company_selection')
@login_required
def company_selection():
    return render_template('company_selection.html', logos=COMPANY_LOGOS)

@app.route('/<company_name>_form', methods=['GET', 'POST'])
@login_required
def company_form(company_name):
    company_name = company_name.upper()
    if company_name not in ["IOC", "BPCL", "HPCL"]:
        flash("Invalid company selected.", 'danger')
        return redirect(url_for('company_selection'))

    if request.method == 'POST':
        # Process form data
        form_data = request.form.to_dict()
        file_path = process_and_generate_excel(company_name, form_data)
        if file_path:
            flash(f"Excel file generated for {company_name}!", 'success')
            return render_template('output_options.html', file_name=os.path.basename(file_path))
        else:
            flash("Failed to generate Excel file.", 'danger')

    # Render appropriate form template
    return render_template(f'{company_name.lower()}_form.html')

@app.route('/download_file/<file_name>')
@login_required
def download_file(file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found.", 'danger')
        return redirect(url_for('admin_panel')) # Or wherever appropriate

@app.route('/delete_file/<file_name>')
@login_required
def delete_file(file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{file_name}' deleted successfully.", 'success')
    else:
        flash("File not found.", 'danger')
    return redirect(url_for('admin_panel'))

@app.route('/admin_panel')
@login_required
def admin_panel():
    if session.get('username') != 'salish': # Only 'salish' can access admin
        flash("Access denied. Only administrators can view this page.", 'danger')
        return redirect(url_for('company_selection'))

    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin_panel.html', files=files)

# --- Calculation and Excel Generation Logic ---
def process_and_generate_excel(company, data):
    # This is a simplified example. Real logic would be more complex.
    # The 'data' dictionary will contain all form inputs.

    df_data = {
        "Field": [],
        "Value": []
    }

    # Add common fields
    df_data["Field"].extend(["TIME ZONES", "SPEED & CONS", "CHOPTION", "GEO ROTATION", "FULL DISCHARGE"])
    df_data["Value"].extend([
        data.get('time_zones', ''),
        data.get('speed_cons', ''),
        data.get('choption', 'No'), # Checkbox will be 'on' or absent
        data.get('geo_rotation', 'No'),
        data.get('full_discharge', 'No')
    ])

    calculated_value = 0
    demurrage = 0

    if company == "IOC":
        base_rate = float(data.get('base_rate', 0))
        selected_ports = data.get('ioc_ports', []) # This would be a list from multi-select/checkboxes

        # Example IOC logic (simplified)
        if "Haldia" in selected_ports and len(selected_ports) == 2: # "1:2 any one port India + Haldia"
            calculated_value = base_rate
        elif ("Vizag" in selected_ports or "Paradip" in selected_ports) and len(selected_ports) == 2:
            calculated_value = base_rate - 100000
        elif "Ennore" in selected_ports and len(selected_ports) == 2:
            calculated_value = base_rate - 200000
        elif "West Coast India" in selected_ports and data.get('geo_rotation') == 'No':
            calculated_value = base_rate - 200000
        elif len(selected_ports) == 3 and "Haldia" in selected_ports: # "1:3 any 3 ports disch including Haldia"
            calculated_value = base_rate + 100000
        else:
            calculated_value = base_rate # Default or error handling

        demurrage = 0 # IOC specific demurrage not provided, assuming 0 or default if not given
        df_data["Field"].append("Base Rate")
        df_data["Value"].append(base_rate)
        df_data["Field"].append("Selected Ports")
        df_data["Value"].append(", ".join(selected_ports))

    elif company == "HPCL":
        hpcl_option = data.get('hpcl_option', '')
        if hpcl_option == 'option1':
            calculated_value = 1600000 - 520000
        elif hpcl_option == 'option2':
            calculated_value = 1420000 - 700000
        elif hpcl_option == 'option3':
            calculated_value = 2100000 - 20000
        elif hpcl_option == 'option4':
            calculated_value = 2120000 # base rate
        elif hpcl_option == 'option5':
            calculated_value = 1670000 - 450000
        elif hpcl_option == 'option6':
            calculated_value = 2030000 - 90000
        demurrage = 25000
        df_data["Field"].append("HPCL Option Selected")
        df_data["Value"].append(hpcl_option)

    elif company == "BPCL":
        bpcl_option = data.get('bpcl_option', '')
        if bpcl_option == 'option1':
            calculated_value = 3450000
        elif bpcl_option == 'option2':
            calculated_value = 3430000
        elif bpcl_option == 'option3':
            calculated_value = 3280000
        elif bpcl_option == 'option4':
            calculated_value = 2860000
        elif bpcl_option == 'option5':
            calculated_value = 2790000
        elif bpcl_option == 'option6':
            calculated_value = 2770000
        demurrage = 57000
        df_data["Field"].append("BPCL Option Selected")
        df_data["Value"].append(bpcl_option)

    df_data["Field"].append("Calculated Freight")
    df_data["Value"].append(f"${calculated_value:,.2f}")
    df_data["Field"].append("Demurrage (USD PDPR)")
    df_data["Value"].append(f"${demurrage:,.2f}")
    df_data["Field"].append("Total (Freight + Demurrage)")
    df_data["Value"].append(f"${calculated_value + demurrage:,.2f}")


    df = pd.DataFrame(df_data)

    file_name = f"{company}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    try:
        # Save to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Calculation Result', index=False)
            # You can add more sheets or formatting here
            # For example, adding an image (logo) requires specific openpyxl methods
            # writer.sheets['Calculation Result'].add_image(img, 'A1') # Complex, needs image object

        return file_path
    except Exception as e:
        print(f"Error generating Excel: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True) # Set debug=False in production