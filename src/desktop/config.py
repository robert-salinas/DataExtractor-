"""
RS | Design System - Desktop Config
Centralizes colors, fonts, and styles for the desktop application.
"""

class AppConfig:
    # Brand Core - RS Orange
    RS_ORANGE = "#FF7A3D"
    RS_ORANGE_LIGHT = "#FFA566"
    RS_ORANGE_DARK = "#E86A2A"
    RS_ORANGE_GLOW = "#FF8C52"

    # Dark Palette - Depth Layers (ADN Visual RS)
    BG_MAIN = "#1A1F2E"        # Azul Noche Profundo (Fondo Principal)
    BG_CARD = "#242A3D"        # Tarjetas ligeramente más claras
    BG_SIDEBAR = "#141824"     # Sidebar más oscuro
    BG_INPUT = "#0F1419"       # Deep Inputs

    # Text Colors
    TEXT_WHITE = "#FFFFFF"
    TEXT_LIGHT = "#F3F4F6"
    TEXT_MUTED = "#9CA3AF"

    # Semantic Colors
    SUCCESS = "#10B981"
    ERROR = "#EF4444"
    WARNING = "#F59E0B"

    # Layout Properties
    RADIUS = 15                # Corner radius=15 solicitado
    TRANSITION_SPEED = 0.25
    
    # Fonts
    FONT_FAMILY = "Inter"
    FONT_MAIN = ("Inter", 12)          # Tamaño 12 para textos
    FONT_BOLD = ("Inter", 12, "bold")
    FONT_KPI = ("Inter", 28, "bold")   # KPIs destacados
    FONT_HEADER = ("Inter", 16, "bold") # Tamaño 16 negrita para títulos
    FONT_TITLE_CARD = ("Inter", 16, "bold")

    # Icons (Simulados con texto por ahora, o placeholders)
    ICON_REGISTROS = "📊"
    ICON_PIPELINE = "⚡"
    ICON_STATUS = "🛡️"
    ICON_INPUT = "📂"
    ICON_TABLE = "🔍"
    ICON_PLAY = "⭕"
    ICON_STOP = "🛑"
    ICON_COPY = "📋"
    ICON_EXPORT = "📊"
    ICON_REPORT = "📄"

    # App Metadata
    APP_NAME = "RS DataExtractor-"
    VERSION = "v0.1.0"
    AUTHOR = "Robert Salinas"
    COPYRIGHT = "© 2026 RS Digital"
