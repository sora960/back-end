from flask import Blueprint, render_template

general = Blueprint('general', __name__)

@general.route('/portfolio/emmerwin-pascion')
def emmerwin_pascion_portfolio():
    return render_template('emmerwin_pascion_portfolio.html')

@general.route('/about-system')
def about_system():
    return render_template('about_system.html')  # Create about_system.html in the templates folder

@general.route('/about-us')
def about_us():
    return render_template('about_us.html')  # Create about_us.html in the templates folder
