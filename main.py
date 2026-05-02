# ============================================================
# SMART-IB-ASSIST — MAIN UI (FINAL INTEGRATION)
# ============================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage

import threading
import json
import os
import hashlib
import uuid
import re

# ===== IMPORT YOUR EXISTING LOGIC =====
from research_modes import (
    run_single_company_research,
    run_comparative_company_research
)
from investor_guided_discovery import investor_guided_discovery
from pdf_report_generator import generate_ai_report

# ============================================================
# UI CONFIG
# ============================================================

Window.size = (420, 900)
Window.clearcolor = (0.08, 0.09, 0.12, 1)

# ============================================================
# COLOR PALETTE
# ============================================================

COLORS = {
    "bg_dark": (0.08, 0.09, 0.12, 1),
    "bg_card": (0.12, 0.14, 0.18, 1),
    "primary": (0.29, 0.56, 0.89, 1),
    "primary_hover": (0.35, 0.62, 0.95, 1),
    "secondary": (0.18, 0.80, 0.55, 1),
    "text_white": (0.95, 0.95, 0.97, 1),
    "text_gray": (0.6, 0.62, 0.68, 1),
    "text_muted": (0.4, 0.42, 0.48, 1),
    "danger": (0.89, 0.35, 0.40, 1),
    "card_border": (0.22, 0.24, 0.30, 1),
    "gold": (0.85, 0.65, 0.20, 1),
}

# ============================================================
# USER DATA MANAGEMENT
# ============================================================

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

def load_users():
    ensure_data_dir()
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    ensure_data_dir()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    users = load_users()
    if email in users:
        return False, "Email already registered"
    
    user_id = str(uuid.uuid4())
    users[email] = {
        "user_id": user_id,
        "pw": hash_password(password)
    }
    save_users(users)
    
    # Create user data folder
    user_dir = os.path.join(DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    for fname in ["favorites.json", "recent.json", "reports.json"]:
        fpath = os.path.join(user_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, "w") as f:
                json.dump([], f)
    
    return True, user_id

def authenticate_user(email, password):
    users = load_users()
    if email not in users:
        return False, "Email not found"
    
    if users[email]["pw"] != hash_password(password):
        return False, "Incorrect password"
    
    return True, users[email]["user_id"]

# ============================================================
# STYLED COMPONENTS
# ============================================================

class StyledButton(Button):
    def __init__(self, text, color_type="primary", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color_type = color_type
        self.size_hint_y = None
        self.height = 52
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.color = COLORS["text_white"]
        self.bold = True
        self.font_size = 16
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas())

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.color_type == "primary":
                Color(*COLORS["primary"])
            elif self.color_type == "secondary":
                Color(*COLORS["secondary"])
            elif self.color_type == "danger":
                Color(*COLORS["danger"])
            elif self.color_type == "gold":
                Color(*COLORS["gold"])
            else:
                Color(*COLORS["bg_card"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])


class StyledTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 52
        self.background_color = COLORS["bg_card"]
        self.foreground_color = COLORS["text_white"]
        self.hint_text_color = COLORS["text_muted"]
        self.cursor_color = COLORS["primary"]
        self.font_size = 15
        self.padding = [16, 16, 16, 16]
        self.multiline = False


class CardLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [20, 16, 20, 16]
        self.spacing = 12
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas())

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS["bg_card"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[16])


# ============================================================
# MAIN APP
# ============================================================

class SmartIBApp(App):

    def build(self):
        self.title = "SMART-IB-ASSIST"
        self.current_user = None
        self.current_user_id = None
        self.root = BoxLayout(orientation="vertical", padding=20, spacing=16)
        self.show_login()
        return self.root

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def clear(self):
        self.root.clear_widgets()

    def header(self, text, subtitle=None):
        container = BoxLayout(orientation="vertical", size_hint_y=None, height=80, spacing=4)
        
        title = Label(
            text=text,
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=40,
            color=COLORS["text_white"],
            halign="center"
        )
        title.bind(size=title.setter("text_size"))
        container.add_widget(title)
        
        if subtitle:
            sub = Label(
                text=subtitle,
                font_size=13,
                size_hint_y=None,
                height=24,
                color=COLORS["text_gray"],
                halign="center"
            )
            sub.bind(size=sub.setter("text_size"))
            container.add_widget(sub)
        
        return container

    def info(self, text, color=None):
        lbl = Label(
            text=text,
            size_hint_y=None,
            color=color or COLORS["text_gray"],
            font_size=14,
            halign="center",
            valign="middle"
        )
        lbl.bind(texture_size=lambda i, v: setattr(i, "height", max(v[1], 30)))
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def spacer(self, height=20):
        return Widget(size_hint_y=None, height=height)

    # --------------------------------------------------------
    # LOGIN SCREEN
    # --------------------------------------------------------

    def show_login(self):
        self.clear()

        self.root.add_widget(self.spacer(60))
        self.root.add_widget(self.header(
            "🏦 SMART-IB-ASSIST",
            "AI-Powered Investment Research"
        ))
        self.root.add_widget(self.spacer(40))

        card = CardLayout()
        
        title = Label(
            text="Sign In",
            font_size=20,
            bold=True,
            size_hint_y=None,
            height=35,
            color=COLORS["text_white"]
        )
        card.add_widget(title)
        card.add_widget(self.spacer(8))
        
        email_input = StyledTextInput(hint_text="Email address")
        password_input = StyledTextInput(hint_text="Password")
        password_input.password = True
        
        status = self.info("", color=COLORS["danger"])

        def do_login(_):
            email = email_input.text.strip()
            password = password_input.text.strip()
            
            if not email or not password:
                status.text = "⚠️ Please fill in all fields"
                return
            
            success, result = authenticate_user(email, password)
            if success:
                self.current_user = email
                self.current_user_id = result
                self.show_dashboard()
            else:
                status.text = f"❌ {result}"

        card.add_widget(email_input)
        card.add_widget(password_input)
        card.add_widget(self.spacer(8))
        card.add_widget(StyledButton(
            text="Sign In",
            color_type="primary",
            on_press=do_login
        ))
        card.add_widget(status)
        
        self.root.add_widget(card)
        self.root.add_widget(self.spacer(20))
        
        # Sign up link
        signup_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        signup_row.add_widget(Widget())
        signup_row.add_widget(self.info("Don't have an account?"))
        signup_btn = StyledButton(
            text="Sign Up",
            color_type="secondary",
            on_press=lambda _: self.show_signup()
        )
        signup_btn.size_hint_x = 0.4
        signup_row.add_widget(signup_btn)
        signup_row.add_widget(Widget())
        
        self.root.add_widget(signup_row)
        self.root.add_widget(Widget())

    # --------------------------------------------------------
    # SIGNUP SCREEN
    # --------------------------------------------------------

    def show_signup(self):
        self.clear()

        self.root.add_widget(self.spacer(40))
        self.root.add_widget(self.header(
            "📝 Create Account",
            "Join SMART-IB-ASSIST"
        ))
        self.root.add_widget(self.spacer(30))

        card = CardLayout()
        
        email_input = StyledTextInput(hint_text="Email address")
        password_input = StyledTextInput(hint_text="Password (min 6 characters)")
        password_input.password = True
        confirm_input = StyledTextInput(hint_text="Confirm password")
        confirm_input.password = True
        
        status = self.info("", color=COLORS["danger"])

        def do_signup(_):
            email = email_input.text.strip()
            password = password_input.text.strip()
            confirm = confirm_input.text.strip()
            
            if not email or not password or not confirm:
                status.text = "⚠️ Please fill in all fields"
                return
            
            if "@" not in email or "." not in email:
                status.text = "⚠️ Please enter a valid email"
                return
            
            if len(password) < 6:
                status.text = "⚠️ Password must be at least 6 characters"
                return
            
            if password != confirm:
                status.text = "⚠️ Passwords do not match"
                return
            
            success, result = register_user(email, password)
            if success:
                self.current_user = email
                self.current_user_id = result
                self.show_dashboard()
            else:
                status.text = f"❌ {result}"

        card.add_widget(email_input)
        card.add_widget(password_input)
        card.add_widget(confirm_input)
        card.add_widget(self.spacer(8))
        card.add_widget(StyledButton(
            text="Create Account",
            color_type="secondary",
            on_press=do_signup
        ))
        card.add_widget(status)
        
        self.root.add_widget(card)
        self.root.add_widget(self.spacer(20))
        
        # Back to login
        back_row = BoxLayout(size_hint_y=None, height=50, spacing=8)
        back_row.add_widget(Widget())
        back_row.add_widget(self.info("Already have an account?"))
        back_btn = StyledButton(
            text="Sign In",
            color_type="primary",
            on_press=lambda _: self.show_login()
        )
        back_btn.size_hint_x = 0.4
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        
        self.root.add_widget(back_row)
        self.root.add_widget(Widget())

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    def show_dashboard(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        
        # User greeting
        user_display = self.current_user.split("@")[0] if self.current_user else "User"
        self.root.add_widget(self.header(
            f"👋 Welcome, {user_display}!",
            "What would you like to research today?"
        ))
        self.root.add_widget(self.spacer(20))

        card = CardLayout()
        
        card.add_widget(StyledButton(
            text="🔍  Start Research",
            color_type="primary",
            on_press=lambda _: self.show_mode_select()
        ))
        
        card.add_widget(StyledButton(
            text="📄  View Recent Reports",
            color_type="secondary",
            on_press=lambda _: self.show_reports_list()
        ))
        
        self.root.add_widget(card)
        self.root.add_widget(Widget())
        
        # Bottom buttons
        bottom = BoxLayout(size_hint_y=None, height=52, spacing=12)
        
        logout_btn = StyledButton(
            text="🚪 Logout",
            color_type="card",
            on_press=lambda _: self.logout()
        )
        bottom.add_widget(logout_btn)
        
        exit_btn = StyledButton(
            text="Exit",
            color_type="danger",
            on_press=lambda _: App.get_running_app().stop()
        )
        bottom.add_widget(exit_btn)
        
        self.root.add_widget(bottom)

    def logout(self):
        self.current_user = None
        self.current_user_id = None
        self.show_login()

    # --------------------------------------------------------
    # MODE SELECTION
    # --------------------------------------------------------

    def show_mode_select(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        self.root.add_widget(self.header(
            "Select Research Mode",
            "Choose the type of analysis you need"
        ))
        self.root.add_widget(self.spacer(20))

        card = CardLayout()
        
        card.add_widget(StyledButton(
            text="🏢  Single Company Research",
            color_type="primary",
            on_press=lambda _: self.single_company_ui()
        ))
        
        card.add_widget(StyledButton(
            text="⚖️  Comparative Analysis",
            color_type="primary",
            on_press=lambda _: self.comparative_ui()
        ))
        
        card.add_widget(StyledButton(
            text="💡  Investor-Guided Discovery",
            color_type="gold",
            on_press=lambda _: self.investor_guided_ui()
        ))
        
        self.root.add_widget(card)
        self.root.add_widget(Widget())

        self.root.add_widget(StyledButton(
            text="← Back to Dashboard",
            color_type="card",
            on_press=lambda _: self.show_dashboard()
        ))

    # --------------------------------------------------------
    # SINGLE COMPANY
    # --------------------------------------------------------

    def single_company_ui(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        self.root.add_widget(self.header(
            "🏢 Single Company Research",
            "Get comprehensive analysis of one company"
        ))
        self.root.add_widget(self.spacer(20))

        card = CardLayout()
        
        company_input = StyledTextInput(hint_text="Enter company name (e.g., Stripe)")
        status = self.info("", color=COLORS["text_muted"])

        def run(_):
            if not company_input.text.strip():
                status.text = "⚠️ Please enter a company name"
                status.color = COLORS["danger"]
                return
            status.text = "🔄 Running agentic research… please wait."
            status.color = COLORS["primary"]
            threading.Thread(
                target=self._run_single_company,
                args=(company_input.text.strip(), status),
                daemon=True
            ).start()

        card.add_widget(company_input)
        card.add_widget(self.spacer(8))
        card.add_widget(StyledButton(
            text="🚀  Run Research",
            color_type="primary",
            on_press=run
        ))
        card.add_widget(self.spacer(8))
        card.add_widget(status)
        
        self.root.add_widget(card)
        self.root.add_widget(Widget())

        self.root.add_widget(StyledButton(
            text="← Back",
            color_type="card",
            on_press=lambda _: self.show_mode_select()
        ))

    def _run_single_company(self, company, status_label):
        try:
            result = run_single_company_research(company)
            html_path = generate_ai_report(
                report_data=result,
                report_type="Single Company Research",
                output_name=f"{company.replace(' ', '_')}_single"
            )
            Clock.schedule_once(lambda dt: self.show_html_preview(html_path, company))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(status_label, "text", f"❌ Error: {str(e)}"))

    # --------------------------------------------------------
    # COMPARATIVE
    # --------------------------------------------------------

    def comparative_ui(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        self.root.add_widget(self.header(
            "⚖️ Comparative Analysis",
            "Compare multiple companies side by side"
        ))
        self.root.add_widget(self.spacer(20))

        card = CardLayout()
        
        companies_input = StyledTextInput(hint_text="e.g., Stripe, Square, Adyen")
        status = self.info("", color=COLORS["text_muted"])

        def run(_):
            companies = [c.strip() for c in companies_input.text.split(",") if c.strip()]
            if len(companies) < 2:
                status.text = "⚠️ Enter at least 2 companies, separated by commas"
                status.color = COLORS["danger"]
                return
            status.text = "🔄 Running comparative research… please wait."
            status.color = COLORS["primary"]
            threading.Thread(
                target=self._run_comparative,
                args=(companies, status),
                daemon=True
            ).start()

        card.add_widget(companies_input)
        card.add_widget(self.spacer(8))
        card.add_widget(StyledButton(
            text="🚀  Run Comparison",
            color_type="primary",
            on_press=run
        ))
        card.add_widget(self.spacer(8))
        card.add_widget(status)
        
        self.root.add_widget(card)
        self.root.add_widget(Widget())

        self.root.add_widget(StyledButton(
            text="← Back",
            color_type="card",
            on_press=lambda _: self.show_mode_select()
        ))

    def _run_comparative(self, companies, status_label):
        try:
            result = run_comparative_company_research(companies)
            html_path = generate_ai_report(
                report_data=result,
                report_type="Comparative Analysis",
                output_name="comparative_analysis"
            )
            Clock.schedule_once(lambda dt: self.show_html_preview(html_path, "Comparative Analysis"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(status_label, "text", f"❌ Error: {str(e)}"))

    # --------------------------------------------------------
    # INVESTOR-GUIDED
    # --------------------------------------------------------

    def investor_guided_ui(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        self.root.add_widget(self.header(
            "💡 Investor-Guided Discovery",
            "AI will interview you to find matching companies"
        ))
        self.root.add_widget(self.spacer(20))

        card = CardLayout()
        
        info_text = self.info(
            "This mode will ask you questions in the terminal.\n"
            "Answer them there to build your investor profile.\n"
            "The UI will update when complete.",
            color=COLORS["text_gray"]
        )
        info_text.height = 80
        
        status = self.info("", color=COLORS["text_muted"])

        def run(_):
            status.text = "🔄 Investor-guided discovery running…\nCheck your terminal for questions."
            status.color = COLORS["primary"]
            threading.Thread(
                target=self._run_investor_guided,
                args=(status,),
                daemon=True
            ).start()

        card.add_widget(info_text)
        card.add_widget(self.spacer(12))
        card.add_widget(StyledButton(
            text="🎯  Start Discovery",
            color_type="gold",
            on_press=run
        ))
        card.add_widget(self.spacer(8))
        card.add_widget(status)
        
        self.root.add_widget(card)
        self.root.add_widget(Widget())

        self.root.add_widget(StyledButton(
            text="← Back",
            color_type="card",
            on_press=lambda _: self.show_mode_select()
        ))

    def _run_investor_guided(self, status_label):
        try:
            result = investor_guided_discovery()
            html_path = generate_ai_report(
                report_data=result,
                report_type="Investor-Guided Discovery",
                output_name="investor_guided_discovery"
            )
            Clock.schedule_once(lambda dt: self.show_html_preview(html_path, "Investor Discovery"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(status_label, "text", f"❌ Error: {str(e)}"))

    # --------------------------------------------------------
    # HTML PREVIEW (DISPLAY REPORT)
    # --------------------------------------------------------

    def show_html_preview(self, html_path, title):
        self.clear()

        self.root.add_widget(self.spacer(10))
        self.root.add_widget(self.header(
            f"📄 {title}",
            f"Report saved: {os.path.basename(html_path)}"
        ))
        self.root.add_widget(self.spacer(10))

        scroll = ScrollView(size_hint=(1, 1))
        content_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=8,
            padding=[10, 10, 10, 20]
        )
        content_container.bind(minimum_height=content_container.setter("height"))

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Extract text content from HTML (simple parsing)
            # Remove style and head tags
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<head[^>]*>.*?</head>', '', html_content, flags=re.DOTALL)
            
            # Convert HTML to readable text for Kivy
            text_content = html_content
            text_content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n[b][size=22][color=4a90e2]\1[/color][/size][/b]\n', text_content)
            text_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n[b][size=18][color=5cb85c]\1[/color][/size][/b]\n', text_content)
            text_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n[b][size=16][color=f0ad4e]\1[/color][/size][/b]\n', text_content)
            text_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text_content, flags=re.DOTALL)
            text_content = re.sub(r'<li[^>]*>(.*?)</li>', r'  • \1\n', text_content)
            text_content = re.sub(r'<br\s*/?>', '\n', text_content)
            text_content = re.sub(r'<[^>]+>', '', text_content)  # Remove remaining tags
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)  # Clean up extra newlines
            text_content = text_content.strip()
            
            # Create label with markup
            report_label = Label(
                text=text_content,
                markup=True,
                size_hint_y=None,
                color=COLORS["text_white"],
                font_size=14,
                halign="left",
                valign="top",
                text_size=(380, None)
            )
            report_label.bind(texture_size=lambda i, v: setattr(i, "height", v[1] + 20))
            content_container.add_widget(report_label)
            
        except Exception as e:
            error_label = self.info(f"❌ Could not load report: {str(e)}", color=COLORS["danger"])
            error_label.height = 60
            content_container.add_widget(error_label)
            
            path_label = self.info(f"Report saved at:\n{html_path}")
            path_label.height = 60
            content_container.add_widget(path_label)

        scroll.add_widget(content_container)
        self.root.add_widget(scroll)

        self.root.add_widget(StyledButton(
            text="← Back to Dashboard",
            color_type="primary",
            on_press=lambda _: self.show_dashboard()
        ))

    # --------------------------------------------------------
    # REPORTS LIST
    # --------------------------------------------------------

    def show_reports_list(self):
        self.clear()

        self.root.add_widget(self.spacer(20))
        self.root.add_widget(self.header(
            "📄 Recent Reports",
            "View previously generated reports"
        ))
        self.root.add_widget(self.spacer(20))

        scroll = ScrollView(size_hint=(1, 1))
        reports_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=10
        )
        reports_container.bind(minimum_height=reports_container.setter("height"))

        from kivy.utils import platform
        if platform == "android":
            reports_dir = "/sdcard/SMART_IB_ASSIST/reports"
        else:
            reports_dir = "reports"
            
        if os.path.exists(reports_dir):
            html_files = [f for f in os.listdir(reports_dir) if f.endswith(".html")]
            html_files.sort(key=lambda x: os.path.getmtime(os.path.join(reports_dir, x)), reverse=True)
            
            if html_files:
                for html_file in html_files:
                    html_path = os.path.join(reports_dir, html_file)
                    btn = StyledButton(
                        text=f"📄  {html_file}",
                        color_type="card"
                    )
                    btn.bind(on_press=lambda _, p=html_path, n=html_file: self.show_html_preview(p, n.replace(".html", "")))
                    reports_container.add_widget(btn)
            else:
                reports_container.add_widget(self.info("No reports found yet.\nRun a research to generate one!"))
        else:
            reports_container.add_widget(self.info("Reports folder not found."))

        scroll.add_widget(reports_container)
        self.root.add_widget(scroll)

        self.root.add_widget(StyledButton(
            text="← Back to Dashboard",
            color_type="card",
            on_press=lambda _: self.show_dashboard()
        ))


# ============================================================
if __name__ == "__main__":
    SmartIBApp().run()
