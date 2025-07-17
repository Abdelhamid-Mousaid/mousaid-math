import streamlit as st
import hashlib
import uuid
import smtplib
from email.mime.text import MIMEText
import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import subprocess

# Assuming db.py is in the backend directory
from backend import db

# Initialize the database
db.init_db()

# --- Configuration ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "mousaid.abdelhamid@gmail.com"  # Replace with your email
SMTP_PASSWORD = "oben fptc lgbk fhor"  # Replace with your email password
BASE_URL = "https://mousaid-math.streamlit.app/" # Hardcoded for deployed app

LATEX_TEMPLATES_DIR = "backend/latex_templates"
GENERATED_PDFS_DIR = "generated_pdfs"

if not os.path.exists(GENERATED_PDFS_DIR):
    os.makedirs(GENERATED_PDFS_DIR)

# --- Helper Functions ---
def send_verification_email(email, token):
    msg = MIMEText(f"Click the link to verify your account: {BASE_URL}/?token={token}")
    msg['Subject'] = "Verify your email address"
    msg['From'] = SMTP_USERNAME
    msg['To'] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

def generate_pdf(data, template_path, output_filename):
    st.info("Step 1: Rendering LaTeX template...")
    env = Environment(
        loader=FileSystemLoader("backend/latex_templates"),
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='<<',
        variable_end_string='>>',
        comment_start_string='((*',
        comment_end_string='*))',
        autoescape=False,
    )
    template = env.get_template(template_path)
    rendered_latex = template.render(data)

    st.info("Step 2: Creating temporary .tex file...")
    tex_file_path = os.path.join(GENERATED_PDFS_DIR, output_filename + ".tex")
    with open(tex_file_path, "w", encoding="utf-8") as f:
        f.write(rendered_latex)

    st.error("PDF generation is not available in this deployed environment.")
    st.info("To enable PDF generation, you need a separate LaTeX compilation service (e.g., a dedicated server running Docker with XeLaTeX, or a cloud-based LaTeX API).")
    return None


def escape_latex(text):
    # Basic LaTeX escaping (can be expanded)
    text = text.replace("&", "\&")
    text = text.replace("%", "\%")
    text = text.replace("$", "\$")
    text = text.replace("#", "\#")
    text = text.replace("_", "\_")
    text = text.replace("{", "\{")
    text = text.replace("}", "\}")
    text = text.replace("~", "\textasciitilde{}")
    text = text.replace("^", "\textasciicircum{}")
    text = text.replace("\\", "\textbackslash{}")
    return text

# --- Streamlit App ---
def generate_free_pdf_interface(selected_level):
    st.subheader(f"Générer le PDF Gratuit pour {selected_level}")

    # Initialize session state for PDF path
    # Initialize session state for PDF path
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None

    with st.form("free_pdf_form_final"):
        nom_complet = st.text_input("Nom Complet", value=st.session_state.user_name, key="free_nom_complet_final", autocomplete="name")
        nom_ecole = st.text_input("Nom de l'école", value=st.session_state.get('free_nom_ecole', ''), key="free_nom_ecole_final", autocomplete="organization")
        annee_scolaire = st.text_input("Année Scolaire", value=st.session_state.get('free_annee_scolaire', f"{datetime.now().year}-{datetime.now().year + 1}"), key="free_annee_scolaire_final", autocomplete="off")
        
        chapitre = "1"
        submit_pdf_button = st.form_submit_button("Générer le PDF")

        if submit_pdf_button:
            # Clear previous PDF path
            st.session_state.pdf_path = None

            st.session_state.free_nom_ecole = nom_ecole
            st.session_state.free_annee_scolaire = annee_scolaire

            data = {
                "nom_complet": escape_latex(nom_complet),
                "email": escape_latex(st.session_state.user_email),
                "nom_ecole": escape_latex(nom_ecole),
                "annee_scolaire": escape_latex(annee_scolaire),
                "date": escape_latex(datetime.now().strftime('%d/%m/%Y')),
                "niveau_classe": escape_latex(selected_level),
                "chapitre": escape_latex(chapitre)
            }
            template_path = f"{selected_level}/1er_semestre/CH-1.tex"
            output_filename = f"planificateur_{selected_level}_S1_CH1_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            pdf_path = generate_pdf(data, template_path, output_filename)
            if pdf_path:
                st.session_state.pdf_path = pdf_path
                st.session_state.show_free_pdf_interface = False # Hide the form
                st.rerun() # Rerun to show the download button
                
                



    



# --- Main execution ---
st.set_page_config(layout="wide", page_title="Mousaid Math - Plateforme Pédagogique")

def show_dashboard():
    st.sidebar.title(f"Bienvenue, {st.session_state.user_name}!")
    if st.sidebar.button("Déconnexion", key="sidebar_logout_button"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_paid_plans = {}
        st.rerun()

    st.title("Votre Tableau de Bord")

    st.header("Plans Disponibles")

    # Display PDF download button if a PDF was generated
    if st.session_state.get('pdf_path'):
        st.success(f"PDF generated successfully! You can download it below.")
        try:
            with open(st.session_state.pdf_path, "rb") as f:
                st.download_button(
                    label="Télécharger le PDF",
                    data=f.read(),
                    file_name=os.path.basename(st.session_state.pdf_path),
                    mime="application/pdf",
                    key=f"download_pdf_{os.path.basename(st.session_state.pdf_path)}_{datetime.now().timestamp()}"
                )
            # Clear the path after showing the button to prevent re-display on subsequent runs
            st.session_state.pdf_path = None
        except FileNotFoundError:
            st.error(f"Error: PDF file not found at {st.session_state.pdf_path}. Please try generating again.")
            st.session_state.pdf_path = None

    # Initialize session state for showing PDF generation interface
    if 'show_free_pdf_interface' not in st.session_state:
        st.session_state.show_free_pdf_interface = False
    if 'show_paid_pdf_interface' not in st.session_state:
        st.session_state.show_paid_pdf_interface = False

    
            

    # Free Plan
    st.markdown("<div class='plan-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='plan-title'>Plan Gratuit</h3>", unsafe_allow_html=True)
    st.markdown("<p class='plan-price'>Accès gratuit au CH-1 du 1er semestre</p>", unsafe_allow_html=True)
    
    free_levels = ["1APIC", "2APIC", "3APIC", "TCSF", "TCLSHF", "1BACSF", "1BACLSHF", "2BACSM", "2BACPC", "2BACSVTF", "2BACSPCF"]
    selected_free_level = st.selectbox("Sélectionnez le niveau pour le plan gratuit", free_levels, key="free_level_selectbox")
    
    if st.button(f"Générer le PDF Gratuit pour {selected_free_level}", key=f"show_free_pdf_form_button_{selected_free_level}"):
        st.session_state.show_free_pdf_interface = True
        st.session_state.show_paid_pdf_interface = False # Hide paid form if free is shown

    if st.session_state.show_free_pdf_interface:
        generate_free_pdf_interface(selected_free_level)
    st.markdown("</div>", unsafe_allow_html=True)

    st.header("Plans Payants")
    col1, col2, col3 = st.columns(3)

    gumroad_urls = {
        "1er semestre": "https://mousaid.gumroad.com/l/1er-semestre?wanted=true",
        "2eme semestre": "https://mousaid.gumroad.com/l/2eme-semestre?wanted=true",
        "annee complete": "https://mousaid.gumroad.com/l/annee-complete?wanted=true"
    }

    plans = {
        "1er semestre": {"price": "199 DH", "description": "Accès à tous les chapitres du 1er semestre.", "levels": ["1APIC", "2APIC", "3APIC", "TCSF", "TCLSHF", "1BACSF", "1BACLSHF", "2BACSM", "2BACPC", "2BACSVTF", "2BACSPCF"]},
        "2eme semestre": {"price": "199 DH", "description": "Accès à tous les chapitres du 2ème semestre.", "levels": ["1APIC", "2APIC", "3APIC", "TCSF", "TCLSHF", "1BACSF", "1BACLSHF", "2BACSM", "2BACPC", "2BACSVTF", "2BACSPCF"]},
        "annee complete": {"price": "299 DH", "description": "Accès à tous les chapitres de l'année complète.", "levels": ["1APIC", "2APIC", "3APIC", "TCSF", "TCLSHF", "1BACSF", "1BACLSHF", "2BACSM", "2BACPC", "2BACSVTF", "2BACSPCF"]}
    }

    for i, (plan_name, plan_info) in enumerate(plans.items()):
        with [col1, col2, col3][i % 3]:
            st.markdown(f"<div class='plan-card'>", unsafe_allow_html=True)
            st.markdown(f"<h3 class='plan-title'>{plan_name}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p class='plan-price'>{plan_info['price']}</p>", unsafe_allow_html=True)
            st.write(plan_info['description'])

            is_unlocked = plan_name in st.session_state.user_paid_plans

            if is_unlocked:
                st.success("Débloqué!")
                # Allow user to select up to 3 levels for paid plans
                st.write("Sélectionnez jusqu'à 3 niveaux:")
                selected_levels = []
                for j in range(3):
                    level_options = [lvl for lvl in plan_info["levels"] if lvl not in selected_levels]
                    selected_level = st.selectbox(f"Niveau {j+1}", ["-- Select --"] + level_options, key=f"{plan_name}_level_{j}")
                    if selected_level != "-- Select --":
                        selected_levels.append(selected_level)
                
                if st.button(f"Générer PDF pour {plan_name}", key=f"generate_{plan_name}"):
                    generate_paid_pdf_interface(plan_name, selected_levels)

            if st.button(f"Générer PDF pour {plan_name}", key=f"generate_{plan_name}"):
                    st.info(f"PDF generation for {plan_name} is not yet implemented.")

            else:
                buy_button_html = f"<a href='{gumroad_urls[plan_name]}' class='gumroad-button'>Acheter maintenant</a>"
                st.markdown(buy_button_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

def generate_paid_pdf_interface(plan_name, selected_levels):
    st.subheader(f"Générer le PDF Payant pour {plan_name}")
    st.write(f"Selected levels: {', '.join(selected_levels)}")
    st.info("This feature is under development. PDF generation for paid plans will be available soon!")

def show_landing_page():
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Bienvenue sur Mousaid Math</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Votre plateforme dédiée aux ressources pédagogiques en mathématiques pour les enseignants marocains.</p>", unsafe_allow_html=True)

    st.write("## Créez votre compte gratuit")
    with st.form("registration_form"):
        full_name = st.text_input("Nom Complet")
        email = st.text_input("Email")
        password = st.text_input("Mot de Passe", type="password")
        confirm_password = st.text_input("Confirmer le Mot de Passe", type="password")
        submit_button = st.form_submit_button("S'inscrire")

        if submit_button:
            if password == confirm_password:
                verification_token = str(uuid.uuid4())
                if db.add_user(full_name, email, password, verification_token):
                    if send_verification_email(email, verification_token):
                        st.success("Account created! Please check your email to verify your account.")
                    else:
                        st.error("Account created, but failed to send verification email. Please contact support.")
                else:
                    st.error("Email already registered. Please log in or use a different email.")
            else:
                st.error("Passwords do not match.")

    st.write("## Déjà un compte ? Connectez-vous")
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de Passe", type="password", key="login_password")
        login_button = st.form_submit_button("Se Connecter")

        if login_button:
            user = db.authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = user["email"]
                st.session_state.user_name = user["full_name"]
                st.session_state.user_paid_plans = user["paid_plans"]
                st.rerun()
            else:
                st.error("Invalid email or password, or account not verified.")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.user_paid_plans = {}
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = None
        

    # Check for email verification token in URL
    query_params = st.query_params
    if "token" in query_params and not st.session_state.logged_in:
        token = query_params["token"]
        if db.verify_user(token):
            st.success("Email verified successfully! You can now log in.")
        else:
            st.error("Invalid or expired verification token.")
        st.query_params.clear() # Clear the token from the URL

    if st.session_state.logged_in:
        show_dashboard()
    else:
        show_landing_page()

# --- Main execution ---
if __name__ == "__main__":
    main()