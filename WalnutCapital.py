import tkinter as tk
import pulp
from tkinter import ttk, messagebox, Canvas
from pulp import LpProblem, LpVariable, LpMaximize, lpSum
from tkinter import PhotoImage
from PIL import Image, ImageTk
import webbrowser
from pulp import COIN_CMD
import os
import sys
from pulp import COIN_CMD

# Determine if we're running in a bundle or a normal Python environment
is_bundle = getattr(sys, 'frozen', False)

# Set the path to the CBC binary accordingly
if is_bundle:
    cbc_path = os.path.join(sys._MEIPASS, 'cbc')
else:
    cbc_path = '/opt/homebrew/bin/cbc'  # Default path for development

# Use the CBC binary path for PuLP
my_solver = COIN_CMD(path=cbc_path)


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = Canvas(self, bg='#2e2e2e')  # Set the Canvas background to dark gray
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='TFrame')  # Apply the TFrame style from CustomStyle class

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class CustomStyle(ttk.Style):
    def __init__(self, theme='clam'):
        super().__init__()
        self.theme_use(theme)
        self.configure('TFrame', background='#2e2e2e')
        self.configure('TLabel', background='#2e2e2e', foreground='white')
        self.configure('TButton', background='#2e2e2e', foreground='white')
        self.configure('TEntry', fieldbackground='#5c5c5c', foreground='white', bordercolor='#2e2e2e')
        self.map('TEntry', fieldbackground=[('disabled', '#2e2e2e'), ('!disabled', '#5c5c5c')])
        self.map('TButton', background=[('active', '#5c5c5c'), ('!disabled', '#2e2e2e')])



class OptimizationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Housing Development Optimization")
        self.custom_style = CustomStyle()
        self.root.configure(background='#2e2e2e')
        self.canvas = Canvas(self.root, width=600, height=800, bg='#2e2e2e')  # Set the Canvas background to dark gray
        self.canvas.pack()


        # Load and resize the logo image
        try:
            original_image = Image.open("Walnut/WalnutLogo.png")  # Update this path
            resized_image = original_image.resize((300, 300), Image.Resampling.LANCZOS)  # Resize as needed
            self.logo_image = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(300, 150, image=self.logo_image)  # Adjust the position as needed
        except IOError as e:
            print(f"Error loading the logo image: {e}")
        self.setup_ui()

    def setup_ui(self):
        
        # Title label
        title_text = "Affordable Housing Optimization Tool"
        self.canvas.create_text(300, 300, text=title_text, font=("Arial", 20), fill="white")  # Position the title
       
        # Create a container frame for the buttons
        button_frame = tk.Frame(self.root, bg='#2e2e2e')  # Adjust the background color to match your canvas
        button_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # Center the frame in the middle of the root window

        # Create and place the Start button
        start_button = ttk.Button(button_frame, text="Start", command=self.initialize_main_interface, width=10)
        start_button.grid(row=0, column=0, padx=5, pady=20)

        # Create and place the Manual button
        manual_button = ttk.Button(button_frame, text="?", command=self.open_manual, width=10)
        manual_button.grid(row=0, column=1, padx=5)

        # Create and place the Report button
        report_button = ttk.Button(button_frame, text="Report", command=self.show_report_message, width=10)
        report_button.grid(row=0, column=2, padx=5)

        # Add a disclaimer at the bottom of the canvas
        disclaimer_text = (
            "Disclaimer: The creators of this tool assume no liability for misuse. "
            "All outputs should be interpreted with caution and, where necessary, consulted with an expert."
        )
        
        # Choose a font size that is subtle yet readable
        disclaimer_font = ("Arial", 8, "italic")
        
        # Position the disclaimer text at the bottom of the canvas
        self.canvas.create_text(
            300,  # x position - half of the canvas width
            780,  # y position - near the bottom of the canvas
            text=disclaimer_text,
            font=disclaimer_font,
            fill="gray",  # A color that is subtle
            width=580,  # Width of the text box; ensure this is within the canvas size
            anchor="s"  # Anchor the text to the south (bottom)
        )

    def initialize_main_interface(self):
        # Hide the canvas and show the main interface
        self.canvas.pack_forget()
        self.main_frame = ScrollableFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Net Residential Area
        ttk.Label(self.main_frame.scrollable_frame, text="Net Residential Area:").grid(column=0, row=0)
        self.net_residential_area_var = tk.DoubleVar()
        ttk.Entry(self.main_frame.scrollable_frame, textvariable=self.net_residential_area_var).grid(column=1, row=0)
        
        # Number of Unit Types
        ttk.Label(self.main_frame.scrollable_frame, text="Number of Unit Types:").grid(column=0, row=1)
        self.num_unit_types_var = tk.IntVar()
        ttk.Entry(self.main_frame.scrollable_frame, textvariable=self.num_unit_types_var).grid(column=1, row=1)

        self.submit_button = ttk.Button(self.main_frame.scrollable_frame, text="Submit", command=self.get_unit_names)
        self.submit_button.grid(column=0, row=2, columnspan=2)

        self.current_row = 3
        self.unit_details = []
        self.ami_vars = {}
        self.min_units_vars = {}
        self.max_units_vars = {}
        self.derived_inputs = []
        self.min_annual_salaries = []

    def open_manual(self):
        # This function opens a web link to the manual in the user's default browser
        manual_url = "https://docs.google.com/document/d/1ib_omownMryn7IKk0UvBdDzMI-sflr131sHJf4WEt7g/edit?usp=sharing"  
        try:
            webbrowser.open_new(manual_url)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open the manual: {e}")
    
    def show_report_message(self):
        # This is the message you want to display when the Report button is clicked
        messagebox.showinfo("Report Issue", "If the program runs with errors or fails to produce any results, please contact raymondpeterdavid@gmail.com")    
    
    def get_unit_names(self):
        num_unit_types = self.num_unit_types_var.get()
        self.unit_details = []  # Reset to ensure clean start
        for i in range(num_unit_types):
            name_var = tk.StringVar()
            ttk.Label(self.main_frame.scrollable_frame, text=f"Name for Unit Type {i+1}:").grid(column=0, row=3 + i)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=name_var).grid(column=1, row=3 + i)
            self.unit_details.append({'name_var': name_var})

        self.submit_button.configure(text="Next", command=self.get_unit_details)

    def get_unit_details(self):
        self.current_row += len(self.unit_details)
        for detail in self.unit_details:
            unit_name = detail['name_var'].get().strip().replace(' ', '_')

            sqft_var = tk.DoubleVar()
            ttk.Label(self.main_frame.scrollable_frame, text=f"Square Footage for {unit_name}:").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=sqft_var).grid(column=1, row=self.current_row)
            detail['sqft_var'] = sqft_var
            self.current_row += 1

            rent_var = tk.DoubleVar()
            ttk.Label(self.main_frame.scrollable_frame, text=f"Monthly Rent for {unit_name}:").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=rent_var).grid(column=1, row=self.current_row)
            detail['rent_var'] = rent_var
            self.current_row += 1

            people_var = tk.IntVar()
            ttk.Label(self.main_frame.scrollable_frame, text=f"Min People for {unit_name}:").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=people_var).grid(column=1, row=self.current_row)
            detail['people_var'] = people_var
            self.current_row += 1
        
        self.submit_button.configure(text="Next", command=self.get_ami_and_min_unit_req)

    def get_ami_and_min_unit_req(self):
        max_people = max(detail['people_var'].get() for detail in self.unit_details)

        ttk.Label(self.main_frame.scrollable_frame, text="100% AMI Income by Household Size:").grid(column=0, row=self.current_row)
        self.current_row += 1
        for i in range(1, max_people + 1):
            ami_var = tk.DoubleVar()
            ttk.Label(self.main_frame.scrollable_frame, text=f"{i} Household:").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=ami_var).grid(column=1, row=self.current_row)
            self.ami_vars[i] = ami_var
            self.current_row += 1

        ttk.Label(self.main_frame.scrollable_frame, text="AMI (%) Limit for Affordable Housing:").grid(column=0, row=self.current_row)
        self.ami_percentage_var = tk.DoubleVar()
        ttk.Entry(self.main_frame.scrollable_frame, textvariable=self.ami_percentage_var).grid(column=1, row=self.current_row)
        self.current_row += 1

        
        #Minimum Affordable Housing Percentage
        ttk.Label(self.main_frame.scrollable_frame, text="Set-aside Requirement (%):").grid(column=0, row=self.current_row)
        self.min_aff_housing_percentage_var = tk.DoubleVar()
        ttk.Entry(self.main_frame.scrollable_frame, textvariable=self.min_aff_housing_percentage_var).grid(column=1, row=self.current_row)
        self.current_row += 1
        
        ttk.Label(self.main_frame.scrollable_frame, text="Min/Max Units Requirement: (in %)").grid(column=0, row=self.current_row)
        self.current_row += 1
        
        for detail in self.unit_details:
            unit_name = detail['name_var'].get().strip().replace(' ', '_')
            min_units_var = tk.IntVar()
            max_units_var = tk.IntVar()
            
            ttk.Label(self.main_frame.scrollable_frame, text=f"Min Units for {unit_name} (Market + Aff.):").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=min_units_var).grid(column=1, row=self.current_row)
            self.min_units_vars[unit_name] = min_units_var
            self.current_row += 1

            ttk.Label(self.main_frame.scrollable_frame, text=f"Max Units for {unit_name} (Market + Aff.):").grid(column=0, row=self.current_row)
            ttk.Entry(self.main_frame.scrollable_frame, textvariable=max_units_var).grid(column=1, row=self.current_row)
            self.max_units_vars[unit_name] = max_units_var
            self.current_row += 1

        self.submit_button.configure(text="Calculate Derived Inputs", command=self.calculate_derived_inputs)

    def calculate_derived_inputs(self):
        ami_values = {size: var.get() * self.ami_percentage_var.get() * 0.01 for size, var in self.ami_vars.items()}
        self.calculate_derived_inputs_logic(ami_values)
        messagebox.showinfo("Derived Inputs Calculated", "Derived inputs have been calculated. Ready to run optimization.")
        self.submit_button.configure(text="Run Optimization", command=self.setup_optimization_problem)

    def calculate_derived_inputs_logic(self, ami_values):
        rent_reduction = 100
        rent_percentage = 0.30
        
        for detail in self.unit_details:
            unit_name = detail['name_var'].get().strip().replace(' ', '_')
            sq_ft = detail['sqft_var'].get()
            rent = detail['rent_var'].get()
            people = detail['people_var'].get()

            ami_income = ami_values.get(people, 0)
            monthly_ami_rent = max(0, (ami_income * rent_percentage / 12) - rent_reduction)

            sq_ft_rule = sq_ft / 12
            rule_50 = rent * 0.5
            max_cost = max(sq_ft_rule, rule_50)

            self.derived_inputs.append({
                'Unit Type': f"{unit_name}",
                'Sq. Ft.': sq_ft,
                'Avg. Rent': rent,
                'Sq. Ft. Rule': sq_ft_rule,
                '50% Rule': rule_50,
                'Max': max_cost,
                'MinAnnualSalary': rent * 12 * 3
            })

            # Repeat for affordable housing with adjusted rent
            self.derived_inputs.append({
                'Unit Type': f"Aff_{unit_name}",
                'Sq. Ft.': sq_ft,
                'Avg. Rent': monthly_ami_rent,
                'Sq. Ft. Rule': sq_ft_rule,
                '50% Rule': rule_50,  # Use same rule_50 as market for consistency
                'Max': max_cost,  # Use same max_cost as market for consistency
                'MinAnnualSalary': rent * 12 * 3
            })

    def setup_optimization_problem(self):
        aff_housing_percent = self.min_aff_housing_percentage_var.get() * 0.01
        self.problem = LpProblem("Optimal_Unit_Mix", LpMaximize)

        # Create decision variables
        unit_vars = {di['Unit Type']: LpVariable(f"units_{di['Unit Type']}", lowBound=0, cat='Integer') for di in self.derived_inputs}
        total_units_var = LpVariable("TotalUnits", lowBound=0, cat='Integer')

        # Define revenue and costs for the objective function
        revenue = lpSum([di['Avg. Rent'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) * 12
        worst_case_costs = lpSum([di['Max'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) * 12
        self.problem += revenue - worst_case_costs, "Total_Annual_Profit_Worst_Case"

        # Define constraints
        self.problem += total_units_var == lpSum([unit_vars[di['Unit Type']] for di in self.derived_inputs]), "TotalUnitsConstraint"
        self.problem += lpSum([di['Sq. Ft.'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) <= self.net_residential_area_var.get(), "Land_Size_Constraint" 
        self.problem += lpSum([di['Sq. Ft.'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) >= 0.9 * self.net_residential_area_var.get(), "Land_Utilization_Constraint"
        for detail in self.unit_details:   
            unit_name = detail['name_var'].get().strip().replace(' ', '_')
            self.problem += (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]) >= 0.01 * self.min_units_vars[unit_name].get() * total_units_var, f"Min_Units_Constraint_{unit_name}"
            self.problem += (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]) <= 0.01 * self.max_units_vars[unit_name].get() * total_units_var, f"Max_Units_Constraint_{unit_name}"
            self.problem += unit_vars[f"Aff_{unit_name}"] >= aff_housing_percent * (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]), f"Affordable_{unit_name}"
            
        # Solve the LP problem
        self.problem.solve(my_solver)

        # Calculate land utilization rate and total units after obtaining the optimal solution
        total_land_used = sum(di['Sq. Ft.'] * unit_vars[di['Unit Type']].varValue for di in self.derived_inputs)
        land_utilization_rate = (total_land_used / self.net_residential_area_var.get()) * 100
        total_units = sum(unit_vars[di['Unit Type']].varValue for di in self.derived_inputs)

        # Calculate best case profit
        best_case_costs = sum(di['Sq. Ft. Rule'] * unit_vars[di['Unit Type']].varValue * 12 for di in self.derived_inputs)
        annual_profit_best_case = (revenue.value() - best_case_costs) * 0.95524
        annual_profit_worst_case = (revenue.value() - worst_case_costs.value()) * 0.95524
        self.ilp_annual_profit_best_case = annual_profit_best_case


        # Pass calculated metrics to display function
        self.display_results_window([(di['Unit Type'], unit_vars[di['Unit Type']].varValue, di['MinAnnualSalary']) for di in self.derived_inputs], annual_profit_worst_case, annual_profit_best_case, land_utilization_rate, total_units)



    def display_results_window(self, results_data, annual_profit_worst_case, annual_profit_best_case, land_utilization_rate, total_units):
        results_window = tk.Toplevel(self.root)
        results_window.title("Optimization Results")
        results_window.geometry("600x600")

        tree = ttk.Treeview(results_window, columns=("Unit Type", "Quantity", "MinAnnualSalary"), show="headings")
        tree.heading("Unit Type", text="Unit Type")
        tree.heading("Quantity", text="Quantity")
        tree.heading("MinAnnualSalary", text = "Minimum Annual Salary")
        for unit_type, quantity, min_annual_salary in results_data:
            tree.insert('', 'end', values=(unit_type, round(quantity, 2),round(min_annual_salary,0)))
        tree.pack(expand=True, fill='both')

        tk.Label(results_window, text=f"Minimum Expected Returns: ${annual_profit_worst_case:,.2f}", font=("Arial", 14)).pack(pady=5)
        tk.Label(results_window, text=f"Maximum Expected Returns: ${annual_profit_best_case:,.2f}", font=("Arial", 14)).pack(pady=5)
        tk.Label(results_window, text=f"Land Utilization Rate: {land_utilization_rate:.2f}%", font=("Arial", 14)).pack(pady=5)
        tk.Label(results_window, text=f"Total Number of Units: {total_units}", font=("Arial", 14)).pack(pady=5)

        self.sa_button = ttk.Button(results_window, text="Show Sensitivity Analysis", command=self.display_sensitivity_analysis)
        self.sa_button.pack(pady=10)
        self.sa_button.configure(text="Show Sensitivity Analysis", command=self.display_sensitivity_analysis)
    
    
    def display_sensitivity_analysis(self):
        # Setup a new LP problem for sensitivity analysis based on the original inputs but without integer constraints
        sa_problem = LpProblem("Sensitivity_Analysis", LpMaximize)
    
        # Use the same structure as in setup_optimization_problem but with continuous variables
        unit_vars = {di['Unit Type']: LpVariable(f"sa_units_{di['Unit Type']}", lowBound=0, cat='Continuous') for di in self.derived_inputs}
        total_units_var = LpVariable("sa_TotalUnits", lowBound=0, cat='Continuous')

        # Reuse the objective function and constraints with the new variables
        revenue = lpSum([di['Avg. Rent'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) * 12
        worst_case_costs = lpSum([di['Max'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) * 12
        sa_problem += revenue - worst_case_costs, "Total_Annual_Profit_Worst_Case"

        # Define constraints similar to the integer problem, but for the LP version
        sa_problem += total_units_var == lpSum([unit_vars[di['Unit Type']] for di in self.derived_inputs]), "TotalUnitsConstraint"
        sa_problem += lpSum([di['Sq. Ft.'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) <= self.net_residential_area_var.get(), "Land_Size_Constraint" 
        sa_problem += lpSum([di['Sq. Ft.'] * unit_vars[di['Unit Type']] for di in self.derived_inputs]) >= 0.9 * self.net_residential_area_var.get(), "Land_Utilization_Constraint"
        for detail in self.unit_details:   
            unit_name = detail['name_var'].get().strip().replace(' ', '_')
            sa_problem += (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]) >= 0.01 * self.min_units_vars[unit_name].get() * total_units_var, f"Min_Units_Constraint_{unit_name}"
            sa_problem += (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]) <= 0.01 * self.max_units_vars[unit_name].get() * total_units_var, f"Max_Units_Constraint_{unit_name}"
            aff_housing_percent = self.min_aff_housing_percentage_var.get() * 0.01
            sa_problem += unit_vars[f"Aff_{unit_name}"] >= aff_housing_percent * (unit_vars[unit_name] + unit_vars[f"Aff_{unit_name}"]), f"Affordable_{unit_name}"

        # Solve the relaxed LP problem
        sa_problem.solve(my_solver)

        # Calculate metrics for the LP version
        total_land_used = sum(di['Sq. Ft.'] * unit_vars[di['Unit Type']].varValue for di in self.derived_inputs)
        land_utilization_rate = (total_land_used / self.net_residential_area_var.get()) * 100
        total_units = sum(unit_vars[di['Unit Type']].varValue for di in self.derived_inputs)

        best_case_costs = sum(di['Sq. Ft. Rule'] * unit_vars[di['Unit Type']].varValue * 12 for di in self.derived_inputs)
        annual_profit_best_case = (revenue.value() - best_case_costs) * 0.95524
        annual_profit_worst_case = (revenue.value() - worst_case_costs.value()) * 0.95524

        # Calculate Precision (%)
        precision = (self.ilp_annual_profit_best_case / annual_profit_best_case) * 100 if annual_profit_best_case else 0

        sa_window = tk.Toplevel(self.root)
        sa_window.title("Sensitivity Analysis & LP Metrics")
        sa_window.geometry("650x800")  # Adjusted size to fit additional information

        # Text for LP Metrics
        metrics_text = f"LP Metrics:\n" \
                   f"Minimum Expected Returns: ${annual_profit_worst_case:,.2f}\n" \
                   f"Maximum Expected Returns: ${annual_profit_best_case:,.2f}\n" \
                   f"Land Utilization Rate: {land_utilization_rate:.2f}%\n" \
                   f"Total Number of Units: {total_units}\n" \
                   f"Precision (%): {precision:.2f}%"

        # Display LP Metrics with aligned text
        metrics_label = tk.Label(sa_window, text=metrics_text, font=("Arial", 12), justify="left", anchor="w")
        metrics_label.pack(fill='x', padx=10, pady=10)

        # Text for LP Variable Quantities
        lp_vars_text = "\n\nLP Variable Quantities:\n"
        for di in self.derived_inputs:
            unit_type = di['Unit Type']
            quantity = unit_vars[unit_type].varValue  # Access the LP solution variable value
            lp_vars_text += f"{unit_type}: {quantity:.2f}\n"

        # Display LP Variable Quantities with aligned text
        lp_vars_label = tk.Label(sa_window, text=lp_vars_text, font=("Arial", 12), justify="left", anchor="w")
        lp_vars_label.pack(fill='x', padx=10, pady=10)


        tree = ttk.Treeview(sa_window, columns=("Variable", "Shadow Price/Reduced Cost"), show="headings")
        tree.heading("Variable", text="Variable")
        tree.heading("Shadow Price/Reduced Cost", text="Shadow Price/Reduced Cost")

        # Shadow Prices for constraints and Reduced Costs for variables
        for name, constraint in sa_problem.constraints.items():
            tree.insert('', 'end', values=(name, f"Shadow Price: {constraint.pi}"))
        for variable in sa_problem.variables():
            tree.insert('', 'end', values=(variable.name, f"Reduced Cost: {variable.dj}"))

        tree.pack(expand=True, fill='both')





def main():
    root = tk.Tk()
    root.geometry("600x800")
    app = OptimizationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()