#!/usr/bin/env python3
"""
WordPress Exporter - Windows GUI Launcher
Double-click this file to run wp-exporter without terminal
"""

import subprocess
import sys
import os
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import threading

class WpExporterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WordPress Exporter - GUI Mode")
        self.root.geometry("600x500")
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="WordPress Exporter", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Mode selection
        mode_frame = tk.Frame(main_frame)
        mode_frame.pack(pady=10)
        
        self.mode_var = tk.StringVar(value="live")
        tk.Radiobutton(mode_frame, text="Live WordPress Site", variable=self.mode_var, value="live").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="XML File", variable=self.mode_var, value="xml").pack(side=tk.LEFT, padx=10)
        
        # Input fields
        input_frame = tk.Frame(main_frame)
        input_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(input_frame, text="Site URL or XML File:").pack(anchor=tk.W)
        self.url_entry = tk.Entry(input_frame, width=50)
        self.url_entry.pack(fill=tk.X, pady=5)
        
        tk.Label(input_frame, text="Credentials (user:password, leave empty if public):").pack(anchor=tk.W)
        self.auth_entry = tk.Entry(input_frame, width=50)
        self.auth_entry.pack(fill=tk.X, pady=5)
        
        # Options
        options_frame = tk.Frame(main_frame)
        options_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(options_frame, text="Options:").pack(anchor=tk.W)
        
        self.list_categories_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="List Categories", variable=self.list_categories_var).pack(anchor=tk.W)
        
        self.clean_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Clean Plugin Shortcodes", variable=self.clean_var).pack(anchor=tk.W)
        
        self.stats_var = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="Show Statistics", variable=self.stats_var).pack(anchor=tk.W)
        
        # Output format
        format_frame = tk.Frame(main_frame)
        format_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(format_frame, text="Output Format:").pack(anchor=tk.W)
        self.format_var = tk.StringVar(value="html")
        tk.Radiobutton(format_frame, text="HTML", variable=self.format_var, value="html").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(format_frame, text="Markdown", variable=self.format_var, value="markdown").pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="List Categories", command=self.list_categories, bg="lightblue").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Extract Content", command=self.extract_content, bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Output area
        tk.Label(main_frame, text="Output:").pack(anchor=tk.W, pady=(10, 0))
        self.output_text = scrolledtext.ScrolledText(main_frame, height=10, width=70)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def log_output(self, message):
        """Add message to output area"""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.root.update()
        
    def clear_fields(self):
        """Clear all input fields"""
        self.url_entry.delete(0, tk.END)
        self.auth_entry.delete(0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
        
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
            
            if not xml_file:
                messagebox.showerror("Error", "Please enter an XML file path")
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
        
    def run_command(self, command):
        """Run command in separate thread"""
        try:
            self.status_var.set("Running...")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
            
            self.log_output(f"Command: {command}")
            self.log_output("=" * 50)
            
            if result.stdout:
                self.log_output("OUTPUT:")
                self.log_output(result.stdout)
                
            if result.stderr:
                self.log_output("ERRORS:")
                self.log_output(result.stderr)
                
            self.status_var.set("Done")
            
        except Exception as e:
            self.log_output(f"Error: {e}")
            self.status_var.set("Error")
            
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
        messagebox.showerror("Error", f"wp-exporter.py not found in {os.path.dirname(__file__)}")
        sys.exit(1)
        
    app = WpExporterGUI()
    app.run()
