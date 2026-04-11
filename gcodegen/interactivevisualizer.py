import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import pickle
import os
from datetime import datetime
from main import ResultsManager, SurfaceModel, ToolpathPoint
import csv


class InteractiveVisualizer:
    """Interactive visualization with export options"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Raster Toolpath Visualizer")
        self.root.geometry("1400x900")
        
        self.surface = None
        self.toolpath = None
        self.results_data = None
        
        # Configure matplotlib to use TkAgg backend
        matplotlib.use('TkAgg')
        
        self.setup_ui()
        self.setup_plot()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main frames
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        plot_frame = ttk.Frame(self.root, padding="10")
        plot_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=1)
        
        # ===== CONTROL PANEL =====
        ttk.Label(control_frame, text="TOOLPATH VISUALIZER", 
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Load buttons
        ttk.Label(control_frame, text="Load Data:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        ttk.Button(control_frame, text="Load Results (JSON)", 
                  command=self.load_results).grid(row=2, column=0, sticky=tk.EW, pady=5)
        
        ttk.Button(control_frame, text="Load Surface (Pickle)", 
                  command=self.load_surface).grid(row=3, column=0, sticky=tk.EW, pady=5)
        
        # Visualization controls
        ttk.Label(control_frame, text="Display Options:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(20, 5))
        
        self.show_surface_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Surface", 
                       variable=self.show_surface_var,
                       command=self.update_plot).grid(row=5, column=0, sticky=tk.W)
        
        self.show_toolpath_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Toolpath", 
                       variable=self.show_toolpath_var,
                       command=self.update_plot).grid(row=6, column=0, sticky=tk.W)
        
        self.show_normals_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Show Normals", 
                       variable=self.show_normals_var,
                       command=self.update_plot).grid(row=7, column=0, sticky=tk.W)
        
        self.show_rapid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Rapid Moves", 
                       variable=self.show_rapid_var,
                       command=self.update_plot).grid(row=8, column=0, sticky=tk.W)
        
        self.surface_alpha_var = tk.DoubleVar(value=0.8)
        ttk.Label(control_frame, text="Surface Opacity:").grid(row=9, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Scale(control_frame, from_=0.1, to=1.0, variable=self.surface_alpha_var,
                 orient=tk.HORIZONTAL, command=self.update_plot).grid(row=10, column=0, sticky=tk.EW)
        
        # View controls
        ttk.Label(control_frame, text="View:", font=("Arial", 10, "bold")).grid(row=11, column=0, sticky=tk.W, pady=(20, 5))
        
        ttk.Button(control_frame, text="3D View", 
                  command=lambda: self.set_view('3d')).grid(row=12, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Top View", 
                  command=lambda: self.set_view('top')).grid(row=13, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Side View", 
                  command=lambda: self.set_view('side')).grid(row=14, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Reset View", 
                  command=self.reset_view).grid(row=15, column=0, sticky=tk.EW, pady=2)
        
        # Export buttons
        ttk.Label(control_frame, text="Export:", font=("Arial", 10, "bold")).grid(row=16, column=0, sticky=tk.W, pady=(20, 5))
        
        ttk.Button(control_frame, text="Export G-code", 
                  command=self.export_gcode).grid(row=17, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Export CSV", 
                  command=self.export_csv).grid(row=18, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Export PNG", 
                  command=self.export_png).grid(row=19, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(control_frame, text="Export PDF", 
                  command=self.export_pdf).grid(row=20, column=0, sticky=tk.EW, pady=2)
        
        # Info display
        ttk.Label(control_frame, text="Info:", font=("Arial", 10, "bold")).grid(row=21, column=0, sticky=tk.W, pady=(20, 5))
        
        self.info_text = tk.Text(control_frame, height=8, width=30, font=("Courier", 9))
        self.info_text.grid(row=22, column=0, sticky=(tk.W, tk.E), pady=5)

        # Live capture section
        ttk.Separator(control_frame, orient='horizontal').grid(row=23, column=0, sticky=tk.EW, pady=8)
        ttk.Label(control_frame, text="Live Capture:", font=("Arial", 10, "bold")).grid(row=24, column=0, sticky=tk.W)
        ttk.Button(control_frame, text="Capture from D405",
                  command=self.capture_from_d405).grid(row=25, column=0, sticky=tk.EW, pady=5)
        self.capture_status_var = tk.StringVar(value="")
        ttk.Label(control_frame, textvariable=self.capture_status_var,
                 foreground="gray").grid(row=26, column=0, sticky=tk.W)

        # Quit button
        ttk.Button(control_frame, text="Quit",
                  command=self.root.quit).grid(row=27, column=0, sticky=tk.EW, pady=(20, 0))
        
        # ===== PLOT AREA =====
        # Create matplotlib figure
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def setup_plot(self):
        """Initialize the plot"""
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_zlabel('Z (mm)')
        self.ax.set_title('Load a dataset to begin visualization', fontsize=14)
        self.ax.grid(True, alpha=0.3)
        
    def load_results(self):
        """Load results from JSON file"""
        filename = filedialog.askopenfilename(
            title="Select results file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.results_data = ResultsManager.load_results(filename)
                
                # Reconstruct surface
                surface_points = np.array(self.results_data['surface_sample'])
                surface_name = self.results_data['metadata']['surface_name']
                # Use mesh-based mode for hand models
                use_mesh_direct = "hand" in surface_name.lower() or "Hand" in surface_name
                self.surface = SurfaceModel(surface_points, surface_name, 
                                          use_mesh_direct=use_mesh_direct)
                
                # Reconstruct toolpath
                self.toolpath = []
                for pt_data in self.results_data['toolpath']:
                    point = ToolpathPoint(
                        position=np.array(pt_data['position']),
                        normal=np.array(pt_data['normal']),
                        feed_rate=pt_data['feed_rate'],
                        is_rapid=pt_data['is_rapid']
                    )
                    self.toolpath.append(point)
                
                self.update_info()
                self.update_plot()
                messagebox.showinfo("Success", f"Loaded: {self.results_data['metadata']['surface_name']}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def load_surface(self):
        """Load surface model from pickle file"""
        filename = filedialog.askopenfilename(
            title="Select surface file",
            filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.surface = SurfaceModel.load(filename)
                self.toolpath = None
                self.results_data = None
                
                self.update_info()
                self.update_plot()
                messagebox.showinfo("Success", f"Loaded surface: {self.surface.surface_name}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def update_info(self):
        """Update information display"""
        info = ""
        
        if self.surface:
            info += f"Surface: {self.surface.surface_name}\n"
            info += f"Points: {len(self.surface.points)}\n"
            bounds = self.surface.points
            info += f"X: [{bounds[:,0].min():.1f}, {bounds[:,0].max():.1f}]\n"
            info += f"Y: [{bounds[:,1].min():.1f}, {bounds[:,1].max():.1f}]\n"
            info += f"Z: [{bounds[:,2].min():.1f}, {bounds[:,2].max():.1f}]\n"
        
        if self.toolpath:
            info += f"\nToolpath Points: {len(self.toolpath)}\n"
            treatment = [pt for pt in self.toolpath if not pt.is_rapid]
            rapid = [pt for pt in self.toolpath if pt.is_rapid]
            info += f"Treatment: {len(treatment)}\n"
            info += f"Rapid: {len(rapid)}\n"
            
            if self.results_data:
                length = self.results_data['metadata']['treatment_length_mm']
                info += f"Length: {length:.1f} mm\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def update_plot(self, *args):
        """Update the plot with current settings"""
        self.ax.clear()
        
        if self.surface and self.show_surface_var.get():
            # Plot surface points
            points = self.surface.points
            scatter = self.ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                                    c=points[:, 1], cmap='terrain',
                                    s=16, alpha=float(self.surface_alpha_var.get()),
                                    edgecolors='k', linewidths=0.2,
                                    label='Surface')
        
        if self.toolpath and self.show_toolpath_var.get():
            positions = np.array([pt.position for pt in self.toolpath])
            is_rapid = np.array([pt.is_rapid for pt in self.toolpath])
            
            # Plot treatment path
            if any(~is_rapid):
                treatment_pos = positions[~is_rapid]
                self.ax.plot(treatment_pos[:, 0], treatment_pos[:, 1], treatment_pos[:, 2],
                           color='#ffd200', linewidth=2.5, alpha=0.9, label='Treatment Path')
            
            # Plot rapid moves
            if self.show_rapid_var.get() and any(is_rapid):
                rapid_pos = positions[is_rapid]
                self.ax.plot(rapid_pos[:, 0], rapid_pos[:, 1], rapid_pos[:, 2],
                           'r--', linewidth=1, alpha=0.5, label='Rapid Moves')
            
            # Plot normals
            if self.show_normals_var.get():
                sample = max(len(self.toolpath) // 20, 1)
                for i in range(0, len(self.toolpath), sample):
                    pt = self.toolpath[i]
                    if not pt.is_rapid:
                        self.ax.quiver(pt.position[0], pt.position[1], pt.position[2],
                                     pt.normal[0]*4, pt.normal[1]*4, pt.normal[2]*4,
                                     color='red', alpha=0.6, arrow_length_ratio=0.15)
        
        self.ax.set_xlabel('X (mm)')
        self.ax.set_ylabel('Y (mm)')
        self.ax.set_zlabel('Z (mm)')
        
        title = f'3D View'
        if self.surface:
            title = f'{self.surface.surface_name} - ' + title
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        
        if self.surface or self.toolpath:
            self.ax.legend()
        
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def set_view(self, view_type):
        """Set specific view angles"""
        if view_type == 'top':
            self.ax.view_init(elev=90, azim=-90)
        elif view_type == 'side':
            self.ax.view_init(elev=0, azim=-90)
        elif view_type == '3d':
            self.ax.view_init(elev=30, azim=45)
        
        self.canvas.draw()
    
    def reset_view(self):
        """Reset to default 3D view"""
        self.ax.view_init(elev=30, azim=45)
        self.canvas.draw()
    
    def export_gcode(self):
        """Export toolpath to G-code"""
        if self.toolpath:
            filename = filedialog.asksaveasfilename(
                defaultextension=".gcode",
                filetypes=[("G-code files", "*.gcode"), ("All files", "*.*")]
            )
            if filename:
                ResultsManager.export_gcode(self.toolpath, filename)
                messagebox.showinfo("Success", f"G-code exported to:\n{filename}")
        else:
            messagebox.showwarning("Warning", "No toolpath data to export")
    
    def export_csv(self):
        """Export toolpath to CSV"""
        if self.toolpath:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                ResultsManager.export_csv(self.toolpath, filename)
                messagebox.showinfo("Success", f"CSV exported to:\n{filename}")
        else:
            messagebox.showwarning("Warning", "No toolpath data to export")
    
    def export_png(self):
        """Export plot to PNG"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot saved to:\n{filename}")
    
    def export_pdf(self):
        """Export plot to PDF"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.fig.savefig(filename, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot saved to:\n{filename}")

    def capture_from_d405(self):
        """Capture a point cloud from the connected RealSense D405 and display it."""
        try:
            import pyrealsense2 as rs
        except ImportError:
            messagebox.showerror(
                "Missing Library",
                "pyrealsense2 not installed.\nRun: pip install pyrealsense2"
            )
            return

        self.capture_status_var.set("Connecting to D405...")
        self.root.update()

        pipeline = None
        try:
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30)
            pipeline.start(config)

            align = rs.align(rs.stream.infrared)
            pc = rs.pointcloud()
            spatial = rs.spatial_filter()
            temporal = rs.temporal_filter()
            hole = rs.hole_filling_filter(1)

            self.capture_status_var.set("Warming up (30 frames)...")
            self.root.update()
            for _ in range(30):
                pipeline.wait_for_frames()

            self.capture_status_var.set("Capturing...")
            self.root.update()
            frames = pipeline.wait_for_frames()
            aligned = align.process(frames)
            depth_frame = aligned.get_depth_frame()
            ir_frame = aligned.get_infrared_frame(1)

            if not depth_frame or not ir_frame:
                raise RuntimeError("Failed to capture valid frames from D405")

            depth_frame = spatial.process(depth_frame)
            depth_frame = temporal.process(depth_frame)
            depth_frame = hole.process(depth_frame)

            pc.map_to(ir_frame)
            points = pc.calculate(depth_frame)

            vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
            tex_coords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)

            # Filter: valid coords, D405 depth range (7-50 cm), center 60% ROI
            valid = (
                np.isfinite(vertices).all(axis=1) &
                (vertices[:, 2] >= 0.07) & (vertices[:, 2] <= 0.50) &
                (tex_coords[:, 0] >= 0.2) & (tex_coords[:, 0] <= 0.8) &
                (tex_coords[:, 1] >= 0.2) & (tex_coords[:, 1] <= 0.8)
            )
            pts = vertices[valid]

            if len(pts) == 0:
                raise RuntimeError(
                    "No valid points captured.\n"
                    "Ensure the target is 7-50 cm from the D405."
                )

            # Convert from meters to mm to match the toolpath coordinate system
            pts_mm = pts * 1000.0

            self.surface = SurfaceModel(pts_mm, "D405 Capture")
            self.toolpath = None
            self.results_data = None
            self.update_info()
            self.update_plot()
            self.capture_status_var.set(f"Captured {len(pts_mm):,} points")

        except Exception as e:
            messagebox.showerror("Capture Failed", str(e))
            self.capture_status_var.set("Capture failed")
        finally:
            if pipeline is not None:
                try:
                    pipeline.stop()
                except Exception:
                    pass


def main():
    """Main function to run the visualizer"""
    root = tk.Tk()
    app = InteractiveVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
