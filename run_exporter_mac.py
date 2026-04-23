#!/usr/bin/env python3
"""
WordPress Exporter - macOS GUI Launcher
Double-click this file to run wp-exporter without terminal
"""

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, scrolledtext
import subprocess
import os
import threading
import sys

class WpExporterMacGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WordPress Exporter")
        self.root.geometry("700x600")
        
        # Configure style for macOS
        self.root.configure(bg='#f0f0f0')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header_frame, text="🚀 WordPress Exporter", 
                       font=("SF Pro Display", 18, "bold"), 
                       bg='#f0f0f0', fg='#333')
        title.pack()
        
        subtitle = tk.Label(header_frame, text="Extract content from WordPress sites", 
                          font=("SF Pro Text", 12), 
                          bg='#f0f0f0', fg='#666')
        subtitle.pack()
        
        # Mode selection
        mode_frame = tk.LabelFrame(main_frame, text="Extraction Mode", 
                                font=("SF Pro Text", 14, "bold"), 
                                bg='#f0f0f0', fg='#333')
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.mode_var = tk.StringVar(value="live")
        live_radio = tk.Radiobutton(mode_frame, text="🌐 Live WordPress Site", 
                                  variable=self.mode_var, value="live",
                                  font=("SF Pro Text", 12), bg='#f0f0f0')
        live_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        xml_radio = tk.Radiobutton(mode_frame, text="📄 XML Export File", 
                                 variable=self.mode_var, value="xml",
                                 font=("SF Pro Text", 12), bg='#f0f0f0')
        xml_radio.pack(anchor=tk.W, padx=10, pady=5)
        
        # Input section
        input_frame = tk.LabelFrame(main_frame, text="Source Configuration", 
                                  font=("SF Pro Text", 14, "bold"), 
                                  bg='#f0f0f0', fg='#333')
        input_frame.pack(fill=tk.X, pady=10)
        
        # URL/File input
        url_frame = tk.Frame(input_frame, bg='#f0f0f0')
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(url_frame, text="Site URL or XML File:", 
                font=("SF Pro Text", 12), bg='#f0f0f0').pack(anchor=tk.W)
        
        url_entry_frame = tk.Frame(url_frame, bg='#f0f0f0')
        url_entry_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = tk.Entry(url_entry_frame, font=("SF Pro Text", 12))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(url_entry_frame, text="Browse", 
                 command=self.browse_file,
                 font=("SF Pro Text", 10)).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Authentication
        auth_frame = tk.Frame(input_frame, bg='#f0f0f0')
        auth_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(auth_frame, text="Credentials (user:password, leave empty if public):", 
                font=("SF Pro Text", 12), bg='#f0f0f0').pack(anchor=tk.W)
        
        self.auth_entry = tk.Entry(auth_frame, font=("SF Pro Text", 12), show="*")
        self.auth_entry.pack(fill=tk.X, pady=5)
        
        # Options
        options_frame = tk.LabelFrame(main_frame, text="Options", 
                                    font=("SF Pro Text", 14, "bold"), 
                                    bg='#f0f0f0', fg='#333')
        options_frame.pack(fill=tk.X, pady=10)
        
        # Checkboxes
        self.list_categories_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="📋 List Categories", 
                      variable=self.list_categories_var,
                      font=("SF Pro Text", 11), bg='#f0f0f0').pack(anchor=tk.W, padx=10, pady=2)
        
        self.clean_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="🧹 Clean Plugin Shortcodes", 
                      variable=self.clean_var,
                      font=("SF Pro Text", 11), bg='#f0f0f0').pack(anchor=tk.W, padx=10, pady=2)
        
        self.stats_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="📊 Show Statistics", 
                      variable=self.stats_var,
                      font=("SF Pro Text", 11), bg='#f0f0f0').pack(anchor=tk.W, padx=10, pady=2)
        
        # Output format
        format_frame = tk.Frame(options_frame, bg='#f0f0f0')
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(format_frame, text="Output Format:", 
                font=("SF Pro Text", 12), bg='#f0f0f0').pack(anchor=tk.W)
        
        format_radio_frame = tk.Frame(format_frame, bg='#f0f0f0')
        format_radio_frame.pack(fill=tk.X, pady=5)
        
        self.format_var = tk.StringVar(value="html")
        tk.Radiobutton(format_radio_frame, text="HTML", 
                      variable=self.format_var, value="html",
                      font=("SF Pro Text", 11), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 20))
        tk.Radiobutton(format_radio_frame, text="Markdown", 
                      variable=self.format_var, value="markdown",
                      font=("SF Pro Text", 11), bg='#f0f0f0').pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(button_frame, text="📋 List Categories", 
                 command=self.list_categories,
                 font=("SF Pro Text", 12, "bold"), 
                 bg='#007AFF', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="📤 Extract Content", 
                 command=self.extract_content,
                 font=("SF Pro Text", 12, "bold"), 
                 bg='#34C759', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="🗑️ Clear", 
                 command=self.clear_fields,
                 font=("SF Pro Text", 12), 
                 bg='#FF9500', fg='white', padx=20, pady=10).pack(side=tk.LEFT)
        
        # Output area
        output_frame = tk.LabelFrame(main_frame, text="Output", 
                                   font=("SF Pro Text", 14, "bold"), 
                                   bg='#f0f0f0', fg='#333')
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                   height=12, 
                                                   font=("SF Mono", 10),
                                                   bg='#1e1e1e', fg='#00ff00')
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="✅ Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                            relief=tk.SUNKEN, anchor=tk.W,
                            font=("SF Pro Text", 10), bg='#f0f0f0')
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
    def browse_file(self):
        """Browse for XML file"""
        filename = filedialog.askopenfilename(
            title="Select WordPress XML Export File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, filename)
            self.mode_var.set("xml")
            
    def clear_fields(self):
        """Clear all input fields"""
        self.url_entry.delete(0, tk.END)
        self.auth_entry.delete(0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("✅ Ready")
        
    def get_script_path(self):
        """Get path to wp-exporter.py"""
        return os.path.join(os.path.dirname(__file__), 'wp-exporter.py')
        
    def build_command(self, action="list"):
        """Build command based on user input"""
        script_path = self.get_script_path()
        mode = self.mode_var.get()
        
        if mode == "live":
            domain = self.url_entry.get().strip()
            auth = self.auth_entry.get().strip()
            
            if not domain:
                messagebox.showerror("Error", "Please enter a WordPress site URL")
                return None
                
            command = f'python3 "{script_path}" --domain "{domain}"'
            
            if auth:
                command += f' --auth "{auth}"'
        else:
            xml_file = self.url_entry.get().strip()
            
            if not xml_file or not os.path.exists(xml_file):
                messagebox.showerror("Error", "Please select a valid XML file")
                return None
                
            command = f'python3 "{script_path}" "{xml_file}"'
            
        # Add options
        if self.list_categories_var.get() or action == "list":
            command += " --list-categories"
            
        if self.clean_var.get():
            command += " --clean"
            
        if self.stats_var.get():
            command += " --stats"
            
        if self.format_var.get() == "markdown":
            command += " --format markdown"
            
        return command
        
    def log_output(self, message):
        """Add message to output area"""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.root.update()
        
    def run_command(self, command):
        """Run command in separate thread"""
        try:
            self.status_var.set("⏳ Running...")
            self.log_output(f"🚀 Executing: {command}")
            self.log_output("=" * 60)
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
            
            if result.stdout:
                self.log_output("📤 OUTPUT:")
                self.log_output(result.stdout)
                
            if result.stderr:
                self.log_output("⚠️ ERRORS:")
                self.log_output(result.stderr)
                
            self.status_var.set("✅ Complete")
            
        except Exception as e:
            self.log_output(f"❌ Error: {e}")
            self.status_var.set("❌ Error")
            
    def list_categories(self):
        """List categories command"""
        command = self.build_command("list")
        if command:
            self.output_text.delete(1.0, tk.END)
            thread = threading.Thread(target=self.run_command, args=(command,))
            thread.start()
            
    def extract_content(self):
        """Extract content command"""
        command = self.build_command("extract")
        if command:
            self.output_text.delete(1.0, tk.END)
            self.list_categories_var.set(False)  # Don't list categories for extraction
            thread = threading.Thread(target=self.run_command, args=(command,))
            thread.start()
            
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check if wp-exporter.py exists
    script_path = os.path.join(os.path.dirname(__file__), 'wp-exporter.py')
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"wp-exporter.py not found in {os.path.dirname(__file__)}\n\nPlease ensure both files are in the same directory.")
        sys.exit(1)
        
    app = WpExporterMacGUI()
    app.run()
