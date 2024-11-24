from flask import Blueprint, request, session, flash, redirect, url_for, render_template
import ipaddress

ip_setup = Blueprint('ip_setup', __name__)

@ip_setup.route('/set_ip', methods=['GET', 'POST'])
def set_router_ip():
    if request.method == 'POST':
        router_ip = request.form.get('router_ip')
        if validate_ip(router_ip):
            session['router_ip'] = router_ip
            flash("Router IP successfully set!", "success")
            # Use the correct endpoint from the dashboard Blueprint
            return redirect(url_for('dashboard.get_dashboard_data'))
        else:
            flash("Invalid IP address. Please try again.", "error")
    return render_template('IP_input.html')

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
